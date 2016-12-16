from django.core.urlresolvers import reverse
from django.forms import inlineformset_factory
from django.forms import modelformset_factory, modelform_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views import generic

from .models import Request, Contract, Department
from lib.bgb_api import BGBContract

def index_view(request):
    return HttpResponseRedirect(reverse('bgb_webcontract:request'))

def backend_view(request):
    new_request_list = Request.objects.filter(accepted=False).order_by('created_date')
    latest_request_list = Request.objects.filter(accepted=True).order_by('created_date')
    print(new_request_list)
    return render(request, 'bgb_webcontract/backend.html',
                  {'new_request_list': new_request_list,
                   'latest_request_list': latest_request_list})


def request_view(request):
    ContractFormset = modelformset_factory(Contract, fields=('full_name', 'position'))
    RequestForm = modelform_factory(Request, fields=('it_manager_fullname',
                                                          'it_manager_position',
                                                          'it_manager_email',
                                                          'department_id'))
    if request.method == 'POST':
        request_form = RequestForm(request.POST)
        contract_formset = ContractFormset(request.POST)
        if contract_formset.is_valid() and request_form.is_valid():
            it_manager_request = request_form.save()
            contracts = contract_formset.save(commit=False)
            for contract in contracts:
                it_manager_request.contract_set.add(contract, bulk=False)
                contract.create_login()
                contract.create_password()
            return HttpResponse('Спасибо за использование нашей системы. '
                                'Введенные данные в ближайшее время '
                                'будут проверены администратором, '
                                'после чего на указанный e-mail '
                                'будет отправлен список логинов и паролей')
    else:
        dep = Department()
        dep.synchronize_with_bgb()
        contract_formset = ContractFormset(queryset=Contract.objects.none())
        request_form = RequestForm()
    return render(request, 'bgb_webcontract/request.html',
                  {'request_form' : request_form, 'contract_formset': contract_formset})

def request_detail_view(request, request_id):
    req = get_object_or_404(Request, pk=request_id)
    ContractInlineFormset = inlineformset_factory(Request, Contract, extra=0,
                                                  fields=('full_name', 'position'))
    RequestForm = modelform_factory(Request, fields=('it_manager_fullname',
                                                     'it_manager_position',
                                                     'it_manager_email',
                                                     'department_id'))
    if request.method == 'POST':
        request_form = RequestForm(request.POST, instance=req)
        contract_formset = ContractInlineFormset(request.POST, instance=req)
        if contract_formset.is_valid() and request_form.is_valid():
            request_form.save()
            contracts = contract_formset.save()
            for contract in contracts:
                contract.create_login()
                contract.create_password()
            action_info = 'Изменения сохранены'
            return render(request, 'bgb_webcontract/request_detail.html',
                          {'contract_formset': contract_formset, 
                           'request_form': request_form,
                           'request': req,
                           'action_info': action_info})
    else:
        request_form = RequestForm(instance=req)
        contract_formset = ContractInlineFormset(instance=req)
    return render(request, 'bgb_webcontract/request_detail.html',
                              {'contract_formset': contract_formset,
                               'request_form': request_form, 'request': req})

def request_detail_backend_view(request, request_id):
    req = get_object_or_404(Request, pk=request_id)
    ContractInlineFormset = inlineformset_factory(Request, Contract, extra = 0,
                                                  fields=('full_name', 'position', 'login', 'password'))
    RequestForm = modelform_factory(Request, fields=('it_manager_fullname',
                                                     'it_manager_position',
                                                     'it_manager_email',
                                                     'department_id',
                                                     'rejection_reason'))
    if request.method == 'POST':
        request_form = RequestForm(request.POST, instance=req)
        print(request.POST)
        contract_formset = ContractInlineFormset(request.POST, instance=req)
        if contract_formset.is_valid() and request_form.is_valid():
            if 'save_to_billing' in request.POST:
                req.accepted = True
                req.rejection_reason = ''
                # Сохраняем изменения
                req = request_form.save()
                contract_formset.save()
                # Получаем все договора для данной заявки (а не только из POST)
                contracts = Request.objects.get(pk=request_id).contract_set.all()
                # Формируем csv для отправки данных заявителю
                req.create_csv()
                for c in contracts:
                    bgb_contract = BGBContract()
                    # Создаем договор в БГБиллинге
                    bgb_contract.create_university_contract(fullname=c.full_name,
                                                            department=req.department_id.id,
                                                            it_manager=' '.join([req.it_manager_fullname,
                                                                                 req.it_manager_position,
                                                                                 req.it_manager_email]),
                                                            position=c.position,
                                                            login=c.login,
                                                            password=c.password,)
                request_form = RequestForm(instance=req)
                contract_formset = ContractInlineFormset(instance=req)
                action_info = "Данные сохранены и отправлены в БГБиллинг"
                return render(request, 'bgb_webcontract/request_detail_backend.html',
                              {'contract_formset': contract_formset,
                               'request_form': request_form,
                               'request': req,
                               'action_info': action_info})
            elif 'save' in request.POST:
                contract_formset.save()
                request_form.save()
                action_info = 'Изменения сохранены'
                request_form = RequestForm(instance=req)
                contract_formset = ContractInlineFormset(instance=req)
                return render(request, 'bgb_webcontract/request_detail_backend.html',
                              {'contract_formset': contract_formset,
                               'request_form': request_form,
                               'request': req,
                               'action_info': action_info})
            elif 'generate_login_pasw' in request.POST:
                # Сохраняем данные из POST
                contract_formset.save()
                # Получаем все договора для данной заявки
                contracts = Request.objects.get(pk=request_id).contract_set.all()
                action_info = 'Отсутствуют договора для генерации логинов и паролей'
                for contract in contracts:
                    contract.create_login()
                    contract.create_password()
                    if contract.login:
                        action_info = 'Логины и пароли успешно сгенерированы'
                    else:
                        action_info = 'При генерации логинов и паролей возникла ошибка'
                # Будем отрисовывать формы с измененными данными
                request_form = RequestForm(instance=req)
                contract_formset = ContractInlineFormset(instance=req)
                return render(request, 'bgb_webcontract/request_detail_backend.html',
                              {'contract_formset': contract_formset,
                               'request_form': request_form,
                               'request': req,
                               'action_info': action_info})
    else:
        request_form = RequestForm(instance=req)
        contract_formset = ContractInlineFormset(instance=req)
    return render(request, 'bgb_webcontract/request_detail_backend.html',
                  {'contract_formset': contract_formset, 'request_form': request_form, 'request': req})
