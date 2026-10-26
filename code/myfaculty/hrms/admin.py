from django.contrib import admin
import hrms.models as m

# Register your models here.
admin.site.register(m.Application)
admin.site.register(m.Reference)
admin.site.register(m.WageClass)
admin.site.register(m.RankClass)
admin.site.register(m.Decision)
admin.site.register(m.PayrollDecision)