from rest_framework import serializers
from django.contrib.auth.models import User
from myprofile.models import StaffMember, Associate
from associates.models import Attendance
from curricula.models import Course
from phdstuds.models import PhdThesis
from projects.models import Project

def getattr_nested(obj, attr_path , default):
    for attr in attr_path.split('.'):
        obj = getattr(obj, attr, default)
    return obj

class StaffSerializer(serializers.ModelSerializer):
    department_title_gr = serializers.SerializerMethodField()
    department_title_en = serializers.SerializerMethodField()
    school_title_gr = serializers.SerializerMethodField()
    school_title_en = serializers.SerializerMethodField()
    institution_title_gr = serializers.SerializerMethodField()
    institution_title_en = serializers.SerializerMethodField()
    picture = serializers.SerializerMethodField()
    webpage = serializers.SerializerMethodField()

    class Meta:
        model = StaffMember
        fields = [
            'pk',
            'email',
            'given_name',
            'surname',
            'given_name_en',
            'surname_en',             
            'title',
            'title_en',
            'department_title_gr',
            'department_title_en',
            'school_title_gr',
            'school_title_en',             
            'institution_title_gr',
            'institution_title_en',             
            'research_field',
            'research_field_en',            
            'office_hours',
            'office_hours_en',            
            'office',
            'office_en',
            'webpage',
            'picture'
        ]

    def get_val(self, lang, attr, obj):
        if obj.is_internal:
            if attr == 'department':
                return getattr_nested(obj, 'internal_department.title_' + lang, '')
            elif attr == 'school':
                return getattr_nested(obj, 'internal_department.school.title_' + lang, '')
            elif attr == 'institution':
                return getattr_nested(obj, 'internal_department.school.institution.title_' + lang, '')
        else:
            if attr in ['department', 'school', 'institution']:
                if lang == 'gr':
                    return getattr_nested(obj, attr,'')
                else:
                    return getattr_nested(obj, attr+'_' + lang, '')
        return '' 
                
    def get_picture(self, obj):
        if obj.personal_info.pic:
            return obj.personal_info.pic.url
    
    def get_department_title_gr(self, obj):
        return self.get_val('gr', 'department', obj)

    def get_school_title_gr(self, obj):
        return self.get_val('gr', 'school', obj)

    def get_institution_title_gr(self, obj):
        return self.get_val('gr', 'school', obj)

    def get_department_title_en(self, obj):
        return self.get_val('en', 'department', obj)

    def get_school_title_en(self, obj):
        return self.get_val('en', 'school', obj)

    def get_institution_title_en(self, obj):
        return self.get_val('en', 'school', obj)
    
    def get_webpage(self, obj):
        return obj.personal_info.webpage
    
          

class StaffFullSerializer(StaffSerializer):
     department_title_gr = serializers.SerializerMethodField()
     department_title_en = serializers.SerializerMethodField()
     school_title_gr = serializers.SerializerMethodField()
     school_title_en = serializers.SerializerMethodField()
     institution_title_gr = serializers.SerializerMethodField()
     institution_title_en = serializers.SerializerMethodField()
     cv_en = serializers.SerializerMethodField()
     cv_gr = serializers.SerializerMethodField()
     publications = serializers.SerializerMethodField()
     scopus_id = serializers.SerializerMethodField()
     picture = serializers.SerializerMethodField()
     webpage = serializers.SerializerMethodField()
    

     class Meta:
        model = StaffMember
        fields = [
            'pk',
            'email',
            'given_name',
            'surname',
            'given_name_en',
            'surname_en',             
            'title',
            'title_en',
            'department_title_gr',
            'department_title_en',
            'school_title_gr',
            'school_title_en',             
            'institution_title_gr',
            'institution_title_en',             
            'research_field',
            'research_field_en',
            'office_hours',
            'office',
            'cv_gr',
            'cv_en',
            'publications',
            'scopus_id',
            'picture',
            'is_internal',
            'webpage',
        ]

     def get_cv_gr(self, obj):
         return obj.personal_info.ieee_cv_gr
     
     def get_cv_en(self,obj):
         return obj.personal_info.ieee_cv_en

     def get_publications(self, obj):
         return obj.personal_info.publications
     
     def get_scopus_id(self,obj):
         return obj.personal_info.scopus_id
     
     def get_picture(self, obj):
        if obj.personal_info.pic:
            return obj.personal_info.pic.url
        
     def get_webpage(self, obj):
        return obj.personal_info.webpage
        
        


class AssociateSeralizer(serializers.ModelSerializer):
    class Meta:
        model = Associate
        fields = ['surname', 'given_name', 'email']

class CourseTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['title_gr', 'title_en', 'pk', 'semester', 'elective']

class CourseSerializer(serializers.ModelSerializer):

    program_title_gr = serializers.CharField(source='program.title_gr', read_only=True)
    program_title_en = serializers.CharField(source='program.title_en', read_only=True)
    department_title_gr = serializers.CharField(source='program.department.title_gr', read_only=True)
    department_title_en = serializers.CharField(source='program.department.title_en', read_only=True)
    school_title_gr = serializers.CharField(source='program.department.school.title_gr', read_only=True)
    school_title_en = serializers.CharField(source='program.department.school.title_en', read_only=True)
    institution_title_gr = serializers.CharField(source='program.department.school.institution.title_gr', read_only=True)
    institution_title_en = serializers.CharField(source='program.department.school.institution.title_en', read_only=True)
    
    class Meta:
        model = Course
        fields = ['program',
                  'program_title_gr',
                  'program_title_en',
                  'department_title_gr',
                  'department_title_en',
                  'school_title_gr',
                  'school_title_en',
                  'institution_title_gr',
                  'institution_title_en',
                  
                 'code_gr', 
                 'code_en', 
                 'semester',
                 'title_gr',
                 'title_en' ,    
                 'weekly_hours', 
                 'weekly_lab_hours',
                 'ects_credits' ,
                 'type_gr', 
                 'type_en' ,
                 'prequesites_gr',
                 'prequesites_en' ,   
                 'url',
                 'language_gr', 
                 'language_en', 
                 'offered_erasmus',
                 'outcomes_gr',
                 'outcomes_en',
                 'skills_gr' ,
                 'skills_en' ,
                 'content_gr' ,
                 'content_en' ,
                 'delivery_gr' ,
                 'delivery_en' ,
                 'ict_gr' ,
                 'ict_en' ,
                 'elective', 
                 'hours_lecturing', 
                 'hours_lab', 
                 'hours_study', 
                 'hours_project', 
                 'hours_lab_prep',
                 ]

class PhDThesisSerializer(serializers.ModelSerializer):

    given_name_gr = serializers.CharField(source='candidate.given_name', read_only=True)
    surname_gr = serializers.CharField(source='candidate.surname', read_only=True)
    given_name_en = serializers.CharField(source='candidate.given_name_en', read_only=True)
    surname_en = serializers.CharField(source='candidate.surname_en', read_only=True)
    program_gr = serializers.CharField(source='candidate.program.title_gr', read_only=True)
    program_en = serializers.CharField(source='candidate.program.title_en', read_only=True)
    department_gr = serializers.CharField(source='candidate.program.department.title_gr', read_only=True)
    department_en = serializers.CharField(source='candidate.program.department.title_en', read_only=True)
    
    supervisor_surname_gr = serializers.CharField(source='supervisor.surname', read_only=True)
    supervisor_surname_en = serializers.CharField(source='supervisor.surname_en', read_only=True)
    supervisor_given_name_gr = serializers.CharField(source='supervisor.given_name', read_only=True)
    supervisor_given_name_en = serializers.CharField(source='supervisor.given_name_en', read_only=True)
    supervisor_title_gr = serializers.CharField(source='supervisor.title', read_only=True)
    supervisor_title_en = serializers.CharField(source='supervisor.title_en', read_only=True)
    
    class Meta:
        model = PhdThesis
        fields = ['given_name_gr',
                  'surname_gr',
                  'given_name_en',
                  'surname_en',
                  'program_gr',
                  'program_en',
                  'department_gr',
                  'department_en',
                  'subject_gr',
                  'subject_en',
                  'inscription_date',
                  'inscription_year',
                  'inscription_ga',
                  'status',
                  'graduation_date',
                  'graduation_ga',  
                  'supervisor_surname_gr',
                  'supervisor_surname_en',
                  'supervisor_given_name_gr',
                  'supervisor_given_name_en',
                  'supervisor_title_gr',
                  'supervisor_title_en'
                 ]

class ProjectSerializer(serializers.ModelSerializer):

    coordinator_surname_gr = serializers.CharField(source='coordinator.surname', read_only=True)
    coordinator_surname_en = serializers.CharField(source='coordinator.surname_en', read_only=True)
    coordinator_given_name_gr = serializers.CharField(source='coordinator.given_name', read_only=True)
    coordinator_given_name_en = serializers.CharField(source='coordinator.given_name_en', read_only=True)
    coordinator_title_gr = serializers.CharField(source='coordinator.title', read_only=True)
    coordinator_title_en = serializers.CharField(source='coordinator.title_en', read_only=True)
    department_title_en = serializers.CharField(source='coordinator.department.title_en', read_only=True)
    department_title_gr = serializers.CharField(source='coordinator.department.title_gr', read_only=True)

    class Meta:
        model = Project
        fields = [
            'approved',
            'submission_approved_ga',
            'implementation_approved_ga',
            'budget_total',
            'budget_dep',
            'call',
            'thematic_areas',
            'title',
            'department_role',
            'department_staff',
            'acronym',
            'abstract',
            'partners',
            'funding_date',
            'duration', 
            'start',
            'submission_date',
            'coordinator_surname_gr',
            'coordinator_surname_en',
            'coordinator_given_name_gr',
            'coordinator_given_name_en',
            'coordinator_title_gr',
            'coordinator_title_en',
            'department_title_en',
            'department_title_gr',
            'document_approved_submission',
            'document_approved_implementation'
    
        ]
