from django.urls import path

from . import views

app_name = 'hrms'
urlpatterns = [    

    
    # HR Views
    path('hr/dashboard', views.hr_dashboard, name='hr_dashboard'),    
    path('hr/create/app', views.hr_select_application_type, name='hr_create_app'),
    path('hr/create/app/employee/<int:pk>', views.hr_select_app_emp, name='hr_select_app_emp'),    
    path('hr/create/app/<int:employee_id>/<str:app_flag>', views.hr_create_app, name='hr_create_app_employee'),
    path('hr/app/<int:pk>', views.hr_update_app, name='hr_update_app'),
    path('hr/employee/<int:pk>', views.hr_employee_overview, name='hr_employee_overview'),
    path('hr/create/dec/<int:pk>', views.hr_create_decision, name='hr_create_decision'),

    path('hr/decision/info/<int:pk>', views.hr_show_decision_info, name='hr_show_decision_info'),
    path('hr/decision/yearly/<int:pk>', views.hr_decision_info_by_year, name='hr_decision_info_by_year'),

    path('hr/decision/<int:pk>', views.hr_update_decision, name='hr_update_decision'),
    path('hr/decision/<int:pk>/year/<int:year>', views.hr_decision_in_year, name='hr_decision_in_year'),
    
    path('hr/app/<int:pk>/delete', views.hr_delete_app, name='hr_delete_app'),
    path('hr/dec/<int:pk>/delete', views.hr_delete_dec, name='hr_delete_dec'),

    path('hr/create/payroll', views.hr_select_payroll_decision_type, name='hr_select_payroll_decision_type'),
    path('hr/create/payroll/employee/<int:pk>', views.hr_select_payroll_decision_emp, name='hr_select_payroll_decision_emp'),
    path('hr/create/payroll/<int:employee_id>/<str:decision_type>', views.hr_create_payroll_decision, name='hr_create_payroll_decision'),
    path('hr/payroll/<int:pk>', views.hr_update_payroll_decision, name='hr_update_payroll_decision'),
    path('hr/payroll/<int:pk>/delete', views.hr_delete_payroll_decision, name='hr_delete_payroll_decision'),

    path('hr/employees', views.hr_employee_list, name='hr_employee_list'),
    path('hr', views.hr_employee_list, name='hr'),

    path('hr/export/desc/<int:pk>', views.hr_export_decision_ints, name='hr_export_desc_int'),
    path('hr/export/app/<int:pk>', views.hr_export_applications, name='hr_export_applications'),
    path('hr/export/emp/<int:pk>', views.hr_export_apps_emp, name='hr_export_apps_emp'),

    path('hr/import/template', views.hr_apps_template, name='hr_apps_template'),
    path('hr/employee/<int:pk>/import', views.hr_upload_apps, name='hr_upload_apps'),
    path('hr/employee/<int:pk>/import/validate', views.hr_validate_apps, name='hr_validate_apps'),
    path('hr/employee/<int:pk>/import/confirm', views.hr_import_apps, name='hr_import_apps'),
    path('hr/employee/<int:pk>/apps/bulk-delete', views.hr_bulk_delete_apps, name='hr_bulk_delete_apps'),

    path('hr/employee/new/<str:etype>', views.hr_create_employee, name='hr_create_employee'),
    path('hr/employee/update/<int:pk>', views.hr_update_employee, name='hr_update_employee'),
    path('hr/employee/delete/<int:pk>', views.hr_delete_employee, name='hr_delete_employee'),

    path('emp/', views.employee_dashboard, name = 'employee_dashboard'),
    path('emp/app/<int:pk>', views.emp_update_app, name='emp_update_app'),
    path('emp/create/app', views.emp_select_application_type, name='emp_create_app'),
    path('emp/create/app/<str:app_flag>', views.emp_create_app, name='emp_create_app_employee'),
    path('emp/app/<int:pk>/delete', views.emp_delete_app, name='emp_delete_app'),

    path('emp/payroll/<int:pk>', views.emp_show_payroll_decision, name='emp_show_payroll_decision'),

]
