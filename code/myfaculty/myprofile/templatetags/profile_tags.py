from django import template
from myprofile.models import StaffMember, Student
from scopes.models import Secretariat
from myprofile.checks import is_secreteriat, is_student, is_staff_member, is_hr_user, is_handled_by_hr
register = template.Library()

@register.filter(name="is_secretariat")
def test_sec(user):
    return is_secreteriat(user)

@register.filter(name="is_staff_member")
def test_staff_member(user):
    return is_staff_member(user)
    
@register.filter(name="is_student")
def test_student(user):
    return is_student(user)

@register.filter(name="is_hr")
def test_for_hr(user):
    return is_hr_user(user)

@register.filter(name="is_employee")
def test_for_employee(user):
    return is_handled_by_hr(user)