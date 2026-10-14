from django.urls import path, include
from .views import StaffMemberFullApiView, StaffMemberApiView, AssociateApiView, AttendanceApiView, CourseApiView, CourseListApiView, StaffMemberFullListApiView, CourseFullListApiView, PhDThesesFullListApiView, ProjectView
from rest_framework.authtoken import views

urlpatterns= [
    path('staff/', StaffMemberFullApiView.as_view()),
    path('staff/list', StaffMemberApiView.as_view()),
    path('staff/list/full', StaffMemberFullListApiView.as_view()),
    
    path('associates/', AssociateApiView.as_view()),
    path('attendances/', AttendanceApiView.as_view()),
    path('course/', CourseApiView.as_view()),
    path('program/courses', CourseListApiView.as_view()), 
    path('program/courses/full', CourseFullListApiView.as_view()), 
    path('phds/full', PhDThesesFullListApiView.as_view()), 
    path('projects/full', ProjectView.as_view()), 
    path('auth/', views.obtain_auth_token)
]