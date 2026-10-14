from django.contrib import admin
import myprofile.models as m
# Register your models here.
admin.site.register(m.StaffMember)
admin.site.register(m.Associate)
admin.site.register(m.CustomUserPermissions)
admin.site.register(m.Student)
admin.site.register(m.PersonalInfo)
admin.site.register(m.AdminStaff)
admin.site.register(m.AdminDepartment)
admin.site.register(m.Employee)






