from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from myprofile.directories import cv_dir, id_dir, declaration_dir, pic_dir
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from curricula.models import Department, StudyProgram
from scopes.models import ScopedModelDep, ScopedModelPrg, ScopedQueryPrg, ScopedQueryDep
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from core.models import PersonStrMixin
from romanize import romanize
from scopes.utils import get_secreteriat_scope
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
User = get_user_model()
# Create your models here.

def create_user_if_required(email):

    email_split = email.split('@')
    username = email_split[0]
    domain = email_split[1]     

    if domain == settings.INTERNAL_DOMAIN:
        if not User.objects.filter(username = username).exists():        
            user = User(username=username, email=email)
            user.save()
        else:
            user = User.objects.filter(username = username).first()
    else:
        if not User.objects.filter(email = email).exists():        
            user = User(username=email, email=email)
            user.save()
        else:
            user = User.objects.filter(email = email).first()
    return user

class AdminDepartment(models.Model):
    """
    The basic department class related to the organization's deparrments
    """
    title = models.CharField(max_length=100)
    short_code = models.CharField(max_length=20)
    supervisor = models.ForeignKey('Employee', on_delete=models.SET_NULL, blank=True, null=True, related_name='sup_department')
    above = models.ForeignKey('Employee', on_delete=models.SET_NULL, blank=True, null=True, related_name='above_department')

    def __str__(self):
        return self.title + ' (' + self.short_code + ')'

class PersonalInfo(ScopedModelDep):

    GENDER_MALE = "M"
    GENDER_FEMALE = "F"
    GENDER_OTHER = "O"

    GENDER_CHOICES = (
        (GENDER_MALE, _("Άρρεν")),
        (GENDER_FEMALE, _("Θηλυ")),
        (GENDER_OTHER, _("Άλλο")),
    )

    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    given_name = models.CharField(max_length=200, null=True)
    surname = models.CharField(max_length=200, null=True)

    given_name_en = models.CharField(null=True, max_length=200)
    surname_en = models.CharField(null=True, max_length=200)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, blank=True, null=True)
    program = models.ForeignKey(StudyProgram, on_delete=models.SET_NULL, blank=True, null=True)
    email = models.EmailField(null=True)    
    secondary_email = models.EmailField(null=True)    
    fathers_name = models.CharField(max_length=50, null=True, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    tin = models.CharField(max_length=50, null=True, blank=True)
    ssn = models.CharField(max_length=50, null=True,blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True)

    home_address_street = models.CharField(max_length=70, null=True, blank=True)
    home_address_no = models.IntegerField(null=True, blank=True)
    home_address_po_box = models.CharField(max_length=30, null=True, blank=True)
    home_address_city = models.CharField(max_length=70, null=True, blank=True)
    home_address_country = models.CharField(max_length=70, null=True, default = 'Ελλάδα', blank=True)
    mobile_phone = models.CharField(max_length=30,blank=True, null=True)    
    home_phone = models.CharField(max_length=30,blank=True, null=True)

    work_address_street = models.CharField(max_length=70, null=True, default = 'Ομήρου')
    work_address_no = models.CharField(max_length=10,null=True, default='9')    
    work_address_po_box = models.CharField(max_length=30, null=True, default = '17778')
    work_address_city = models.CharField(max_length=70, null=True, default = 'Αθήνα')
    work_address_country = models.CharField(max_length=70, null=True, default = 'Ελλάδα')
    work_phone = models.CharField(max_length=20,blank=True, null=True)
    last_update = models.DateTimeField(null=True, blank=True)
    
    ieee_cv_gr = models.TextField(null=True, blank=True)
    ieee_cv_en = models.TextField(null=True, blank=True)
    scopus_id = models.CharField(null=True, blank=True)
    pic = models.ImageField(null=True, blank=True, upload_to=pic_dir)
    publications = models.TextField(null=True, blank=True)
    webpage = models.URLField(null=True, blank=True)
    
    # Square avatar (cropped)
    avatar = ImageSpecField(
        source='pic',
        processors=[ResizeToFill(300, 300)],
        format='JPEG',
        options={'quality': 85}
    )

    # Small thumbnail (for lists, navbars, etc.)
    avatar_small = ImageSpecField(
        source='pic',
        processors=[ResizeToFill(50, 50)],
        format='JPEG',
        options={'quality': 80}
    )

    def update_from_relation(self):
        if self.staffmember_set.exists():
            rel = self.staffmember_set.first()
        elif self.adminstaff_set.exists():
            rel = self.adminstaff_set.first()
        elif self.student_set.exists():
            rel = self.student_set.first()
        else:
            return False
        self.given_name = rel.given_name
        self.surname = rel.surname
        self.email = rel.email
        self.save()
        return True
    
    def update_relation(self):
        if self.staffmember_set.exists():
            rel = self.staffmember_set.first()
        elif self.adminstaff_set.exists():
            rel = self.adminstaff_set.first()
        elif self.student_set.exists():
            rel = self.student_set.first()
        else:
            return False
        rel.given_name = self.given_name
        rel.surname = self.surname
        rel.email = self.email
        rel.save()        

    def scope_query(self, scope):
        if self.staffmember_set.exists():
            staff_member = self.staffmember_set.first()
            return scope['departments'].filter(id = staff_member.internal_department.id).exists()
        elif self.associate_set.exists():
            associate = self.associate_set.first()
            return scope['departments'].filter(id = associate.department.id).exists()
        elif self.student_set.exists():
            student = self.student_set.first()
            return scope['programs'].filter(id = student.program.id).exists()
        else:
            return False
            
    def save(self, *args, **kwargs):
        self.display_name = self.email
        user = create_user_if_required(self.email)
        if self.given_name:
            user.first_name = self.given_name
        
        if self.surname:
            user.last_name = self.surname
        
        user.save()
        self.user = user
        self.last_update = timezone.now()

        if self.pk:
            old_instances = PersonalInfo.objects.filter(pk = self.pk)
            if old_instances.exists():
                old_instance = old_instances.first()
                if old_instance.pic and old_instance.pic != self.pic:
                    old_instance.pic.delete(save=False)

        if self.given_name:
            if not ( self.given_name_en and (self.given_name_en != '') ):
                self.given_name_en = romanize(self.given_name)

        if self.surname:
            if not ( self.surname_en and (self.surname_en != '') ):
                self.surname_en = romanize(self.surname)
        super().save(*args, **kwargs)

    
def create_personal_info_if_required(obj):
    email = obj.email
    pis = PersonalInfo.objects.filter(email = email)
    if not pis.exists():
        pi = PersonalInfo(email = email)
        pi.save()
    else:
        pi = pis.first()
    return pi

class ScopedStaffMemberQuery(ScopedQueryDep):
    def scope_filter(self, scope):
        return self.filter()

class AdminStaff(PersonStrMixin, ScopedModelDep):
    """
    The basic administrative staff member class. Stores information related to administrative staff members
    """
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)        
    handled_by_hr = models.BooleanField(null=True, default=False)   # Set to True if it can be handled by the HR department

    institution = models.ForeignKey('curricula.Institution', on_delete=models.SET_NULL, null=True)
    department = models.ForeignKey(AdminDepartment, on_delete=models.SET_NULL, null=True)    
    title = models.CharField(max_length=200, null=True)    
    personal_info = models.ForeignKey(PersonalInfo, blank=True, null=True, on_delete=models.SET_NULL)
   
    def to_dict(self):
        return {
            'user': getattr(getattr(self, 'user', None), 'username', ''),
            'email': getattr(self, 'email', ''),
            'given_name': getattr(self, 'given_name', ''),
            'surname': getattr(self, 'surname', ''),
            'institution': getattr(self, 'institution', ''),
            'school': getattr(self, 'school', ''),
            'department': getattr(self, 'department', ''),
            'title': getattr(self, 'title', ''),
        }

    def __str__(self):
        pi = self.personal_info
        return f'{pi.given_name} {pi.surname} ({self.title})'       
    
class StaffMember(PersonStrMixin, ScopedModelDep):
    """
    The basic staff member class. Stores information related to faculty members
    """
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)    
    email = models.EmailField(null=True)    
    given_name = models.CharField(max_length=50)
    surname = models.CharField(max_length=70)
    given_name_en = models.CharField(null=True, max_length=50)
    surname_en = models.CharField(null=True, max_length=70)
    
    display_name = models.CharField(max_length=150, null=True, blank=True)
    display_name_full = models.CharField(max_length=200, null=True, blank=True)
    display_name_en = models.CharField(max_length=150, null=True, blank=True)
    
    is_internal = models.BooleanField(null=True, default=True)    
    handled_by_hr = models.BooleanField(null=True, default=False)   # Set to True if it can be handled by the HR department

    institution = models.CharField(max_length=100, blank=True, null=True)
    institution_en = models.CharField(max_length=100, blank=True, null=True)
    school = models.CharField(max_length=100, blank=True, null=True)    
    school_en = models.CharField(max_length=100, blank=True, null=True)    
    department = models.CharField(max_length=100, blank=True, null=True)
    department_en = models.CharField(max_length=100, blank=True, null=True)
    
    internal_department = models.ForeignKey(Department, null=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=200, null=True)
    title_en = models.CharField(max_length=200, blank=True, null=True)
    research_field = models.CharField(max_length=500, blank=True, null=True)  
    research_field_en = models.CharField(max_length=500, blank=True, null=True)  
    
    office_hours = models.CharField(max_length=300, blank=True, null=True)
    office_hours_en = models.CharField(max_length=300, blank=True, null=True)
    
    office = models.CharField(max_length=300, null=True, blank=True)
    office_en = models.CharField(max_length=300, null=True, blank=True)

    personal_info = models.ForeignKey(PersonalInfo, blank=True, null=True, on_delete=models.SET_NULL)

    objects = ScopedStaffMemberQuery.as_manager()
    
    can_apply_for_phd = models.BooleanField(null=True, default=False)
    can_review_phd_apps = models.BooleanField(null=True, default=True)
    can_post_theses = models.BooleanField(null=True, default=True)
   
    def to_dict(self):
        return {
            'user': getattr(getattr(self, 'user', None), 'username', ''),
            'email': getattr(self, 'email', ''),
            'given_name': getattr(self, 'given_name', ''),
            'surname': getattr(self, 'surname', ''),
            'is_internal': getattr(self, 'is_internal', ''),
            'institution': getattr(self, 'institution', ''),
            'school': getattr(self, 'school', ''),
            'department': getattr(self, 'department', ''),
            'internal_department': getattr(getattr(self, 'internal_department', None), 'title_gr', ''),
            'title': getattr(self, 'title', ''),
            'can_apply_for_phd': getattr(self, 'can_apply_for_phd', ''),
            'can_review_phd_apps': getattr(self, 'can_review_phd_apps', ''),
            'can_post_theses': getattr(self, 'can_post_theses', ''),
        }
    
    def scope_query(self, scope):
        return True
    
    def can_edit(self, user):
        scope = get_secreteriat_scope(user)
        return scope['departments'].filter(id = self.internal_department.id).exists()
        
    def save(self, *args, **kwargs):
        self.display_name = self.given_name + ' ' + self.surname
        self.display_name_full = self.display_name + ' (' + self.title + ')'
        self.user = create_user_if_required(self.email)
        self.personal_info = create_personal_info_if_required(self) 
        self.personal_info.surname = self.surname
        self.personal_info.given_name = self.given_name
        self.personal_info.department = self.internal_department
        self.personal_info.email = self.email
        self.personal_info.save()     
        
        if not ( self.given_name_en and (self.given_name_en != '') ):
            self.given_name_en = romanize(self.given_name)

        if not ( self.surname_en and (self.surname_en != '') ):
            self.surname_en = romanize(self.surname)
            
        self.display_name_en = self.given_name_en + ' ' + self.surname_en
        
        super().save(*args, **kwargs)

class EmployeeManager(models.Manager):

    def get_from_user(self, user):
        all_faculty = Employee.objects.filter(is_faculty_staff = True)
        faculty = all_faculty.filter(faculty_staff__user=user)
        if faculty.exists():
            return faculty.first()

        all_admins = Employee.objects.filter(is_admin_staff = True)
        admins = all_admins.filter(admin_staff__user=user)
        if admins.exists():
            return admins.first()
        
        raise Employee.DoesNotExist(f"No correspoding employees found for user {user}")


class Employee(models.Model):
    is_admin_staff = models.BooleanField(null=True)
    is_faculty_staff = models.BooleanField(null=True)
    faculty_staff = models.ForeignKey(StaffMember, null=True, blank=True, on_delete=models.SET_NULL)
    admin_staff = models.ForeignKey(AdminStaff, null=True, blank=True, on_delete=models.SET_NULL)
    date_hired = models.DateField(null=True)
    wage_step_years = models.PositiveIntegerField(
        default=2,
        help_text=_('Κάθε πόσα έτη αλλάζει το ΜΚ (συνήθως 2 - ορισμένες κατηγορίες προσωπικού έχουν 3). '
                     'Δεν αφορά τη μετάβαση ΜΚ0->ΜΚ1, που είναι πάντα 1 έτος.'),
    )
    objects = EmployeeManager()

    def get_staff(self):
        if self.is_faculty_staff:
            return self.faculty_staff
        elif self.is_admin_staff:
            return self.admin_staff
    
    def get_personal_info(self):
        return self.get_staff().personal_info
    
    def child_obj(self):
        if self.is_admin_staff:
            return self.admin_staff
        else:
            return self.faculty_staff

    def given_name(self):
        return self.get_personal_info().given_name
    
    def surname(self):
        return self.get_personal_info().surname
    
    def username(self):
        return self.child_obj().user.username
    
    def email(self):
        return self.get_personal_info().email
    
    def employee_type(self):
        return _('Διοικητικό Προσωπικό') if self.admin_staff else _('Διδακτικό Προσωπικό')
    
    def __str__(self):
        if self.is_faculty_staff:
            return f'{self.faculty_staff.given_name} {self.faculty_staff.surname} ({self.faculty_staff.email})'
        elif self.is_admin_staff:
            return f'{self.admin_staff.personal_info.given_name} {self.admin_staff.personal_info.surname} ({self.admin_staff.personal_info.email})'
    
class Associate(ScopedModelDep):

    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    
    email = models.EmailField(null=True)    
    given_name = models.CharField(max_length=50)
    surname = models.CharField(max_length=70)
    display_name = models.CharField(max_length=150, null=True, blank=True)
    display_name_full = models.CharField(max_length=200, null=True, blank=True)
    department = models.ForeignKey('curricula.Department', null=True, on_delete=models.SET_NULL)
    
    is_phd_student = models.BooleanField(null=True, default=False)
    is_postdoc = models.BooleanField(null=True, default=False)
    
    card_no = models.CharField(max_length=40,blank=True, null=True)
    seat_no = models.CharField(max_length=40,blank=True, null=True)
    office_no = models.CharField(max_length=40,blank=True, null=True)

    supervisor = models.ForeignKey(StaffMember, null=True, blank=True, on_delete=models.SET_NULL)

    notes = models.TextField(blank=True, null=True)
    days_per_week = models.IntegerField(blank=True, null=True)
    contract = models.BooleanField(blank=True, null=True)
    project_contract = models.CharField(max_length=100, blank=True, null=True)
    last_update = models.DateField(blank = True, null=True )
    personal_info = models.ForeignKey(PersonalInfo, blank=True, null=True, on_delete=models.SET_NULL)
    
    def scope_query(self, scope):
        return scope['departments'].filter(id = self.department.id).exists()
    
    def save(self, *args, **kwargs):
        self.display_name = self.given_name + ' ' + self.surname
        self.personal_info = create_personal_info_if_required(self)        
        self.last_update = timezone.now()
        if self.supervisor:
            self.department = self.supervisor.internal_department

        super().save(*args, **kwargs)

    def __str__(self):
        return self.display_name
    
    def to_dict(self):
        obj = self
        d = {
            "id": obj.id,
            "email" : getattr(obj,'email',''),
            "given_name" : getattr(obj,'given_name',''),
            "surname" : getattr(obj,'surname',''),
            "is_phd_student" : getattr(obj,'is_phd_student',''),
            "is_postdoc" : getattr(obj,'is_postdoc',''),
            "days_per_week" : getattr(obj,'days_per_week',''),
            "contract" : getattr(obj,'contract',''),
            "office_no" : getattr(obj,'office_no',''),
            "seat_no" : getattr(obj,'seat_no',''),
            "last_update" : getattr(obj,'last_update','')
            }
        if hasattr(obj,'supervisor'):
            d['supervisor'] = obj.supervisor.display_name

        return d
        
    
class CustomUserPermissions(models.Model):
    class Meta:
        permissions = (
            ("is_secreteriat", "Is a secreteriat user"),
        )

class StudentQuery(ScopedQueryPrg):

    def get_profile(self, username):      
        return get_object_or_404(Student, username = username)


class Student(ScopedModelPrg):
    
    username = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)    
    email = models.EmailField(null=True)    

    given_name = models.CharField(max_length=50, null=True)
    surname = models.CharField(max_length=70, null=True)

    given_name_en = models.CharField(null=True, max_length=50)
    surname_en = models.CharField(null=True, max_length=70)

    semester = models.IntegerField(null=True)
    program = models.ForeignKey('curricula.StudyProgram', null=True, on_delete=models.SET_NULL)
    reg_num = models.CharField(max_length=70, null=True)
    display_name = models.CharField(max_length=200, null=True)
    personal_info = models.ForeignKey(PersonalInfo, on_delete=models.SET_NULL, null=True, blank=True)
    
    objects = StudentQuery.as_manager()
    def save(self, *args, **kwargs):
        
        self.user = create_user_if_required(email=self.email)   
        self.personal_info = create_personal_info_if_required(self)        
        self.username = self.user.username        
        self.display_name = self.given_name + ' ' + self.surname + ' (' + self.user.username + ')'

        self.personal_info.surname = self.surname
        self.personal_info.given_name = self.given_name
        self.personal_info.email = self.email
        self.personal_info.save()

        if self.given_name:
            if not ( self.given_name_en and (self.given_name_en != '') ):
                self.given_name_en = romanize(self.given_name)

        if self.surname:
            if not ( self.surname_en and (self.surname_en != '') ):
                self.surname_en = romanize(self.surname)

        super().save(*args, **kwargs)
           
    def __str__(self):
        if self.display_name:
            return self.display_name
        else:
            return str(self.id)

class DoctorateApplicantQuery(ScopedQueryPrg):

    def scope_filter(self, scope):
        return self.filter(
            doctorateapplication__call__program__in = scope['programs']
        )
class DoctorateApplicant(ScopedModelPrg):
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    surname = models.CharField(max_length=200, null=True)
    given_name = models.CharField(max_length=200, null=True)        
    objects = DoctorateApplicantQuery.as_manager()
    
    def save(self, *args, **kwargs):
        if self.user:
            self.given_name = self.user.first_name
            self.surname = self.user.last_name
        super().save(*args, **kwargs)
            
    def __str__(self):
        return f"{self.user.username}"        
        





