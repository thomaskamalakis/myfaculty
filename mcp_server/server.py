"""
MCP server for myfaculty.

A thin layer over the role-based REST API (/apiv2/hr/..., /apiv2/sec/...,
/apiv2/...). It keeps no secrets and implements no permissions: every MCP
client sends its own Django API token as `Authorization: Token <token>`, the
server forwards it unchanged, and Django decides what that user may see or
change (HR / secretariat scope / admin).
"""
import functools
import logging
import os
import re
from typing import Any, Literal

import httpx
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

API_URL = os.environ.get('MYFACULTY_API_URL', 'http://web:8000').rstrip('/')
# Django only accepts hosts listed in ALLOWED_HOSTS; 'web' (the compose service
# name) usually is not one of them, so requests carry this Host header instead.
API_HOST = os.environ.get('MYFACULTY_API_HOST', 'localhost')
TIMEOUT = float(os.environ.get('MYFACULTY_API_TIMEOUT', '30'))

log = logging.getLogger('myfaculty-mcp')

# MCP_MODE: OFF (answers nothing), READ_ONLY (no create/update/delete) or FULL.
# A missing or unknown value means OFF, the safe default.
MODES = ('OFF', 'READ_ONLY', 'FULL')


def _parse_mode(raw: str | None) -> str | None:
    value = (raw or '').strip().upper().replace('-', '_')
    if value == 'READONLY':
        value = 'READ_ONLY'
    return value if value in MODES else None


MODE = _parse_mode(os.environ.get('MCP_MODE'))
if MODE is None:
    log.warning("MCP_MODE is missing or not one of %s (got %r): running as OFF.", MODES, os.environ.get('MCP_MODE'))
    MODE = 'OFF'
log.warning('myfaculty MCP server mode: %s', MODE)

DISABLED_MESSAGE = ('Ο MCP server του myfaculty είναι απενεργοποιημένος (MCP_MODE=OFF). '
                    'The myfaculty MCP server is disabled (MCP_MODE=OFF).')
READ_ONLY_MESSAGE = ('Ο MCP server του myfaculty λειτουργεί μόνο για ανάγνωση (MCP_MODE=READ_ONLY): '
                     'δεν επιτρέπονται create, update, delete. '
                     'The myfaculty MCP server is read-only (MCP_MODE=READ_ONLY): create, update and delete are disabled.')


def _check_mode(kind: str) -> None:
    if MODE == 'OFF':
        raise ToolError(DISABLED_MESSAGE)
    if MODE == 'READ_ONLY' and kind == 'write':
        raise ToolError(READ_ONLY_MESSAGE)


def gated(kind: str):
    """Runs the MCP_MODE check before the tool does anything (kind: 'read' or 'write')."""
    def decorator(function):
        @functools.wraps(function)
        async def wrapper(*args, **kwargs):
            _check_mode(kind)
            return await function(*args, **kwargs)
        return wrapper
    return decorator


Role = Literal['hr', 'sec', 'admin']
RESOURCE_RE = re.compile(r'^[a-z0-9_]+/[a-z0-9_]+$')
RESERVED_PARAMS = {'page', 'page_size', 'format', 'search', 'expand'}

INSTRUCTIONS = """
Access to the myfaculty department management system.

Every tool takes a `role`: 'hr' (human resources: hrms contracts, decisions,
employees), 'sec' (secretariat: students, theses, PhD, leaves, projects -
limited to the secretariat's own programmes/departments) or 'admin' (all
models, superusers only). The API token you connect with decides which roles
work; others answer 403.

A `resource` is written app/model in lower case, e.g. 'hrms/application' or
'myprofile/student'. Call list_resources first, and describe_resource to see
the fields of a resource before create/update.

To find people or records by name or text use search(..., search="papadop"):
several words must all match; case is ignored but accents are not. Use
`expand=["employee"]` to get a readable `employee_display` next to the id
(every record also has a `display` string). employee_summary() gives an
overview of one employee (wage class, rank, contracts, decisions), and
decision_experience() the prior-service breakdown of one decision.

search() filters use Django lookups, e.g. {"employee": 12},
{"start_date__gte": "2020-01-01"}, {"organization__icontains": "univ"}.
Dates are YYYY-MM-DD. Relations are given as ids.

hrms.Application types: Fulltime, Workcontract, Teaching407fractioonal,
Teachinghourly, Teachingdays, OT (other), External. Status: P pending,
A approved, R rejected. Work type: Teaching, Research. For types OT and
External `day_percentage` is a fraction 0-1 (0.7 = 70%).
""".strip()

MODE_NOTE = {
    'OFF': DISABLED_MESSAGE + ' Every tool call is refused.',
    'READ_ONLY': 'Mode: READ_ONLY - search and read tools work; create, update and delete are disabled.',
    'FULL': 'Mode: FULL - reading and writing are enabled.',
}[MODE]
INSTRUCTIONS = MODE_NOTE + '\n\n' + INSTRUCTIONS

mcp = FastMCP(
    'myfaculty',
    instructions=INSTRUCTIONS,
    host=os.environ.get('MCP_HOST', '0.0.0.0'),
    port=int(os.environ.get('MCP_PORT', '8765')),
    # No session state is needed: each call carries its own token.
    stateless_http=True,
)


def _token(ctx: Context) -> str:
    request = ctx.request_context.request
    header = request.headers.get('authorization') if request is not None else None
    if not header:
        raise ToolError(
            "Missing API token. Configure the MCP client to send the header "
            "'Authorization: Token <your token>'.")
    return header


def _url(role: str, resource: str | None = None, pk: int | str | None = None, action: str | None = None) -> str:
    if role not in ('hr', 'sec', 'admin'):
        raise ToolError("role must be 'hr', 'sec' or 'admin'.")
    url = f'{API_URL}/apiv2/'
    if role != 'admin':
        url += f'{role}/'
    if resource is not None:
        if not RESOURCE_RE.match(resource):
            raise ToolError("resource must look like 'app/model', e.g. 'hrms/application'.")
        url += f'{resource}/'
    if pk is not None:
        if not str(pk).isdigit():
            raise ToolError('id must be a number.')
        url += f'{pk}/'
    if action is not None:
        url += f'{action}/'
    return url


async def _call(ctx: Context, method: str, url: str, *, params=None, body=None) -> Any:
    # Second line of defence behind @gated: a tool that forgot its decorator still cannot write
    _check_mode('read' if method in ('GET', 'OPTIONS') else 'write')
    headers = {'Authorization': _token(ctx), 'Accept': 'application/json', 'Host': API_HOST}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.request(method, url, params=params, json=body, headers=headers)
    except httpx.HTTPError as e:
        raise ToolError(f'Could not reach the myfaculty API: {e}')
    if response.status_code >= 400:
        raise ToolError(f'HTTP {response.status_code} from the API: {response.text[:2000]}')
    if response.status_code == 204 or not response.content:
        return {'ok': True}
    return response.json()


READ = ToolAnnotations(readOnlyHint=True, openWorldHint=False)
WRITE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False)
UPDATE = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=True, openWorldHint=False)
DELETE = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=True, openWorldHint=False)


@mcp.tool(annotations=READ)
@gated('read')
async def list_resources(role: Role, ctx: Context) -> Any:
    """List the resources (app/model) the role exposes, with their API URLs."""
    return await _call(ctx, 'GET', _url(role))


@mcp.tool(annotations=READ)
@gated('read')
async def describe_resource(role: Role, resource: str, ctx: Context) -> Any:
    """Describe a resource: the fields, types, required flags and choices accepted by create/update.
    The 'actions' part is missing when the role may not write to this resource."""
    return await _call(ctx, 'OPTIONS', _url(role, resource))


@mcp.tool(annotations=READ)
@gated('read')
async def search(role: Role, resource: str, ctx: Context,
                 search: str | None = None,
                 filters: dict[str, str | int | float | bool] | None = None,
                 expand: list[str] | None = None,
                 page: int = 1, page_size: int = 50) -> Any:
    """Search/list records. `search` is free text over names, emails, reference numbers and text fields
    (e.g. "papadop", or "giorgos papa" - all words must match). `filters` are exact Django lookups
    (field, field__icontains, field__gte, related__field). `expand` lists foreign-key fields (e.g. ["employee"])
    for which a readable `<field>_display` is added. Returns {count, next, previous, results}.
    For sec, only records in the secretariat's scope are returned."""
    params = {k: v for k, v in (filters or {}).items() if k not in RESERVED_PARAMS}
    params.update({'page': page, 'page_size': page_size})
    if search:
        params['search'] = search
    if expand:
        params['expand'] = ','.join(expand)
    return await _call(ctx, 'GET', _url(role, resource), params=params)


@mcp.tool(annotations=READ)
@gated('read')
async def get(role: Role, resource: str, id: int, ctx: Context) -> Any:
    """Fetch one record by id."""
    return await _call(ctx, 'GET', _url(role, resource, id))


HrRole = Literal['hr', 'admin']
# Recalculating a decision refreshes its stored total_days: idempotent, but not read-only
RECALC = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=True, openWorldHint=False)


@mcp.tool(annotations=READ)
@gated('read')
async def employee_summary(employee_id: int, ctx: Context, role: HrRole = 'hr') -> Any:
    """Overview of one employee (HR only): date hired, current wage class and rank with time in each,
    contracts by type and status, recognition decisions with their stored experience, and payroll decisions
    by type. Find the employee_id with search(resource='myprofile/employee', search='name')."""
    return await _call(ctx, 'GET', _url(role, 'myprofile/employee', employee_id, 'summary'))


@mcp.tool(annotations=RECALC)
@gated('read')
async def decision_experience(decision_id: int, ctx: Context, role: HrRole = 'hr') -> Any:
    """Prior-service calculation of one recognition decision (HR only): total days, years/months/days of this
    decision, of earlier decisions and in total, days per year, overlapping contracts and the contracts used.
    Recalculates the decision first, which updates its stored total_days."""
    return await _call(ctx, 'GET', _url(role, 'hrms/decision', decision_id, 'experience'))


@mcp.tool(annotations=WRITE)
@gated('write')
async def create(role: Role, resource: str, data: dict[str, Any], ctx: Context) -> Any:
    """Create a record. Use describe_resource to see the accepted fields.
    Validation errors come back as {"field": ["message"]}."""
    return await _call(ctx, 'POST', _url(role, resource), body=data)


@mcp.tool(annotations=UPDATE)
@gated('write')
async def update(role: Role, resource: str, id: int, data: dict[str, Any], ctx: Context) -> Any:
    """Change the given fields of a record (partial update); fields not in `data` stay as they are."""
    return await _call(ctx, 'PATCH', _url(role, resource, id), body=data)


@mcp.tool(annotations=DELETE)
@gated('write')
async def delete(role: Role, resource: str, id: int, ctx: Context) -> Any:
    """Permanently delete a record. This cannot be undone."""
    return await _call(ctx, 'DELETE', _url(role, resource, id))


if __name__ == '__main__':
    mcp.run(transport='streamable-http')
