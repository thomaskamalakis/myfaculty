from django.core.exceptions import FieldDoesNotExist, FieldError, ValidationError
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError, PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from scopes.utils import get_secreteriat_scope

from . import actions, hooks
from .permissions import IsHrRole, IsReadOnly, IsSecretariatRole, IsSuperUser
from .registry import DISPLAY_RELATED, RO, SEC_SCOPE_OVERRIDES, SEC_UNSCOPED, search_fields_for

# Query params reserved for pagination/DRF machinery - never treated as
# model-field filters.
RESERVED_QUERY_PARAMS = {'page', 'page_size', 'format', 'search', 'expand'}

# ?search= limits
MAX_SEARCH_TERMS = 6
MAX_TERM_LENGTH = 100

# Field names that must never be filterable by the non-admin roles, even on
# an allowed model (a filter on them would work as a guessing oracle).
FORBIDDEN_FILTER_PARTS = {'password', 'token', 'secret'}

ADMIN, HR, SEC = 'admin', 'hr', 'sec'
ROLE_PERMISSION = {ADMIN: IsSuperUser, HR: IsHrRole, SEC: IsSecretariatRole}


class ApiV2Pagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 500


def check_filter_key(model, key, allowed_models):
    """Walks a Django lookup such as 'applicant__user__password__startswith'
    and rejects it if it crosses into a model outside `allowed_models` (so
    the non-admin roles can never reach e.g. auth.User) or names a
    forbidden field. Returns nothing; raises ParseError."""
    current = model
    parts = key.split('__')
    for index, part in enumerate(parts):
        if part in FORBIDDEN_FILTER_PARTS:
            raise ParseError(f'Invalid filter parameter: {key}')
        try:
            field = current._meta.get_field(part)
        except FieldDoesNotExist:
            # 'pk', or a lookup/transform such as icontains - nothing left to cross
            return
        if not field.is_relation:
            return
        if index == len(parts) - 1:
            # Filtering on the relation itself (compares ids) crosses nothing
            return
        current = field.related_model
        if current not in allowed_models:
            raise ParseError(f'Invalid filter parameter: {key}')



def resolve_search_fields(model, allowed_models):
    """The model's search paths that stay inside `allowed_models`. A path
    that names a field that does not exist is a configuration error and
    stops the server at startup; one that merely crosses into a model the
    role cannot access is dropped."""
    resolved = []
    for path in search_fields_for(model):
        current = model
        usable = True
        parts = path.split('__')
        for index, part in enumerate(parts):
            try:
                field = current._meta.get_field(part)
            except FieldDoesNotExist:
                raise ImproperlyConfigured(f'apiv2 search field {model.__name__}.{path}: no field {part!r}')
            if index < len(parts) - 1:
                current = field.related_model
                if current is None or current not in allowed_models:
                    usable = False
                    break
        if usable:
            resolved.append(path)
    return resolved


def parse_expand(model, raw, allowed_models):
    """Validates ?expand=a,b: forward FK/OneToOne/M2M fields of `model`
    pointing to a model the role can access. Returns the list of names."""
    names = [n.strip() for n in (raw or '').split(',') if n.strip()]
    for name in names:
        try:
            field = model._meta.get_field(name)
        except FieldDoesNotExist:
            raise ParseError(f'Cannot expand {name!r}.')
        forward = field.is_relation and not field.auto_created and (
            field.many_to_one or field.one_to_one or field.many_to_many)
        if not forward or field.related_model not in allowed_models:
            raise ParseError(f'Cannot expand {name!r}.')
    return names


def _make_action(url_path, function):
    def handler(self, request, pk=None):
        return Response(function(request, self.get_object()))
    handler.__name__ = url_path
    return action(detail=True, methods=['get'], url_path=url_path, url_name=url_path)(handler)


def build_viewset(model, serializer_cls, role=ADMIN, access='rw', allowed_models=()):
    """Builds a full-CRUD ModelViewSet for `model`: list/create/retrieve/
    update/partial_update/destroy, one instance at a time via the URL's
    <pk> (never a query param or request body).

    `role` selects who may call it: ADMIN (superuser only, sees every row),
    HR (HR staff, every row) or SEC (a secretariat, limited to the rows in
    its scope; a superuser sees everything). `access` 'ro' makes the
    endpoint read-only. Any query param not in RESERVED_QUERY_PARAMS is
    passed straight to queryset.filter(**kwargs) - Django's own "__" lookup
    syntax gives dotted related-field filtering for free (e.g.
    ?user__username=jdoe&is_internal=True). For HR/SEC the lookups may only
    cross into models the role can itself access (check_filter_key).

    UI-side business rules the plain serializer would skip (validation,
    recalculation of decisions) are applied through hooks.py."""

    search_fields = resolve_search_fields(model, set(allowed_models) or {model})
    permissions = [ROLE_PERMISSION[role]]
    if access == RO:
        permissions.append(IsReadOnly)

    class GenericModelViewSet(viewsets.ModelViewSet):
        serializer_class = serializer_cls
        permission_classes = permissions
        # TokenAuthentication is already the project-wide default
        # (settings.REST_FRAMEWORK) - SessionAuthentication is added here
        # too so a superuser already logged into the site can use DRF's
        # browsable API directly without obtaining a token first.
        authentication_classes = [TokenAuthentication, SessionAuthentication]
        pagination_class = ApiV2Pagination

        def base_queryset(self):
            if role != SEC or self.request.user.is_superuser or model in SEC_UNSCOPED:
                return model.objects.all()
            override = SEC_SCOPE_OVERRIDES.get(model)
            if override:
                scope = get_secreteriat_scope(self.request.user)
                return override(model.objects.all(), scope).distinct()
            return model.objects.in_scope_of(self.request.user).distinct()

        def get_serializer_context(self):
            context = super().get_serializer_context()
            context['expand'] = self.expand_names()
            return context

        def expand_names(self):
            if not hasattr(self, '_expand_names'):
                self._expand_names = parse_expand(model, self.request.query_params.get('expand'), allowed_models)
            return self._expand_names

        def apply_search(self, qs):
            terms = self.request.query_params.get('search', '').split()[:MAX_SEARCH_TERMS]
            if not terms or not search_fields:
                return qs
            for term in terms:
                term = term[:MAX_TERM_LENGTH]
                condition = Q()
                for path in search_fields:
                    condition |= Q(**{f'{path}__icontains': term})
                qs = qs.filter(condition)
            return qs.distinct()

        def apply_related(self, qs):
            """select_related for what str() reads (the `display` field) and
            for ?expand=..., so a page of rows does not trigger N+1 queries."""
            select = list(DISPLAY_RELATED.get(model, ()))
            prefetch = []
            for name in self.expand_names():
                field = model._meta.get_field(name)
                if field.many_to_many:
                    prefetch.append(name)
                else:
                    select.append(name)
                    select += [f'{name}__{p}' for p in DISPLAY_RELATED.get(field.related_model, ())]
            if select:
                qs = qs.select_related(*select)
            if prefetch:
                qs = qs.prefetch_related(*prefetch)
            return qs

        def get_queryset(self):
            qs = self.apply_related(self.base_queryset())
            qs = self.apply_search(qs)
            filters = {k: v for k, v in self.request.query_params.items() if k not in RESERVED_QUERY_PARAMS}
            if filters:
                if role != ADMIN:
                    for key in filters:
                        check_filter_key(model, key, allowed_models)
                try:
                    qs = qs.filter(**filters)
                except (FieldError, ValueError, ValidationError, TypeError) as e:
                    raise ParseError(f'Invalid filter parameters: {e}')
            return qs

        def _save(self, serializer):
            with transaction.atomic():
                instance = serializer.save()
                hooks.after_save(instance)
                # A secretariat must not create or move a row out of its own
                # scope; raising here rolls the whole transaction back.
                if role == SEC and not self.base_queryset().filter(pk=instance.pk).exists():
                    raise PermissionDenied('The object is outside your scope.')

        def perform_create(self, serializer):
            self._save(serializer)

        def perform_update(self, serializer):
            self._save(serializer)

        def perform_destroy(self, instance):
            with transaction.atomic():
                state = hooks.before_delete(instance)
                instance.delete()
                hooks.after_delete(instance, state)

    # Read-only computed endpoints (apiv2/actions.py), e.g. .../employee/<pk>/summary/
    # Not offered to the secretariat role.
    for url_path, function in ({} if role == SEC else actions.ACTIONS.get(model, {})).items():
        setattr(GenericModelViewSet, url_path, _make_action(url_path, function))

    GenericModelViewSet.__name__ = f'{model.__name__}ViewSet'
    return GenericModelViewSet
