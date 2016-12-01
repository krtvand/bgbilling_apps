from django.contrib import admin

from .models import Question, Request, Contract, Department

class ContractInline(admin.TabularInline):
    model = Contract
    extra = 2

class RequestAdmin(admin.ModelAdmin):
    inlines = [ContractInline]
    list_display = ('it_manager_fullname', 'created_date', 'department_id')

class ContractAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'position', 'login', 'password', 'request_id')

admin.site.register(Request, RequestAdmin)
admin.site.register(Contract, ContractAdmin)
admin.site.register(Department)