from django.contrib import admin

from .models import Request, Contract, Department

class ContractInline(admin.TabularInline):
    model = Contract
    extra = 2

class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')

class RequestAdmin(admin.ModelAdmin):
    inlines = [ContractInline]
    list_display = ('it_manager_fullname', 'created_date', 'department_id')

class ContractAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'department_id', 'position', 'login', 'password', 'request_id', 'bgb_cid')

admin.site.register(Request, RequestAdmin)
admin.site.register(Contract, ContractAdmin)
admin.site.register(Department, DepartmentAdmin)