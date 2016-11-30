from django import forms
from django.forms import ModelForm

from .models import Request, Department

class RequestForm(ModelForm):
    class Meta:
        model = Request
        fields = ['it_manager_fullname', 'it_manager_position', 'it_manager_email', 'department_id']

