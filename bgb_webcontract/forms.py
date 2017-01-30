from django import forms
from django.forms import ModelForm, BaseModelFormSet, BaseInlineFormSet
from django.forms import inlineformset_factory
from django.forms import modelformset_factory, modelform_factory
from .models import Request, Department, Contract

class RequestForm(ModelForm):
    class Meta:
        model = Request
        fields = ['it_manager_fullname', 'it_manager_position', 'it_manager_email', 'department_id']


class ContractModelForm(ModelForm):

    class Meta:
        model = Contract
        fields = ['full_name', 'position']


class ContractBaseInlineFormset(BaseInlineFormSet):
    def save(self, commit=True):
        contracts = super().save(commit=False)
        for contract in contracts:
            if contract.request_id:
                contract.department_id_id = contract.request_id.department_id_id
                if commit:
                    contract.save()
            else:
                raise Exception('Can not save contract {}. Contract object doesnt have request id. '
                                'May be related request object doesnt saved yet'.format(contract.full_name))
        return contracts

ContractFormset = inlineformset_factory(Request, Contract, ContractModelForm, ContractBaseInlineFormset)