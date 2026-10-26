"""
Explicit registry of every model apiv2 exposes - one line per model,
grouped by app for readability. Deliberately explicit rather than
auto-discovered via apps.get_models(): adding a new model to the API is a
conscious, reviewable one-line addition here, not something that happens
silently just by adding a model to one of these apps.

MODELS (36 + 6 hrms entries) covers every concrete model in curricula, hrms,
leaves, myprofile, phdapplications, phdstuds, projects and theses and is what
the admin (superuser) endpoints at /apiv2/<app>/<model>/ expose. HR_ACCESS and
SEC_ACCESS are the subsets exposed to the HR and secretariat roles at
/apiv2/hr/... and /apiv2/sec/..., each with an access level ('rw' or 'ro'). Note phdapplications.JournalPublication/ConferencePublication
share a class name with phdstuds.JournalPublication/ConferencePublication -
harmless here since apiv2/urls.py namespaces every URL/router basename by
app_label.
"""
from curricula import models as curricula_models
from hrms import models as hrms_models
from leaves import models as leaves_models
from myprofile import models as myprofile_models
from phdapplications import models as phdapplications_models
from phdstuds import models as phdstuds_models
from projects import models as projects_models
from theses import models as theses_models

MODELS = [
    # curricula
    curricula_models.Institution,
    curricula_models.School,
    curricula_models.Department,
    curricula_models.StudyProgram,
    curricula_models.Course,
    curricula_models.Director,
    # leaves
    leaves_models.Leave,
    # myprofile
    myprofile_models.AdminDepartment,
    myprofile_models.PersonalInfo,
    myprofile_models.AdminStaff,
    myprofile_models.StaffMember,
    myprofile_models.Employee,
    myprofile_models.Associate,
    myprofile_models.CustomUserPermissions,
    myprofile_models.Student,
    myprofile_models.DoctorateApplicant,
    # phdapplications
    phdapplications_models.Call,
    phdapplications_models.Applicant,
    phdapplications_models.AppPersonalInfo,
    phdapplications_models.Application,
    phdapplications_models.Degree,
    phdapplications_models.ReferenceLetter,
    phdapplications_models.ReferenceContact,
    phdapplications_models.JournalPublication,
    phdapplications_models.ConferencePublication,
    phdapplications_models.WorkExperience,
    # phdstuds
    phdstuds_models.PhdThesis,
    phdstuds_models.JournalPublication,
    phdstuds_models.ConferencePublication,
    phdstuds_models.TeachingTask,
    phdstuds_models.ExamSupervision,
    phdstuds_models.AdministrativeTask,
    phdstuds_models.ThesisProgress,
    phdstuds_models.Recommendation,
    # projects
    projects_models.Project,
    # theses
    theses_models.Thesis,
    # hrms
    hrms_models.Application,
    hrms_models.Decision,
    hrms_models.PayrollDecision,
    hrms_models.Reference,
    hrms_models.WageClass,
    hrms_models.RankClass,
]

RW = 'rw'
RO = 'ro'

# HR role (/apiv2/hr/): the hrms app plus the employee records it works on.
HR_ACCESS = {
    hrms_models.Application: RW,
    hrms_models.Decision: RW,
    hrms_models.PayrollDecision: RW,
    hrms_models.Reference: RW,
    hrms_models.WageClass: RW,
    hrms_models.RankClass: RW,
    myprofile_models.Employee: RW,
    myprofile_models.StaffMember: RW,
    myprofile_models.AdminStaff: RW,
    myprofile_models.PersonalInfo: RW,
    myprofile_models.AdminDepartment: RW,
    curricula_models.Institution: RO,
    curricula_models.Department: RO,
}

# Secretariat role (/apiv2/sec/): only models that can be limited to the
# secretariat's programs/departments. Not exposed: PersonalInfo (ssn/tin),
# AdminStaff/AdminDepartment/Employee (HR data), CustomUserPermissions,
# Director and everything in hrms.
SEC_ACCESS = {
    # curricula
    curricula_models.Institution: RO,
    curricula_models.School: RO,
    curricula_models.Department: RO,
    curricula_models.StudyProgram: RO,
    curricula_models.Course: RW,
    # myprofile
    myprofile_models.StaffMember: RO,
    myprofile_models.Associate: RO,
    myprofile_models.Student: RW,
    myprofile_models.DoctorateApplicant: RW,
    # leaves / projects / theses
    leaves_models.Leave: RW,
    projects_models.Project: RW,
    theses_models.Thesis: RW,
    # phdapplications
    phdapplications_models.Call: RW,
    phdapplications_models.Applicant: RW,
    phdapplications_models.AppPersonalInfo: RW,
    phdapplications_models.Application: RW,
    phdapplications_models.Degree: RW,
    phdapplications_models.ReferenceLetter: RW,
    phdapplications_models.ReferenceContact: RW,
    phdapplications_models.JournalPublication: RW,
    phdapplications_models.ConferencePublication: RW,
    phdapplications_models.WorkExperience: RW,
    # phdstuds
    phdstuds_models.PhdThesis: RW,
    phdstuds_models.JournalPublication: RW,
    phdstuds_models.ConferencePublication: RW,
    phdstuds_models.TeachingTask: RW,
    phdstuds_models.ExamSupervision: RW,
    phdstuds_models.AdministrativeTask: RW,
    phdstuds_models.ThesisProgress: RW,
    phdstuds_models.Recommendation: RW,
}

# How a secretariat's queryset is limited. Default: the model manager's own
# in_scope_of(user) (scopes/models.py). Overrides below are for models whose
# manager scope is missing or does not match the real fields.
SEC_UNSCOPED = {curricula_models.Institution, curricula_models.School}

SEC_SCOPE_OVERRIDES = {
    # ScopedProjectQuery filters on coordinator__department (a text field)
    projects_models.Project: lambda qs, scope: qs.filter(
        coordinator__internal_department__in=scope['departments']),
    # No program field of its own: scope through the applicant's applications
    phdapplications_models.AppPersonalInfo: lambda qs, scope: qs.filter(
        applicant__application__call__program__in=scope['programs']),
}


# ---------------------------------------------------------------------------
# ?search= : which fields a free-text search looks at, per model. Models not
# listed use every plain text field of their own (search_fields_for()).
# ---------------------------------------------------------------------------
EMPLOYEE_NAME_FIELDS = [
    'faculty_staff__surname', 'faculty_staff__given_name', 'faculty_staff__email',
    'admin_staff__personal_info__surname', 'admin_staff__personal_info__given_name',
    'admin_staff__personal_info__email',
]


def _of_employee(prefix='employee'):
    return [f'{prefix}__{path}' for path in EMPLOYEE_NAME_FIELDS]


SEARCH_FIELDS = {
    myprofile_models.Employee: EMPLOYEE_NAME_FIELDS,
    myprofile_models.StaffMember: ['surname', 'given_name', 'surname_en', 'given_name_en', 'email', 'display_name'],
    myprofile_models.AdminStaff: ['personal_info__surname', 'personal_info__given_name', 'personal_info__email', 'title'],
    myprofile_models.PersonalInfo: ['surname', 'given_name', 'email', 'secondary_email', 'fathers_name'],
    myprofile_models.Student: ['surname', 'given_name', 'surname_en', 'given_name_en', 'username', 'reg_num', 'email'],
    hrms_models.Application: ['organization', 'contract_id', 'document2_id', 'notes', 'notes_decision'] + _of_employee(),
    hrms_models.Decision: ['ref_no', 'notes'] + _of_employee(),
    hrms_models.PayrollDecision: ['protocol_number', 'justification', 'rank'] + _of_employee(),
    hrms_models.WageClass: _of_employee(),
    hrms_models.RankClass: ['rank'] + _of_employee(),
    hrms_models.Reference: _of_employee(),
    phdstuds_models.PhdThesis: ['subject_gr', 'subject_en', 'inscription_ga', 'candidate__surname',
                                'candidate__given_name', 'candidate__reg_num'],
    leaves_models.Leave: ['country', 'city', 'organization', 'project_title', 'applicant__surname', 'applicant__given_name'],
    projects_models.Project: ['title', 'acronym', 'coordinator__surname', 'coordinator__given_name'],
}

# Related fields added on top of the automatic own-field list
SEARCH_EXTRA = {
    theses_models.Thesis: ['assigned_to__surname', 'assigned_to__reg_num', 'supervisor__surname'],
}

# Fields never searched automatically
SEARCH_EXCLUDED_NAMES = {'password', 'token', 'secret', 'tin', 'ssn'}


def search_fields_for(model):
    """Search paths for `model` (see SEARCH_FIELDS / SEARCH_EXTRA)."""
    from django.db import models as dj_models
    if model in SEARCH_FIELDS:
        return list(SEARCH_FIELDS[model])
    own = [
        f.name for f in model._meta.concrete_fields
        if isinstance(f, (dj_models.CharField, dj_models.TextField))
        and not f.choices and f.name not in SEARCH_EXCLUDED_NAMES
    ]
    return own + SEARCH_EXTRA.get(model, [])


# ---------------------------------------------------------------------------
# select_related paths needed by a model's __str__ (used for the `display`
# field), so listing 50 rows does not run 50+ extra queries.
# ---------------------------------------------------------------------------
_EMPLOYEE_STR = ['faculty_staff', 'admin_staff__personal_info']
_OF_EMPLOYEE = ['employee__faculty_staff', 'employee__admin_staff__personal_info']

DISPLAY_RELATED = {
    myprofile_models.Employee: _EMPLOYEE_STR,
    myprofile_models.AdminStaff: ['personal_info'],
    hrms_models.Application: _OF_EMPLOYEE,
    hrms_models.Decision: _OF_EMPLOYEE,
    hrms_models.PayrollDecision: _OF_EMPLOYEE,
    hrms_models.WageClass: _OF_EMPLOYEE,
    hrms_models.RankClass: _OF_EMPLOYEE,
    hrms_models.Reference: _OF_EMPLOYEE,
    leaves_models.Leave: ['applicant'],
    projects_models.Project: ['coordinator'],
}
