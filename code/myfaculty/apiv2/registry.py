"""
Explicit registry of every model apiv2 exposes - one line per model,
grouped by app for readability. Deliberately explicit rather than
auto-discovered via apps.get_models(): adding a new model to the API is a
conscious, reviewable one-line addition here, not something that happens
silently just by adding a model to one of these apps.

36 entries total, covering every concrete model in curricula, leaves,
myprofile, phdapplications, phdstuds, projects and theses (per the plan's
model survey). Note phdapplications.JournalPublication/ConferencePublication
share a class name with phdstuds.JournalPublication/ConferencePublication -
harmless here since apiv2/urls.py namespaces every URL/router basename by
app_label.
"""
from curricula import models as curricula_models
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
]
