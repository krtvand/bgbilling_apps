from django import forms
from django.forms import ModelForm, BaseModelFormSet
from django.forms import inlineformset_factory
from django.forms import modelformset_factory, modelform_factory
from .models import Request, Department, Contract

# class RequestForm(ModelForm):
#     class Meta:
#         model = Request
#         fields = ['it_manager_fullname', 'it_manager_position', 'it_manager_email', 'department_id']


class ContractModelForm(ModelForm):

    class Meta:
        model = Contract
        fields = ['full_name', 'position']


class ContractBaseFormset(BaseModelFormSet):
    def save(self, commit=True, *args, **kwargs):
        contracts = super().save(commit=False)
        for contract in contracts:
            if 'department_id' in kwargs and 'request_id' in kwargs:
                contract.department_id_id = kwargs['department_id']
                contract.request_id_id = kwargs['request_id']
                if commit:
                    contract.save()
            # Если мы сначала передали аргументы, но не сохранили,
            # возможен вызов метода save без дополнительных параметров
            elif contract.department_id_id and contract.request_id_id:
                if commit:
                    contract.save()
            else:
                raise Exception('Can not save contract {}. Contract object require '
                                'additional attributes, but not present'.format(contract.full_name))
        return contracts

ContractFormset = modelformset_factory(Contract, form=ContractModelForm, formset=ContractBaseFormset)
