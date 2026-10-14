from django.urls import path

from . import views

app_name = 'myprofile'
urlpatterns = [
    path("", views.index, name="index"),
    path('logout', views.logout_view, name='logout'),
    path('sec/associates', views.list_associates.as_view(), name='list_associates'),
    path('sec/associate/<int:pk>', views.edit_associate.as_view(), name='edit_associate'),
    path('sec/associate/<int:pk>/delete', views.delete_associate, name='delete_associate'),
    path('sec/associates/new', views.create_associate.as_view(), name='create_associate'),    
    path('sec/associates/export', views.export_associate_csv, name='export_associate_csv'),    
    
    
    path('sec/staff', views.list_staff.as_view(), name='list_staff'),    
    path('sec/staff/<int:pk>', views.edit_staff.as_view(), name='edit_staff'),
    path('sec/staff/<int:pk>/delete', views.delete_staff, name='delete_staff'),
    path('sec/staff/new', views.create_staff.as_view(), name='create_staff'),    
    path('sec/staff/export', views.export_staff_csv, name='export_staff_csv'),    
 
    path('staff/associates', views.staff_list_associates.as_view(), name='staff_list_associates'),
    path('staff/associate/<int:pk>', views.staff_edit_associate.as_view(), name='staff_edit_associate'),  
    path('staff/associate/<int:pk>/delete', views.staff_delete_associate, name='staff_delete_associate'),
    path('staff/associates/new', views.staff_create_associate.as_view(), name='staff_create_associate'),    
    
    path('staffmember-autocomplete/', views.StaffMemberAutocomplete.as_view(), name='staffmember-autocomplete'),
    path('student-autocomplete/', views.StudentAutocomplete.as_view(), name='student-autocomplete'),    
    path('phd-students-autocomplete/', views.SecScopedPhDStudentAutoComplete.as_view(), name='phd-student-autocomplete'),
    
    path('signup/<str:token>',views.signup,name='signup'),
    path('signupsuccess',views.signup_success,name='signup_success'),
    path('register/',views.register,name='register'),
    path('register/success/',views.register_success,name='register_success'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('password/change', views.password_change, name='password_change'),
    path('password/reset/info', views.password_reset_choice, name='password_reset_choice'),
    path('password/forgot', views.forgot_password, name='forgot_password'),
    path('password/token/<str:token>', views.password_token, name='password_token'),
    
    path('staff/profile/', views.profile_update.as_view(), name='staff_profile_update'),
    path('sec/profile/<int:pk>', views.sec_profile_update.as_view(), name='sec_profile_update'),
]