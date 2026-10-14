import os
import sys
import django
from datetime import date

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myfaculty.settings")
django.setup()

from hrms.models import Application, Reference, WageClass, Decision
from myprofile.models import Employee, StaffMember

STAFF_MEMBER_EMAIL = 'staff.member@example.com'
HIRED_DATE = date(2008,4,17)

APP_DATA = [
    {
        'start' : date(2006,8,2),
        'end' : date(2007,4,10),
        'organization' : 'Χαροκόπειο',
        'day_percentage' : 0.7,
        'status' : Application.APPROVED,
        'type' : Application.FULLTIME,
    },
    {
        'start' : date(2007,1,1),
        'end' : date(2008,12,12),
        'organization' : 'ΕΚΠΑ',
        'day_percentage' : 0.5,
        'status' : Application.APPROVED,
        'type' : Application.FULLTIME,
    },
    {
        'start' : date(2006,1,1),
        'end' : date(2007,2,10),
        'organization' : 'Παν. Πειραιώς',
        'day_percentage' : 0.3,
        'status' : Application.APPROVED,
        'type' : Application.FULLTIME,
    }

]

REFERENCE_DATA = {
    'years' : 2,
    'days' : 0,
    'months' : 4,
    'ref_date' : date(2008, 4, 17)
}

WAGE_DATA = {
    'ref_date' : date(2022, 10, 6),
    'ref_value' : 16
}

DECISION_1 = {
    'date' : date(2025,2,1),
    'apps' : [0, 1]
}

DECISION_2 = {
    'date' : date(2025,5,1),
    'apps' : [2]
}

def create_employee():
    staff_member = StaffMember.objects.get(email = STAFF_MEMBER_EMAIL)
    employee = Employee.objects.filter(faculty_staff = staff_member)
    if not employee.exists():
        employee = Employee()
    else:
        employee = employee.first()
    employee.faculty_staff= staff_member 
    employee.is_faculty_staff = True 
    employee.is_admin_staff = False
    employee.date_hired = HIRED_DATE
    employee.save()
    return employee

def create_applications(employee, app_data=APP_DATA):
    Application.objects.filter(employee=employee).delete()
    objects = []
    for app in app_data:
        application = Application(
            employee = employee,
            start_date = app['start'],
            end_date = app['end'],
            day_percentage = app['day_percentage'],
            organization = app['organization'],
            status = app['status'],
            type = app['type'],
        ).save()
        objects.append(application)
    return objects

def create_reference(employee, ref_data = REFERENCE_DATA):
    ref = Reference.objects.filter(employee=employee)
    if ref.exists():
        ref = ref.first()
    else:
        ref = Reference(employee = employee)
    ref.ref_date = ref_data['ref_date']
    ref.set_from_ymd( ref_data['years'], ref_data['months'], ref_data['days'] )
    ref.save()
    return ref

def create_wage_class(employee, wage_data = WAGE_DATA):
    wc = WageClass.objects.filter(employee=employee)
    if wc.exists():
        wc = wc.first()
    else:
        wc = WageClass(employee = employee)
        
    wc.ref_date = wage_data['ref_date']
    wc.ref_value = wage_data['ref_value']
    wc.save()
    return wc

def create_decision(employee, decision_data):
    applications = Application.objects.order_by('id')
    date1 = decision_data['date']
    decision = Decision.objects.filter(date=date1)
    if decision.exists():
        decision = decision.first()
    else:
        decision = Decision(employee=employee, date=date1)
    
    decision.save()
    decision.applications.clear()

    for ord_id in decision_data['apps']:
        decision.applications.add( applications[ord_id] )
    decision.save()

    return decision

    

employee = create_employee()
applications = create_applications(employee)
applications = Application.objects.filter(employee=employee).order_by('start_date')
reference = create_reference(employee)
wageclass = create_wage_class(employee)
decision1 = create_decision(employee, DECISION_1)
decision2 = create_decision(employee, DECISION_2)

print('Original Appplications')
print('=' * 80)
for wi in applications:
    print(wi)
print('=' * 80)

imap1 = decision1.calc()
imap2 = decision2.calc()




