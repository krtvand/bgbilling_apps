from django.contrib import admin

# Register your models here.

from .models import Question, Request, Contract, Department

admin.site.register(Question)
admin.site.register(Request)
admin.site.register(Contract)
admin.site.register(Department)