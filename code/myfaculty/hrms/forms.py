from core.forms import GenericModelForm, GenericForm
import hrms.models as m
from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from myprofile.models import Employee, PersonalInfo, create_user_if_required, create_personal_info_if_required
from curricula.models import Department, Institution
from myprofile.models import AdminDepartment, AdminStaff, StaffMember
from myprofile.forms import LABELS, PI_LABELS
from crispy_forms.layout import Layout, Submit, Row, Column, Div, Field, HTML, Fieldset
from django.contrib.auth import get_user_model
from core.utils import update_obj, create_or_update_obj

User = get_user_model()

WAGE_FORM_LABELS = {
    'ref_date' : _('Ημερομηνία Αναφοράς'),
    'employee' : _('Εργαζόμενος'),
    'ref_value' : _('ΜΚ αναφοράς')
}

class WageClassForm(GenericModelForm):

    class Meta:
        model = m.WageClass
        labels = WAGE_FORM_LABELS
        fields = ['ref_date', 'employee', 'ref_value']

WORK_EXP_REF_LABELS = {
    'ref_date' : _('Ημερομηνία Αναφοράς'),
    'employee' : _('Εργαζόμενος'),
    'no_days' : _('Συνολικός Αριθμός Ημερών'),
    'years' : _('Χρόνια'),
    'months' : _('Μήνες'),
    'days' : _('Μέρες'),
}

   
APPLICATION_LABELS = {
    'date_submitted' : _('Ημερομηνία Υποβολής'),
    'date_approved' : _('Ημερομηνία Έγκρισης'),
    'start_date' : _('Έναρξη Διαστήματος Προϋπηρεσίας'),
    'end_date' : _('Λήξη Διαστήματος Προϋπηρεσίας'),
    'related_document1' : _('Σύμβαση'),
    'related_document2' : _('Βεβαίωση'),
    'employee' : _('Εργαζόμενος'),
    'payment' : _('Συνολική Αμοιβή (βάσει σύμβασης)'),
    'organization' : _('Εργοδότης'),
    'notes' : _('Σημειώσεις'),
    'contract_id' : _('Αριθμός Πρωτοκόλλου Σύμβασης'),
    'document2_id' : _('Αριθμός Πρωτοκόλλου Βεβαίωσης'),    
    'status' : _('Κατάσταση'),
    'type' : _('Τύπος Σύμβασης'),
    'day_percentage' : _('Ποσοστό Αναγνώρισης'),
    'assignment_percentage' : _('Ανάθεση (σε έκτα)'),
    'no_days' : _('Αριθός Ημερών Εργασίας'),
    'no_hours' : _('Αριθός Ωρών'),
    'worktype' : _('Τύπος Προυπηρεσίας'),
    'ref_hours' : _('Ωρες που αντιστοιχούν σε πλήρη ημέρα διδασκαλίας'),
    'work_type' : _('Τύπος παρεχόμενης εργασίας'),
    'notes' : _('Επισημάνσεις Αιτούντα'),
    'notes_decision' : _('Επισημάνσεις Υπηρεσίας'),
    
}

HELP_TEXTS = {
    'assignment_percentage' : _('π.χ. για ανάθεση 2/6, συμπληρώστε 2'),
    'ref_hours' : _('ο αριθμός των ωρών που αντιστοιχεί σε μία πλήρη ημέρα διδασκαλίας, συχνά αναφέρεται στη σύμβαση'),
    'work_type' : _('Διδασκαλία ή έρευνα')
}

class HrForm(GenericModelForm):
    submit_button_text = 'Υποβολή'
    submit_button_icon = 'check'
    date_picker = False
    
    class Meta:
        model = None
        labels = APPLICATION_LABELS
        fields = '__all__'  
        help_texts = HELP_TEXTS      

    
def employees_by_name():
    # Αλφαβητικά κατά επώνυμο και όνομα (διδακτικό ή διοικητικό προσωπικό)
    return Employee.objects.order_by(
        'faculty_staff__surname', 'faculty_staff__given_name',
        'admin_staff__personal_info__surname', 'admin_staff__personal_info__given_name')


class HrSelectAppplicationType(GenericModelForm):
    
    submit_button_text = 'Υποβολή'
    submit_button_icon = 'check'
    required_fields_extra = ['type', 'employee']
    class Meta:
        model = m.Application
        labels = APPLICATION_LABELS
        fields = ['type', 'employee'] 

    def __init__(self, *args, employee=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = employees_by_name()
        if employee:
            self.fields['employee'].initial = employee
            self.fields['employee'].disabled = True
               
class ApplicationForm(HrForm):

    class Meta:
        model = m.Application
        labels = APPLICATION_LABELS
        fields = '__all__'

    def __init__(self, *args, employee=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.employee = employee

    def clean(self):
        now = timezone.now().date()
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date > now:
            self.add_error( 'start_date', _('Δεν μπορείτε να καταχωρήσετε μελλονική ημερομηνία') )

        if start_date > end_date:
            self.add_error( 'start_date', _('H ημερομηνία έναρξης δεν μπορεί να είναι μεγαλύτερη από την ημερομηνία λήξης') )
      
        if self.employee:
            if self.employee.date_hired:
                date_hired = self.employee.date_hired
                if start_date > date_hired:
                    msg = _("Η ημερομηνία έναρξης δεν μπορεί να υπερβαίνει την ημερομηνία πρόσληψης %(date)s") % {
                        "date" : date_hired.strftime("%d/%m/%Y")
                    }
                    self.add_error( 'start_date', msg )
                
        return cleaned_data

class HrApplicatioForm(ApplicationForm):

    class Meta:
        model = m.Application
        labels = APPLICATION_LABELS
        fields = '__all__'


COMMON_APP_FIELDS = ['start_date', 
                     'end_date',
                     'contract_id',                     
                     'related_document1',
                     'document2_id',                     
                     'related_document2',
                     'organization',
                     'notes',                     
                     'status',
                     'notes_decision',
                     'notes',
                     'work_type']

class HrFullTimeAppForm(HrApplicatioForm):

    class Meta:
        fields = COMMON_APP_FIELDS
        model = m.Application
        labels = APPLICATION_LABELS

class HrWorkContractAppForm(HrApplicatioForm):

    required_fields_extra = ['payment']
    
    class Meta:
        fields = COMMON_APP_FIELDS + ['payment']
        model = m.Application
        labels = APPLICATION_LABELS

class HrTeachingApp407Form(HrApplicatioForm):

    required_fields_extra = ['assignment_percentage']

    class Meta:
        fields = COMMON_APP_FIELDS + ['assignment_percentage']
        model = m.Application
        labels = APPLICATION_LABELS
        help_texts = HELP_TEXTS

    def clean(self):
        cleaned_data = super().clean()
        assignment_percentage = cleaned_data['assignment_percentage']
        if assignment_percentage < 0:
            self.add_error('assignment_percentage', _('Δεν μπορείτε να καταχωρήσετε αρνητικό αριθμό.') )
        if assignment_percentage > 6:
            self.add_error('assignment_percentage', _('Δεν μπορείτε να καταχωρήσετε αριθμό μεγαλύτερο του 6.') )

        return cleaned_data

class HrTeachingAppHourlyForm(HrApplicatioForm):

    required_fields_extra = ['no_hours', 'ref_hours']

    class Meta:
        fields = COMMON_APP_FIELDS + ['no_hours', 'ref_hours']
        model = m.Application
        labels = APPLICATION_LABELS
        help_texts = HELP_TEXTS

class HrTeachingAppDaysForm(HrApplicatioForm):

    required_fields_extra = ['no_days']

    class Meta:
        fields = COMMON_APP_FIELDS + ['no_days']
        model = m.Application
        labels = APPLICATION_LABELS
        help_texts = HELP_TEXTS

class HrOtherAppForm(HrApplicatioForm):

    class Meta:
        fields = COMMON_APP_FIELDS + ['day_percentage']
        model = m.Application
        labels = APPLICATION_LABELS

class HrExternalAppForm(HrApplicatioForm):
    """Εμπειρία εξωτερικού: το ποσοστό προϋπηρεσίας δίνεται 0-100 (όπως στη βεβαίωση)
    και αποθηκεύεται ως δεκαδικό 0-1 στο day_percentage."""

    required_fields_extra = ['day_percentage']

    class Meta:
        fields = COMMON_APP_FIELDS + ['day_percentage']
        model = m.Application
        labels = APPLICATION_LABELS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields['day_percentage']
        field.validators = [MinValueValidator(0.01), MaxValueValidator(100)]
        field.help_text = _('Ποσοστό 0-100, π.χ. 70 για 70%')
        if self.instance and self.instance.day_percentage is not None:
            self.initial['day_percentage'] = round(self.instance.day_percentage * 100, 2)

    def clean_day_percentage(self):
        return self.cleaned_data['day_percentage'] / 100



DECISION_LABELS = {
    'applications' : _('Συμβάσεις που περιλαμβάνονται στην απόφαση'),
    'date' : _('Ημερομηνία απόφασης'),
    'document' : _('Κείμενο Απόφασης'),
    'notes' : _('Σημειώσεις'),
    'ref_no' : _('Αριθμός Πρωτοκόλλου')
}

class HrDecisionForm(GenericModelForm):
    
    class Meta:
        model = m.Decision
        labels = DECISION_LABELS
        fields = ['ref_no', 'applications', 'date', 'document', 'notes']

        widgets = {
            'applications': forms.SelectMultiple(
                attrs={'size': 15}
            )
        }

    def __init__(self, *args, employee=None, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            employee = self.instance.employee

        application_q = m.Application.objects.filter(
            employee = employee, decisions__isnull = True, status = m.Application.APPROVED
        )
        if self.instance.pk:
            application_q = self.instance.applications.all() | application_q
        
        self.fields['applications'].queryset = application_q


PAYROLL_DECISION_LABELS = {
    'employee': _('Εργαζόμενος'),
    'decision_type': _('Τύπος Απόφασης'),
    'decision_date': _('Ημερομηνία Πράξης'),
    'effective_date': _('Ημερομηνία Ισχύος'),
    'protocol_number': _('Αριθμός Πρωτοκόλλου'),
    'wage_class': _('Μισθολογικό Κλιμάκιο'),
    'rank': _('Βαθμίδα'),
    'responsibility_position': _('Θέση Ευθύνης'),
    'term_end_date': _('Λήξη Θητείας'),
    'legal_framework': _('Νομοθετικό Πλαίσιο'),
    'justification': _('Αιτιολογία'),
    'prior_service_years': _('Προϋπηρεσία (Έτη)'),
    'prior_service_months': _('Προϋπηρεσία (Μήνες)'),
    'prior_service_days': _('Προϋπηρεσία (Ημέρες)'),
    'total_prior_service_days': _('Σύνολο Ημερών Προϋπηρεσίας'),
    'document': _('Πράξη/Απόφαση (PDF)'),
    'summary_document': _('Περίληψη Πράξης'),
    'transmittal_document': _('Διαβιβαστικό'),
    'oath_document': _('Πρωτόκολλο Ορκωμοσίας'),
    'duty_assumption_document': _('Πρωτόκολλο Ανάληψης Καθηκόντων'),
    'notes': _('Παρατηρήσεις'),
    'linked_decision': _('Συνδεδεμένη Απόφαση Αναγνώρισης'),
}

# Τα 4 companion-document πεδία (και το responsibility_position) αφορούν
# αποκλειστικά τους νέους τύπους APPOINTMENT/DUTY_ASSUMPTION (βλ.
# APPOINTMENT_FIELDS/DUTY_ASSUMPTION_FIELDS πιο κάτω, το καθένα με το δικό
# του υποσύνολο - δες τα σχόλια εκεί) - ΔΕΝ μπαίνουν σε κανένα από τα παλιά
# field-list constants παρακάτω, ώστε οι φόρμες των παλιών ειδών απόφασης
# να μείνουν ακριβώς όπως ήταν πριν.

# source_file_path/alternate_files είναι scandocs-importer bookkeeping
# fields, όχι κάτι που συμπληρώνει η HR με το χέρι - μένουν έξω από όλες τις
# φόρμες, επεξεργάσιμα μόνο μέσω /admin ή του import script.
PAYROLL_DECISION_FIELDS = [
    'decision_date', 'effective_date', 'protocol_number',
    'wage_class', 'rank', 'legal_framework', 'justification',
    'prior_service_years', 'prior_service_months', 'prior_service_days',
    'total_prior_service_days',
    'document', 'notes', 'linked_decision',
]

class HrSelectPayrollDecisionType(GenericModelForm):

    submit_button_text = 'Υποβολή'
    submit_button_icon = 'check'
    required_fields_extra = ['decision_type', 'employee']

    class Meta:
        model = m.PayrollDecision
        labels = PAYROLL_DECISION_LABELS
        fields = ['decision_type', 'employee']

    def __init__(self, *args, employee=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = employees_by_name()
        if employee:
            self.fields['employee'].initial = employee
            self.fields['employee'].disabled = True


class HrPayrollDecisionForm(HrForm):

    class Meta:
        model = m.PayrollDecision
        labels = PAYROLL_DECISION_LABELS
        fields = PAYROLL_DECISION_FIELDS

    def __init__(self, *args, employee=None, decision_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.employee = employee
        self.decision_type = decision_type
        if self.instance.pk:
            employee = self.instance.employee
        if employee:
            self.fields['linked_decision'].queryset = m.Decision.objects.filter(employee=employee)
        else:
            self.fields['linked_decision'].queryset = m.Decision.objects.none()


class HrPriorServiceRecognitionSystemForm(HrForm):
    """Αναγνώριση προϋπηρεσίας υπολογιζόμενη από το σύστημα: η HR δηλώνει
    μόνο ποιά Decision αντιστοιχεί· τα υπόλοιπα στοιχεία κληρονομούνται από
    αυτήν μέσω PayrollDecision.sync_from_linked_decision()."""

    required_fields_extra = ['linked_decision', 'effective_date']

    class Meta:
        model = m.PayrollDecision
        labels = PAYROLL_DECISION_LABELS
        fields = ['linked_decision', 'effective_date', 'legal_framework']

    def __init__(self, *args, employee=None, decision_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.employee = employee
        self.decision_type = decision_type
        if self.instance.pk:
            employee = self.instance.employee
        if employee:
            self.fields['linked_decision'].queryset = m.Decision.objects.filter(employee=employee)
        else:
            self.fields['linked_decision'].queryset = m.Decision.objects.none()


class HrPriorServiceRecognitionLegacyForm(HrPayrollDecisionForm):
    """Αναγνώριση προϋπηρεσίας από παλαιά/εισαγόμενα δεδομένα (π.χ.
    scandocs) - ίδια πεδία με τη γενική φόρμα· ξεχωριστή κλάση ώστε κάθε
    decision_type να αντιστοιχίζεται 1-1 σε φόρμα, όπως θα γίνει και για
    τους υπόλοιπους τύπους αργότερα."""
    pass


WAGE_PROGRESSION_FIELDS = [
    'decision_date', 'effective_date', 'protocol_number', 'wage_class',
    'justification', 'legal_framework', 'document', 'notes',
]

class HrWageProgressionForm(HrForm):
    """Μισθολογική εξέλιξη: δεν αφορά βαθμίδα, προϋπηρεσία ή linked_decision -
    μικρότερο, αποκλειστικό σύνολο πεδίων."""

    class Meta:
        model = m.PayrollDecision
        labels = PAYROLL_DECISION_LABELS
        fields = WAGE_PROGRESSION_FIELDS

    def __init__(self, *args, employee=None, decision_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.employee = employee
        self.decision_type = decision_type


LEGAL_FRAMEWORK_RECLASSIFICATION_FIELDS = [
    'decision_date', 'effective_date', 'protocol_number', 'wage_class',
    'justification', 'legal_framework', 'document', 'notes',
]

class HrLegalFrameworkReclassificationForm(HrForm):
    """Συλλογική κατάταξη λόγω αλλαγής νομοθετικού πλαισίου: ίδια πεδία με
    το HrWageProgressionForm - η διαφορά είναι στο PayrollDecision.save(),
    που εξαιρεί ρητά αυτόν τον τύπο από το sync_employee_wage_class() (δεν
    μηδενίζει το ρολόι μέχρι το επόμενο ΜΚ)."""

    class Meta:
        model = m.PayrollDecision
        labels = PAYROLL_DECISION_LABELS
        fields = LEGAL_FRAMEWORK_RECLASSIFICATION_FIELDS

    def __init__(self, *args, employee=None, decision_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.employee = employee
        self.decision_type = decision_type


INDIVIDUAL_RANKING_FIELDS = [
    'decision_date', 'effective_date', 'protocol_number', 'wage_class',
    'justification', 'legal_framework', 'document', 'notes',
]

class HrIndividualRankingForm(HrForm):
    """Μισθολογική κατάταξη: ίδιο σύνολο πεδίων με το HrWageProgressionForm
    σήμερα, αλλά ξεχωριστή κλάση/λίστα ώστε να μπορεί να διαφοροποιηθεί
    ανεξάρτητα αν το HR ζητήσει κάτι παραπάνω στο μέλλον."""

    class Meta:
        model = m.PayrollDecision
        labels = PAYROLL_DECISION_LABELS
        fields = INDIVIDUAL_RANKING_FIELDS

    def __init__(self, *args, employee=None, decision_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.employee = employee
        self.decision_type = decision_type


RANK_PROMOTION_FIELDS = [
    'decision_date', 'effective_date', 'protocol_number', 'rank',
    'justification', 'legal_framework', 'document', 'notes',
]

class HrRankPromotionForm(HrForm):
    """Εξέλιξη/Προαγωγή βαθμίδας: αλλαγή ακαδημαϊκής βαθμίδας (π.χ. Επίκουρος
    -> Αναπληρωτής -> Καθηγητής) - η νέα βαθμίδα καταχωρείται στο `rank`, όχι
    στο `wage_class` (που αφορά το INDIVIDUAL_RANKING/μισθολογική κατάταξη)."""

    class Meta:
        model = m.PayrollDecision
        labels = PAYROLL_DECISION_LABELS
        fields = RANK_PROMOTION_FIELDS

    def __init__(self, *args, employee=None, decision_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.employee = employee
        self.decision_type = decision_type


class HrGradeChangeForm(HrForm):
    """Αλλαγή διοικητικού βαθμού (Α/Β/Γ/Δ) του διοικητικού προσωπικού - η νέα
    τιμή καταχωρείται στο `rank` (ίδιο πεδίο με το HrRankPromotionForm, απλά
    διαφορετικό νόημα/decision_type)."""

    class Meta:
        model = m.PayrollDecision
        labels = PAYROLL_DECISION_LABELS
        fields = RANK_PROMOTION_FIELDS

    def __init__(self, *args, employee=None, decision_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.employee = employee
        self.decision_type = decision_type


# Πραγματικά δεδομένα (employee_history.csv) δείχνουν πράξη/περίληψη/
# διαβιβαστικό μόνο σε Διορισμό, ποτέ ορκωμοσία/ανάληψη καθηκόντων -
# ξεχωριστό companion-document υποσύνολο από το DUTY_ASSUMPTION_FIELDS πιο
# κάτω, όχι το ίδιο σε όλους τους νέους τύπους. Το responsibility_position
# επίσης ΔΕΝ μπαίνει εδώ - στα πραγματικά δεδομένα εμφανίζεται μόνο σε
# Ανάληψη_καθηκόντων (π.χ. Κοσμήτορας), ποτέ σε Διορισμό (πάντα rank εκεί).
APPOINTMENT_FIELDS = [
    'decision_date', 'effective_date', 'protocol_number', 'rank',
    'justification', 'legal_framework',
    'document', 'summary_document', 'transmittal_document', 'notes',
]


class HrAppointmentForm(HrForm):
    """Διορισμός: αρχική τοποθέτηση - καταγράφει τη βαθμίδα/θέση ευθύνης
    εκκίνησης, όχι το ΜΚ (αυτό ξεκινά με ξεχωριστή WAGE_PROGRESSION/
    INDIVIDUAL_RANKING απόφαση)."""

    class Meta:
        model = m.PayrollDecision
        labels = PAYROLL_DECISION_LABELS
        fields = APPOINTMENT_FIELDS

    def __init__(self, *args, employee=None, decision_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.employee = employee
        self.decision_type = decision_type


# Αντίστροφα από το APPOINTMENT_FIELDS: πραγματικά δεδομένα δείχνουν
# ορκωμοσία/ανάληψη καθηκόντων μόνο σε Ανάληψη_καθηκόντων, ποτέ πράξη/
# περίληψη/διαβιβαστικό - δεν υπάρχει καν δικιά της "πράξη" σε αυτόν τον
# τύπο (η πράξη ανήκει στο προηγούμενο γεγονός Διορισμού/αλλαγής βαθμίδας),
# οπότε ούτε το βασικό 'document' δεν μπαίνει εδώ.
DUTY_ASSUMPTION_FIELDS = [
    'decision_date', 'effective_date', 'protocol_number', 'rank',
    'responsibility_position', 'term_end_date', 'justification', 'legal_framework',
    'oath_document', 'duty_assumption_document', 'notes',
]


class HrDutyAssumptionForm(HrForm):
    """Ανάληψη καθηκόντων. Το save() του PayrollDecision συμπληρώνει
    αυτόματα το Employee.date_hired από αυτόν τον τύπο, όταν είναι ακόμα
    κενό (βλ. sync_employee_date_hired στο hrms/models.py)."""

    class Meta:
        model = m.PayrollDecision
        labels = PAYROLL_DECISION_LABELS
        fields = DUTY_ASSUMPTION_FIELDS

    def __init__(self, *args, employee=None, decision_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.employee = employee
        self.decision_type = decision_type


# Αναγνώριση συνάφειας (μεταπτυχιακού/διδακτορικού): η αναγνώριση αυτή καθαυτή
# δεν έχει δικό της ΜΚ/effective_date - το ίδιο έγγραφο συνήθως περιλαμβάνει
# επιπλέον και μία κατάταξη (με "πλεονάζοντα χρόνο") και ενδεχομένως διαδοχικές
# εξελίξεις σε επόμενα ΜΚ, οι οποίες καταχωρούνται ξεχωριστά ως δικές τους
# INDIVIDUAL_RANKING/WAGE_PROGRESSION εγγραφές (ίδιο protocol_number/document).
RELEVANCE_RECOGNITION_FIELDS = [
    'decision_date', 'protocol_number', 'legal_framework',
    'justification', 'document', 'notes',
]

class HrMastersRelevanceRecognitionForm(HrForm):
    """Αναγνώριση συνάφειας μεταπτυχιακού."""

    class Meta:
        model = m.PayrollDecision
        labels = PAYROLL_DECISION_LABELS
        fields = RELEVANCE_RECOGNITION_FIELDS

    def __init__(self, *args, employee=None, decision_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.employee = employee
        self.decision_type = decision_type


class HrPhdRelevanceRecognitionForm(HrForm):
    """Αναγνώριση συνάφειας διδακτορικού - ίδιο σύνολο πεδίων με το
    HrMastersRelevanceRecognitionForm, ξεχωριστή κλάση για ανεξάρτητη
    μελλοντική διαφοροποίηση."""

    class Meta:
        model = m.PayrollDecision
        labels = PAYROLL_DECISION_LABELS
        fields = RELEVANCE_RECOGNITION_FIELDS

    def __init__(self, *args, employee=None, decision_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.employee = employee
        self.decision_type = decision_type


REFERENCE_FIELDS = ['ref_date', 'no_days', 'employee']
REFERENCE_LABELS = {
    'ref_date' : _('Ημερομηνία Αναφοράς'),
    'no_days' : _('Ημέρες Προυπηρεσίας'),
    'employee' : _('Εργαζόμενος'),    
}

class HrReferenceForm(GenericModelForm):

    class Meta:
        model = m.Reference
        labels = REFERENCE_LABELS
        fields = REFERENCE_FIELDS

    def __init__(self, *args, employee=None, **kwargs):
        super().__init__(*args, **kwargs)
        if employee:
            self.fields['employee'].initial = employee
            self.fields['employee'].disabled = True

EMPLOYEE_LABELS = {
    'date_hired' : _('Ημερομηνία Πρόσληψης'),
    "academic_department" : _('Ακαδημαϊκό Τμήμα'),
    "admin_department" : _('Διοικητικό Τμήμα'),
    "we_ref_value" : _('Αναγνωρισμένες Μέρες Προϋπηρεσίας Αναφοράς'),
    "we_ref_date" : _('Ημερομηνία Αναφοράς Προϋπηρεσίας'),
    "wage_ref_value" : _('Μισθοδολογικό Κλιμάκιο Αναφοράς'),
    "wage_ref_date" : _('Ημερομηνία Αναφοράς Μισθολογικού Κλιμακίου'),
    "wage_step_years" : _('Έτη ανά ΜΚ'),
    "title" : _('Τίτλος'),
        
}

def HR_EMPLOYEE_FORM_LAYOUT(admin_staff=False):

    department_field = "admin_department" if admin_staff else "academic_department"

    return Layout(

        Div(
           Submit("submit", _("Αποθήκευση"), css_class="btn btn-primary"),
            css_class="d-flex justify-content-end mt-4",
        ),

        Fieldset(
            _("Προσωπικές Πληροφορίες"),
            Row(
                Column("surname", css_class="col-md-6"),
                Column("given_name", css_class="col-md-6"),
            ),
            Row(
                Column("surname_en", css_class="col-md-6"),
                Column("given_name_en", css_class="col-md-6"),
            ),

            Row(
                Column("fathers_name", css_class="col-md-6"),
                Column("gender", css_class="col-md-6"),
            ),

            Row(
                Column("date_of_birth", css_class="col-md-6"),
                Column("date_hired", css_class="col-md-6"),
            ),

            Row(
                Column("tin", css_class="col-md-6"),
                Column("ssn", css_class="col-md-6"),
            ),
            css_class="hr-fieldset"
        ),

        Fieldset(
        _("Τμήμα στον οργανισμό"),
            Row(
                Column(department_field, css_class="col-md-6"),
            ),
            css_class="hr-fieldset"
        ),
        Fieldset(_("Ιδιότητα"),
           Row(
                Column("title", css_class="col-md-6"),
            ),
            css_class="hr-fieldset"
        ),
        Fieldset(
        _("Στοιχεία Αναφοράς Προϋπηρεσίας"),
            Row(
                Column("we_ref_date", css_class="col-md-6"),
                Column("we_ref_value", css_class="col-md-6"),                
            ),
            css_class="hr-fieldset"
        ),
        Fieldset(
        _("Στοιχεία Αναφοράς Μισθοδολογικού Κλιμακίου"),
            Row(
                Column("wage_ref_date", css_class="col-md-4"),
                Column("wage_ref_value", css_class="col-md-4"),
                Column("wage_step_years", css_class="col-md-4"),
            ),
            css_class="hr-fieldset"
        ),        
        Fieldset(
            _("Στοιχεία Επικοινωνίας"),

            Row(
                Column("email", css_class="col-md-6"),
                Column("secondary_email", css_class="col-md-6"),
            ),

            Row(
                Column("mobile_phone", css_class="col-md-6"),
                Column("home_phone", css_class="col-md-6"),
            ),
            css_class="hr-fieldset"
        ),

        Fieldset(
            _("Διεύθυνση Κατοικίας"),

            Row(
                Column("home_address_street", css_class="col-md-8"),
                Column("home_address_no", css_class="col-md-4"),
            ),

            Row(
                Column("home_address_po_box", css_class="col-md-4"),
                Column("home_address_city", css_class="col-md-8"),
            ),

            Row(
                Column("home_address_country", css_class="col-md-6"),
            ),
            css_class="hr-fieldset"
        ),

        Fieldset(
            _("Διεύθυνση Εργασίας"),

            Row(
                Column("work_address_street", css_class="col-md-8"),
                Column("work_address_no", css_class="col-md-4"),
            ),

            Row(
                Column("work_address_po_box", css_class="col-md-4"),
                Column("work_address_city", css_class="col-md-8"),
            ),

            Row(
                Column("work_address_country", css_class="col-md-6"),
                Column("work_phone", css_class="col-md-6"),
            ),
            css_class="hr-fieldset"
        ),
    )

PI_FIELDS_TO_UPDATE = [
    "given_name",
    "surname",
    "given_name_en",
    "surname_en",
    "email",
    "secondary_email",
    "fathers_name",
    "date_of_birth",
    "tin",
    "ssn",
    "gender",
    "home_address_street",
    "home_address_no",
    "home_address_po_box",
    "home_address_city",
    "home_address_country",
    "mobile_phone",
    "home_phone",
    "work_address_street",
    "work_address_no",
    "work_address_po_box",
    "work_address_city",
    "work_address_country",
    "work_phone",
]

class HrEmployeeForm(GenericForm):

    date_hired = forms.DateField()
    surname = forms.CharField(max_length=100)
    given_name = forms.CharField(max_length=100)
    surname_en = forms.CharField(max_length=100, required=False)
    given_name_en = forms.CharField(max_length=100, required=False)
    fathers_name = forms.CharField(max_length=100, required=False)
    date_of_birth = forms.DateField(required=False)
    title = forms.CharField(max_length=100)

    tin = forms.CharField(required=False)
    ssn = forms.CharField(required=False)
    gender = forms.ChoiceField(choices=PersonalInfo.GENDER_CHOICES, help_text = _('Επιλέξτε'))    
    email = forms.EmailField()
    secondary_email = forms.EmailField(required=False)
    
    academic_department = forms.ModelChoiceField(queryset = Department.objects.all(),empty_label = _('Επιλέξτε'))
    admin_department = forms.ModelChoiceField(queryset = AdminDepartment.objects.all(), empty_label = _('Επιλέξτε'))

    wage_ref_date = forms.DateField()
    wage_ref_value = forms.IntegerField(min_value = 0)
    wage_step_years = forms.IntegerField(min_value = 1, initial = 2)

    we_ref_date = forms.DateField()
    we_ref_value = forms.IntegerField(min_value = 0)

    home_address_street = forms.CharField(max_length=70, required=False)
    home_address_no = forms.IntegerField(required=False)
    home_address_po_box = forms.CharField(max_length=30, required=False)
    home_address_city = forms.CharField(max_length=70, required=False)
    home_address_country = forms.CharField(max_length=70, required=False)
    mobile_phone = forms.CharField(max_length=30, required=False)    
    home_phone = forms.CharField(max_length=30, required=False)

    work_address_street = forms.CharField(max_length=70, required=False)
    work_address_no = forms.CharField(max_length=10, required=False)    
    work_address_po_box = forms.CharField(max_length=30, required=False)
    work_address_city = forms.CharField(max_length=70, required=False)
    work_address_country = forms.CharField(max_length=70, required=False)
    work_phone = forms.CharField(max_length=20, required=False)
    
    config = {
        'labels' : EMPLOYEE_LABELS | PI_LABELS,
    }

    #def set_initial_values(self, employee):

    def __init__(self, *args, admin_staff=False, employee = None, **kwargs):

        super().__init__(*args, **kwargs)
        self.employee = employee

        if employee:
            admin_staff = employee.is_admin_staff
        self.admin_staff=admin_staff
        

        if admin_staff:
            del self.fields['academic_department']
            self.fields['title'].required = False
        else:
            del self.fields['admin_department']
            self.fields['title'].required = True

        # Set initial values if this form is used for update
        
        self.set_form_init_values()
        self.helper.layout = HR_EMPLOYEE_FORM_LAYOUT(admin_staff=admin_staff)
        

    def get_init_values(self):
        employee = self.employee        
        init_values = {}
        pi = employee.get_personal_info()

        if self.admin_staff:
            init_values['admin_department'] = employee.admin_staff.department
        else:
            init_values['academic_department'] = employee.faculty_staff.internal_department
            init_values['title'] = employee.faculty_staff.title
        
        init_values['date_hired'] = employee.date_hired
        init_values['wage_step_years'] = employee.wage_step_years

        for k in PI_FIELDS_TO_UPDATE:
            if k in self.fields:
                init_values[k] = getattr(pi, k)

        wageclass=m.WageClass.objects.filter(employee=employee)
        if wageclass.exists():
            wageclass=wageclass.first()
            init_values['wage_ref_date'] = wageclass.ref_date
            init_values['wage_ref_value'] = wageclass.ref_value

        we=m.Reference.objects.filter(employee=employee)
        if we.exists():
            we=we.first()
            init_values['we_ref_date'] = we.ref_date
            init_values['we_ref_value'] = we.no_days
            
        return init_values
    
    def set_form_init_values(self):
        if self.employee:
            init_values = self.get_init_values()
        else:
            now = timezone.localdate()
            init_values = {
                'wage_ref_date' : now,
                'wage_ref_value' : 0,
                'wage_step_years' : 2,
                'we_ref_date' : now,
                'we_ref_value' : 0,
            }
        for k, v in init_values.items():
                if k in self.fields:
                    self.fields[k].initial = v

    def user_attrs(self):
        data = self.cleaned_data
        return {
            'first_name' : data['given_name'],
            'last_name' : data['surname'],
        }
    
    def pi_attrs(self):
        data = self.cleaned_data
        d = {}
        for k in PI_FIELDS_TO_UPDATE:
            if k in data:
                d[k] = data[k]
        return d
                  
    def save(self):
        data = self.cleaned_data
        email = self.cleaned_data['email']
        
        # Check that the user exists, if not create it. User is updated based on the form data
        user = create_user_if_required(email)
        user = update_obj(user, self.user_attrs())
        
        # Check that the personal information instance exists, if not create it. Instance is updated based on the form data
        pi = create_or_update_obj(PersonalInfo, self.pi_attrs(), email=email)

        # Check StaffMember of AdminStaff instance
        if self.admin_staff:
            admin_data = {
                'user' : user,
                'handled_by_hr' : True,
                'institution' : Institution.objects.first(),
                'department' : data['admin_department'],
                'personal_info' : pi
            }
            admin_staff = create_or_update_obj(AdminStaff, admin_data, user=user)            
        else:
            department = data['academic_department']
            staff_data = {
                'user' : user,
                'email' : data['email'],
                'given_name' : data['given_name'],
                'surname' : data['surname'],
                'is_internal' : True,
                'handled_by_hr' : True,
                'department' : department.title_gr,
                'school' : department.school.title_gr,
                'institution' : department.school.institution.title_gr,
                'internal_department' : department,
                'personal_info' : pi,
                'title' : data['title']
            } 
            staff_member = create_or_update_obj(StaffMember, staff_data, user=user)            

        # Check for the employee instance and update it if it exists. Otherwise create it
        if self.admin_staff:
            employee_data = {
                'is_admin_staff' : True,
                'is_faculty_staff' : False,
                'admin_staff' : admin_staff,
                'date_hired' : data['date_hired'],
                'wage_step_years' : data['wage_step_years'],
                'faculty_staff' : None
            }
            employee = create_or_update_obj(Employee, employee_data, admin_staff=admin_staff )
        else:
            employee_data = {
                'is_admin_staff' : False,
                'is_faculty_staff' : True,
                'faculty_staff' : staff_member,
                'date_hired' : data['date_hired'],
                'wage_step_years' : data['wage_step_years'],
                'admin_staff' : None
            }
            employee = create_or_update_obj(Employee, employee_data, faculty_staff=staff_member )

        # Create wage class and work experience reference instances

        we_data = {
            'ref_date' : data['we_ref_date'],
            'no_days' : data['we_ref_value'],        
            'employee' : employee    
        }
        wage_data = {
            'ref_date' : data['wage_ref_date'],
            'ref_value' : data['wage_ref_value'],            
            'employee' : employee
        }
        
        wageclass = create_or_update_obj(m.WageClass, wage_data, employee=employee)
        we = create_or_update_obj(m.Reference, we_data, employee=employee)
        
        return employee

class EmpForm(GenericModelForm):
    submit_button_text = 'Υποβολή'
    submit_button_icon = 'check'
    date_picker = True
    
    class Meta:
        model = None
        labels = APPLICATION_LABELS
        fields = '__all__'
        help_texts = HELP_TEXTS

class EmpPayrollDecisionForm(EmpForm):

    class Meta:
        model = m.PayrollDecision
        labels = PAYROLL_DECISION_LABELS
        fields = PAYROLL_DECISION_FIELDS

    def __init__(self, *args, employee=None, decision_type=None, **kwargs):
        kwargs['disabled'] = True
        super().__init__(*args, **kwargs)
        self.employee = employee
        self.decision_type = decision_type

class EmpSelectAppplicationType(GenericModelForm):
    
    submit_button_text = 'Υποβολή'
    submit_button_icon = 'check'
    required_fields_extra = ['type']
    
    class Meta:
        model = m.Application
        labels = APPLICATION_LABELS
        fields = ['type'] 
        help_texts= {'type' : 'Επιλέξτε τον τύπο της σύμβασης βάσει των οδηγιών.'}
        
class EmpApplicationForm(ApplicationForm):

    class Meta:
        model = m.Application
        labels = APPLICATION_LABELS
        fields = '__all__'

    def __init__(self, *args, employee=None, **kwargs):

        instance = kwargs.get('instance', None)
        disabled = False

        if instance:
            if instance.status != m.Application.PENDING:
                disabled = True


        super().__init__(*args, disabled = disabled, **kwargs)
        self.employee = employee

        # # Disable form if status is not pending
        # if self.instance.status != m.Application.PENDING:
        #     self.disable()        
        
    def clean(self):
        # This checks dates etc.
        cleaned_data = super().clean()
        
        # The employee must upload either a related document or the contract itself or both

        related_document1 = cleaned_data.get("related_document1")
        related_document2 = cleaned_data.get("related_document2")
        contract_id = cleaned_data.get("contract_id")
        document2_id = cleaned_data.get("document2_id")
        
        if not related_document1 and not related_document2:
            raise forms.ValidationError(
                _("Πρέπει να ανεβάσετε το αρχείο της σύμβασης ή το αρχείο της βεβαίωσης από τον οικείο φορέα στο αντίστοιχο πεδίο της φόρμας.")
            )
    
        if related_document1 and (not contract_id or (contract_id == "") ):
            self.add_error("contract_id",
                _("Πρέπει να συμπληρώσετε τον αριθμό της σύμβασης όπως αναγράφεται σε αυτήν.")
            )
        
        if related_document2 and (not document2_id or (document2_id == "") ):
            self.add_error("document2_id",
                _("Πρέπει να συμπληρώσετε τον αριθμό της βεβαίωσης όπως αναγράφεται σε αυτήν.")
            )

        return cleaned_data

EMP_COMMON_APP_FIELDS = ['start_date', 
                     'end_date',
                     'contract_id',                    
                     'related_document1',
                     'document2_id',                     
                     'related_document2',
                     'organization',
                     'notes',
                     'work_type']

class EmpFullTimeAppForm(EmpApplicationForm):

    class Meta:
        fields = EMP_COMMON_APP_FIELDS
        model = m.Application
        labels = APPLICATION_LABELS

class EmpWorkContractAppForm(EmpApplicationForm):

    required_fields_extra = ['payment']
    
    class Meta:
        fields = EMP_COMMON_APP_FIELDS + ['payment']
        model = m.Application
        labels = APPLICATION_LABELS
     
class EmpTeachingApp407Form(EmpApplicationForm):

    required_fields_extra = ['assignment_percentage']

    class Meta:
        fields = EMP_COMMON_APP_FIELDS + ['assignment_percentage']
        model = m.Application
        labels = APPLICATION_LABELS
        help_texts = HELP_TEXTS

    def clean(self):
        cleaned_data = super().clean()
        assignment_percentage = cleaned_data['assignment_percentage']
        if assignment_percentage < 0:
            self.add_error('assignment_percentage', _('Δεν μπορείτε να καταχωρήσετε αρνητικό αριθμό.') )
        if assignment_percentage > 6:
            self.add_error('assignment_percentage', _('Δεν μπορείτε να καταχωρήσετε αριθμό μεγαλύτερο του 6.') )

        return cleaned_data

class EmpTeachingAppHourlyForm(EmpApplicationForm):

    required_fields_extra = ['no_hours', 'ref_hours']

    class Meta:
        fields = EMP_COMMON_APP_FIELDS + ['no_hours', 'ref_hours']
        model = m.Application
        labels = APPLICATION_LABELS
        help_texts = HELP_TEXTS

class EmpTeachingAppDaysForm(EmpApplicationForm):

    required_fields_extra = ['no_days']

    class Meta:
        fields = EMP_COMMON_APP_FIELDS + ['no_days']
        model = m.Application
        labels = APPLICATION_LABELS
        help_texts = HELP_TEXTS

class EmpOtherAppForm(EmpApplicationForm):

    class Meta:
        fields = EMP_COMMON_APP_FIELDS + ['day_percentage']
        model = m.Application
        labels = APPLICATION_LABELS

class EmpExternalAppForm(EmpApplicationForm):
    """Βλ. HrExternalAppForm - ίδια λογική ποσοστού 0-100."""

    required_fields_extra = ['day_percentage']

    class Meta:
        fields = EMP_COMMON_APP_FIELDS + ['day_percentage']
        model = m.Application
        labels = APPLICATION_LABELS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields['day_percentage']
        field.validators = [MinValueValidator(0.01), MaxValueValidator(100)]
        field.help_text = _('Ποσοστό 0-100, π.χ. 70 για 70%')
        if self.instance and self.instance.day_percentage is not None:
            self.initial['day_percentage'] = round(self.instance.day_percentage * 100, 2)

    def clean_day_percentage(self):
        return self.cleaned_data['day_percentage'] / 100


            




    



    
        





