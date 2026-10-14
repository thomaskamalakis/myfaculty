from django import forms
from .models import StaffMember, Associate, Student, PersonalInfo
from django.forms import ModelForm
from django.conf import settings
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div, Field, HTML
from crispy_forms.bootstrap import Accordion, AccordionGroup
import re
from django.contrib.auth import get_user_model
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox
from django.core.signing import TimestampSigner
from .checks import check_password_complexity, validate_password
from django.utils.translation import gettext_lazy as _
from scopes.utils import get_secreteriat_scope
from core.forms import GenericModelForm

STAFF_FIELDS_DISABLED = ['email', 'given_name', 'surname', 'title']
ASSOCIATE_FIELDS_DISABLED = []
ASSOCIATE_FIELDS_REQUIRED = []

STUDENT_FIELDS_DISABLED = ['email', 'given_name', 'surname', 'program', 'reg_num']

LABELS = {
    "email": _("Ε-mail"),
    "given_name": _("Όνομα"),
    "surname": _("Επώνυμο"),
    "fathers_name": _("Όνομα Πατρός"),
    "date_of_birth": _("Ημερομηνία Γέννησης"),
    "tin": _("ΑΦΜ"),
    "ssn": _("ΑΜΚΑ"),
    "institution": _("Φορεάς"),
    "school": _("Σχολή"),
    "internal_department" : _("Τμήμα εντός του ιδρύματος"),
    "title": _("Ιδιότητα"),
    "home_address_street": _("Οδός"),
    "home_address_po_box": _("Ταχυδρομικός Κώδικας"),
    "home_address_city": _("Πόλη"),
    "home_address_country": _("Χώρα"),
    "mobile_phone": _("Κινητό Τηλέφωνο"),
    "home_phone": _("Τηλέφωνο Οικίας"),
    "work_address_street": _("Οδός"),
    "work_address_po_box": _("Ταχυδρομικός Κώδικας"),
    "work_address_city": _("Πόλη"),
    "work_address_country": _("Χώρα"),
    "work_phone": _("Τηλέφωνο Εργασίας"),
    "seat_no": _("Αριθμός Θέσης"),
    "office_no": _("Γραφείο"),

    "card_no": _("Αριθμός Κάρτας"),
    "program": _("Πρόγραμμα Σπουδών"),
    "reg_num": _("Αριθμός Μητρώου"),
    "is_internal": _("Είναι εσωτερικός;"),
    "notes": _("Επιπλέον Πληροφορίες"),
    "days_per_week": _("Ημέρες παρουσίας (εβδομαδίαιες)"),
    "contract": _("Έχει σύμβαση;"),
    "project_contract": _("Έργο στο οποίο εργάζεται"),
    "is_phd_student": _("Είναι υποψήφιος διδάκτορας;"),
    "is_postdoc": _("Είναι μεταδιδακτορικός;"),
    "can_apply_for_phd" : _("Μπορεί να κάνει αίτηση για διδακτορικό;"),
    "can_review_phd_apps" : _("Μπορεί να είναι αξιολογητής σε αιτήσεις διδακτορικού;"),
    "can_post_theses" : _("Μπορεί να είναι επιβλέπων ή μέλος επιτροπής διπλωματικών;"),
    "title_en" : ("Ιδιότητα (στα Αγγλικά)"),
    "research_field" : ("Γνωστικό Αντικείμενο"),
    "research_field_en" : ("Γνωστικό Αντικείμενο (στα Αγγλικά)"),
    "office" : _("Γραφείο"),
    "office_hours" : _("Ώρες Γραφείου"),    
    "office_hours_en" : _("Ώρες Γραφείου (Αγγλικά)"),    
    "institution_en": _("Φορεάς (Αγγλικά)"),
    "school_en": _("Σχολή (Αγγλικά)"),
    "department" : _("Τμήμα"),
    "department_en" : _("Τμήμα (Αγγλικά)"),
    "gender" : _("Φύλο"),
    "secondary_email" : _("Εναλλακτικό e-mail"),
    
}

profile_data = _('Στοιχεία Προφίλ')
update = _('Ενημέρωση')
home_address = _('Διεύθυνση Κατοικίας')
work_address = _('Διεύθυνση Εργασίας ')
work_no = _('Θέση Εργασίας')


SEC_STAFF_MEMBER_LAYOUT = Layout(
            Row(
               Div(HTML('<h4> %s </h4>' %profile_data),css_class = 'col-md-8'),
               Div(Submit('submit', update),css_class='col-md-4 text-end'),
               css_class="row"),
            Row(
                Div(Field('surname'),css_class = 'col-md-3'),
                Div(Field('given_name'),css_class = 'col-md-3'),
                Div(Field('email'),css_class = 'col-md-3'),                
                css_class="row"),
            Row(
                Div(Field('is_internal'),css_class = 'col-md-4'),
                css_class="row"),
            Row(
                Div(Field('institution'),css_class = 'col-md-3'),
                Div(Field('school'),css_class = 'col-md-3'),
                Div(Field('internal_department'),css_class = 'col-md-3'),
                Div(Field('title'),css_class = 'col-md-3'),
                css_class="row"),
            )

STAFF_MEMBER_LAYOUT = Layout(
            Row(
               Div(HTML('<h4> %s </h4>' %profile_data),css_class = 'col-md-8'),               
               css_class="row"),
            Row(
                Div(Field('surname'),css_class = 'col-md-4'),
                Div(Field('given_name'),css_class = 'col-md-4'),                               
                Div(Field('email'),css_class = 'col-md-4'),                
                css_class="row"),
            Row(
                Div(Field('title'),css_class = 'col-md-4'),
                css_class="row"),            
            )

ASSOCIATE_LAYOUT = Layout(
            Row(
               Div(HTML('<h4> %s </h4>' %profile_data),css_class = 'col-md-8'),
               Div(Submit('submit', update),css_class='col-md-4 text-end'),
               css_class="row"),
           Row(
                Div(Field('surname'),css_class = 'col-md-4'),
                Div(Field('given_name'),css_class = 'col-md-4'),
                css_class="row"),
            Row(
                Div(Field('email'),css_class = 'col-md-3'),                
                css_class="row"),

            Row(
                Div(Field('contract'),css_class = 'col-md-2'),
                Div(Field('project_contract'),css_class = 'col-md-2'),
                Div(Field('is_phd_student'),css_class = 'col-md-2'),                
                Div(Field('is_postdoc'),css_class = 'col-md-2'),
                Div(Field('days_per_week'),css_class = 'col-md-4'),                                
                css_class="row"),
            Row(
               Div(HTML('<p></p><h5> %s </h5>' %work_no),css_class = 'col-md-8'),
               css_class="row"),
            Row(
               Div(Field('seat_no'),css_class = 'col-md-4'),
               Div(Field('office_no'),css_class = 'col-md-4'),                
               css_class="row"),            
            Row(
                Div(Field('work_phone'),css_class = 'col-md-4'),
                css_class="row"),            
            Row(
                Div(Field('notes'),css_class = 'col-md-12'),
                css_class="row"),
    
            )

SEC_ASSOCIATE_LAYOUT = Layout(
            Row(
               Div(HTML('<h4> %s </h4>' %profile_data),css_class = 'col-md-8'),
               Div(Submit('submit', update),css_class='col-md-4 text-end'),
               css_class="row"),
            Row(
                Div(Field('surname'),css_class = 'col-md-4'),
                Div(Field('given_name'),css_class = 'col-md-4'),
                css_class="row"),
            Row(
                Div(Field('email'),css_class = 'col-md-3'),                
                css_class="row"),
            Row(
                Div(Field('contract'),css_class = 'col-md-2'),
                Div(Field('project_contract'),css_class = 'col-md-2'),
                Div(Field('is_phd_student'),css_class = 'col-md-2'),                
                Div(Field('is_postdoc'),css_class = 'col-md-2'),
                Div(Field('days_per_week'),css_class = 'col-md-4'),                                
                css_class="row"),
            Row(
               Div(HTML('<p></p><h5> %s </h5>' %work_no),css_class = 'col-md-8'),
               css_class="row"),
            Row(
               Div(Field('seat_no'),css_class = 'col-md-4'),
               Div(Field('office_no'),css_class = 'col-md-4'),                
               Div(Field('card_no'),css_class = 'col-md-4'),                
               css_class="row"),
            Row(
                Div(Field('work_phone'),css_class = 'col-md-4'),
                css_class="row"),
            Row(
                Div(Field('notes'),css_class = 'col-md-12'),
                css_class="row"),
                
            )

class StaffForm(GenericModelForm):

    class Meta:

        model = StaffMember

        fields = ['email', 
                  'given_name', 'surname', 
                  'is_internal', 'internal_department', 
                  'institution', 'school', 'department',
                  'institution_en', 'school_en', 'department_en',
                  'title', 'title_en',                  
                  'research_field', 'research_field_en',
                  'office', 'office_hours', 'office_hours_en',
                  'can_apply_for_phd', 'can_review_phd_apps', 'can_post_theses']
        
        scoped_fields = ['internal_department']

        labels = LABELS

        help_texts = {
            'department' : _('Συμπληρώστε μόνο εάν δεν είναι εσωτερικός'),
            'school' : _('Συμπληρώστε μόνο εάν δεν είναι εσωτερικός'),
            'institution' : _('Συμπληρώστε μόνο εάν δεν είναι εσωτερικός'),
            'department_en' : _('Συμπληρώστε μόνο εάν δεν είναι εσωτερικός'),
            'school_en' : _('Συμπληρώστε μόνο εάν δεν είναι εσωτερικός'),
            'institution_en' : _('Συμπληρώστε μόνο εάν δεν είναι εσωτερικός'),            
        }

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        user = kwargs.get('user')
        if instance and user:
            if instance.can_edit(user):
                super().__init__(*args, **kwargs)
            else:
                self.disabled = True
                super().__init__(*args, **kwargs)
        else:
            super().__init__(*args, **kwargs)
    # def __init__(self, *args, **kwargs):
        
        # user = kwargs.pop('user', None)
        # super().__init__(*args, **kwargs)
        # self.user = user

        # self.helper = FormHelper()

        # if self.user:
        #     scope = get_secreteriat_scope(user)
        #     self.fields['internal_department'].queryset = scope['departments']
        # else:
        #     self.fields['internal_department'].queryset = None

class AssociateForm(ModelForm):

    class Meta:
         
         model = Associate

         fields = ['email', 'given_name', 'surname']
         
         labels = LABELS

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.user = user
        self.helper = FormHelper()
        self.helper.layout = SEC_ASSOCIATE_LAYOUT

        

class AssociateFormRestricted(AssociateForm):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for k in ASSOCIATE_FIELDS_DISABLED:
            self.fields[k].disabled = True

        for k in ASSOCIATE_FIELDS_REQUIRED  :
            self.fields[k].required = True

        self.helper = FormHelper()
        self.helper.layout = ASSOCIATE_LAYOUT
             
class StaffFormRestricted(StaffForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for k in STAFF_FIELDS_DISABLED:
            self.fields[k].disabled = True

        self.helper = FormHelper()
        self.helper.layout = STAFF_MEMBER_LAYOUT
         
class StudentFormRestricted(ModelForm):

    class Meta:
        fields = STUDENT_FIELDS_DISABLED
        model = Student
        labels = LABELS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for k in STUDENT_FIELDS_DISABLED:
            self.fields[k].disabled = True

class SignUpForm(forms.Form):

    email = forms.EmailField(label=_('Το email σας') )
    name = forms.CharField(label=_('To μικρό σας όνομα'), max_length = 40)
    surname = forms.CharField(label=_('To επίθετο σας'),max_length = 100)
    password1 = forms.CharField(label=_('Κωδικός πρόσβασης'),max_length = 100, widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    password2 = forms.CharField(label=_('Κωδικός πρόσβασης (επανάληψη)'),max_length = 100, widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))

    def __init__(self, *args, **kwargs):
        email = kwargs.pop('email', None)
        super().__init__(*args, **kwargs)
        if email:
           self.fields['email'].disabled = True
           self.fields['email'].initial = email


    def complexity_message(self):
        return _('Παρακαλούμε τηρήστε τις οδηγίες στην οθόνη για τον κωδικό σας!') 
        
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data['password1']
        password2 = cleaned_data['password2']
        email = cleaned_data['email']

        validate_password(password1, password2)
        
        if settings.INTERNAL_DOMAIN in email:
            raise forms.ValidationError( _('Δεν μπορείτε να χρησιμοποιήσετε διεύθυνση ταχυδρομείου @') + settings.INTERNAL_DOMAIN)

        User = get_user_model()
        users = User.objects.filter(email = email)
        if users.count() > 0:
            raise forms.ValidationError(_('Υπάρχει ήδη χρήστης με αυτό το e-mail') )
        
        return cleaned_data
        
class RegisterForm(forms.Form):

    email1 = forms.EmailField(label=_('Το e-mail σας:') )
    email2 = forms.EmailField(label=_('Το e-mail σας (ξανά):') )
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)    

    def clean(self):
        cleaned_data = super().clean()
        if ('email1' not in cleaned_data) or ('email2' not in cleaned_data):
            raise forms.ValidationError( _('Εισάγετε μία έγκυρη διεύθυνση ηλεκτρονικού ταχυδρομείου') )
        
        email1 = cleaned_data['email1']
        email2 = cleaned_data['email2']
        
        if email1 != email2:
            raise forms.ValidationError(_('Τα email πρέπει να ταυτίζονται!') )
        
        if settings.INTERNAL_DOMAIN in email1:
            raise forms.ValidationError( _('Αν έχετε ήδη email της μορφής @') + settings.INTERNAL_DOMAIN + _(' δεν χρειάζεται να εγγραφείτε.') )
        
        User = get_user_model()
        users = User.objects.filter(email = email1)
        if users.count() > 0:
            raise forms.ValidationError( _('Υπάρχει ήδη χρήστης με αυτό το e-mail') )

class ForgotPasswordForm(forms.Form):
    email1 = forms.EmailField(label= _('Το e-mail σας:'))
    email2 = forms.EmailField(label= _('Το e-mail σας (ξανά):'))
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)    

    def clean(self):
        cleaned_data = super().clean()
        if ('email1' not in cleaned_data) or ('email2' not in cleaned_data):
            raise forms.ValidationError(_('Εισάγετε μία έγκυρη διεύθυνση ηλεκτρονικού ταχυδρομείου'))
        
        email1 = cleaned_data['email1']
        email2 = cleaned_data['email2']
        
        if email1 != email2:
            raise forms.ValidationError(_('Τα email πρέπει να ταυτίζονται!'))
        
        if settings.INTERNAL_DOMAIN in email1:
            raise forms.ValidationError(_('Αν έχετε ήδη email της μορφής @') + settings.INTERNAL_DOMAIN + _(' δεν μπορείτε να επαναφέρετε τον κωδικό σας μέσω αυτού του συστήματος.') )
        
        User = get_user_model()
        users = User.objects.filter(email = email1)
        if users.count() == 0:
            raise forms.ValidationError(_('Δεν υπάρχει χρήστης με αυτό το e-mail') )
        
          
class PasswordForm(forms.Form):

    password1 = forms.CharField(label=_('Νέος κωδικός πρόσβασης'),max_length = 100, widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    password2 = forms.CharField(label=_('Νέος κωδικός πρόσβασης (επανάληψη)'),max_length = 100, widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data['password1']
        password2 = cleaned_data['password2']
        validate_password(password1, password2)


PROFILE_INFO_FIELDS = ['pic', 'ieee_cv_gr', 'ieee_cv_en', 'publications', 'scopus_id']
PROFILE_INFO_LABELS = {
    'pic' : _('Φωτογραφία Προφίλ'),
    'ieee_cv_gr' : _('Βιογραφικό σημείωμα (τύπου IEEE) στα Ελληνικά'), 
    'ieee_cv_en' : _('Βιογραφικό σημείωμα (τύπου IEEE) στα Αγγλικά'), 
    'scopus_id' : _('Αναγνωριστικό στο Scopus'),
    'publications' : _('Ενδειτικές δημοσιεύσεις')
}

PROFILE_INFO_HELP = {
    'pic' : _('Παρακαλούμε χρησιμοποιείστε μία φωτογραφία με ικανοποιητική ευκρίνεια.'),
    'ieee_cv_gr' : _('Βιογραφικό σημείωμα με απλό κείμενο (plain-text) που χρησιμοποιούμε σε δημοσιεύσεις IEEE στα Ελληνικά.'), 
    'ieee_cv_en' : _('Βιογραφικό σημείωμα με απλό κείμενο (plain-text) που χρησιμοποιούμε σε δημοσιεύσεις IEEE στα Αγγλικά.'),     
    'scopus_id' : _('Αν δεν τον γνωρίζετε μπορείτε να το αναζητήσετε στο Scopus'),
    'publications' : _('Μία λίστα με ενδεικτές δημοσιεύσεις. Συμπεριλάβετε τίτλο, συγγραφείς, όνομα περιοδικού/συνέδρίου, έτος, κτλ.')
}

class ProfileForm(GenericModelForm):

    required_fields_extra = PROFILE_INFO_FIELDS
    
    class Meta:
        model = PersonalInfo
        fields = PROFILE_INFO_FIELDS
        labels = PROFILE_INFO_LABELS    

SEC_PROFILE_INFO_FIELDS = ['given_name', 'surname', 'pic', 'ieee_cv_gr', 'ieee_cv_en', 'publications', 'scopus_id', 'webpage']
SEC_PROFILE_INFO_LABELS = {
    'given_name' : _('Όνομα'),
    'surname' : _('Επώνυμο'),    
    'pic' : _('Φωτογραφία Προφίλ'),
    'ieee_cv_gr' : _('Βιογραφικό σημείωμα (τύπου IEEE) στα Ελληνικά'), 
    'ieee_cv_en' : _('Βιογραφικό σημείωμα (τύπου IEEE) στα Αγγλικά'), 
    'scopus_id' : _('Αναγνωριστικό στο Scopus'),
    'publications' : _('Ενδειτικές δημοσιεύσεις'),
    'webpage' : _('Ιστοσελίδα'),
    
}

class SecProfileForm(GenericModelForm):

    required_fields_extra = PROFILE_INFO_FIELDS
    disabled_fields = ['given_name', 'surname']
    class Meta:
        model = PersonalInfo
        fields = SEC_PROFILE_INFO_FIELDS
        labels = SEC_PROFILE_INFO_LABELS

class HrStaffForm(GenericModelForm):

    class Meta:

        model = StaffMember

        fields = ['email', 
                  'given_name', 'surname', 
                  'is_internal', 'internal_department', 
                  'title', 'title_en',                  
                  'research_field', 'research_field_en',
                  'can_apply_for_phd', 'can_review_phd_apps', 'can_post_theses']

        labels = LABELS

PI_FORM_LAYOUT = Layout(
    Row(
    Div(HTML('<h4> %s </h4>' %_('Ενημέρωση Προσωπικών Στοιχείων')),css_class = 'col-md-8'),
    Div(Submit('submit', _('Yποβολή')),css_class='col-md-4 text-end'),
    css_class="row"),
    Accordion(
        AccordionGroup(
            _("Βασικά Στοιχεία"),
            Row(
                Column("given_name", css_class="col-md-6"),
                Column("surname", css_class="col-md-6"),
            ),
            Row(
                Column("fathers_name", css_class="col-md-4"),
                Column("gender", css_class="col-md-4"),
                Column("date_of_birth", css_class="col-md-4"),
            ),
            Row(
                Column("tin", css_class="col-md-6"),
                Column("ssn", css_class="col-md-6"),
            ),
            "pic",
        ),

        AccordionGroup(
            _("Ακαδημαϊκά Στοιχεία"),
            Row(
                Column("department", css_class="col-md-6"),
                Column("program", css_class="col-md-6"),
            ),
        ),
        AccordionGroup(
            _("Στοιχεία Επικοινωνίας"),

            Row(
                Column("email", css_class="col-md-6"),
                Column("secondary_email", css_class="col-md-6"),
            ),
            Row(
                Column("mobile_phone", css_class="col-md-6"),
                Column("home_phone", css_class="col-md-6"),
            ),
        ),

        AccordionGroup(
            _("Διεύθυνση Κατοικίας"),
            Row(
                Column("home_address_street", css_class="col-md-5"),
                Column("home_address_no", css_class="col-md-2"),
                Column("home_address_po_box", css_class="col-md-5"),
            ),
            Row(
                Column("home_address_city", css_class="col-md-6"),
                Column("home_address_country", css_class="col-md-6"),
            ),
        ),
        AccordionGroup(
            _("Στοιχεία Εργασίας"),

            Row(
                Column("work_address_street", css_class="col-md-5"),
                Column("work_address_no", css_class="col-md-2"),
                Column("work_address_po_box", css_class="col-md-5"),
            ),
            Row(
                Column("work_address_city", css_class="col-md-6"),
                Column("work_address_country", css_class="col-md-6"),
            ),
            "work_phone",
        ),
        AccordionGroup(
            _("Βιογραφικό και Ερευνητικό Έργο"),
            "scopus_id",
            "ieee_cv_gr",
            "ieee_cv_en",
            "publications",
        ),

    )
)

PI_LABELS = {
        "given_name": _("Όνομα"),
        "surname": _("Επώνυμο"),

        "given_name_en": _("Όνομα στα Αγγλικά"),
        "surname_en": _("Επώνυμο στα Αγγλικά"),

        "department": _("Τμήμα"),
        "program": _("Πρόγραμμα Σπουδών"),

        "email": _("Ηλεκτρονικό Ταχυδρομείο"),
        "secondary_email": _("Δευτερεύον Ηλεκτρονικό Ταχυδρομείο"),

        "fathers_name": _("Πατρώνυμο"),
        "date_of_birth": _("Ημερομηνία Γέννησης"),

        "tin": _("Α.Φ.Μ."),
        "ssn": _("Α.Μ.Κ.Α."),

        "gender": _("Φύλο"),

        "home_address_street": _("Οδός Κατοικίας"),
        "home_address_no": _("Αριθμός"),
        "home_address_po_box": _("Ταχυδρομικός Κώδικας"),
        "home_address_city": _("Πόλη"),
        "home_address_country": _("Χώρα"),

        "mobile_phone": _("Κινητό Τηλέφωνο"),
        "home_phone": _("Τηλέφωνο Κατοικίας"),

        "work_address_street": _("Οδός Εργασίας"),
        "work_address_no": _("Αριθμός"),
        "work_address_po_box": _("Ταχυδρομικός Κώδικας"),
        "work_address_city": _("Πόλη"),
        "work_address_country": _("Χώρα"),
        "work_phone": _("Τηλέφωνο Εργασίας"),

        "pic": _("Φωτογραφία"),

        "scopus_id": _("Scopus ID"),

        "ieee_cv_gr": _("Σύντομο Βιογραφικό (Ελληνικά)"),
        "ieee_cv_en": _("Σύντομο Βιογραφικό (Αγγλικά)"),

        "publications": _("Δημοσιεύσεις"),
    }

PI_FIELDS = {
        "given_name",
        "surname",
        "department",
        "program",
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
        "pic",
        "scopus_id",
        "ieee_cv_gr",
        "ieee_cv_en",
        "publications",
    }
class HrPIForm(GenericModelForm):
    
    class Meta:
        model = PersonalInfo
        fields = PI_FIELDS
        labels = PI_LABELS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = PI_FORM_LAYOUT



        


    

