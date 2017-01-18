# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.forms import inlineformset_factory
from django.forms import modelformset_factory, modelform_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.core.mail import send_mail, EmailMessage
import logging
import sys
import os

from . import models
from lib.bgb_api import BGBContract

# Зададим параметры логгирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(u'%(filename)s[LINE:%(lineno)d]# '
                              u'%(levelname)-8s [%(asctime)s]  %(message)s')
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def index_view(request):
    return HttpResponseRedirect(reverse('bgb_webcontract:request'))


def backend_view(request):
    new_request_list = models.Request.objects.filter(accepted=False).order_by('created_date')
    latest_request_list = models.Request.objects.filter(accepted=True).order_by('created_date')
    return render(request, 'bgb_webcontract/backend.html',
                  {'new_request_list': new_request_list,
                   'latest_request_list': latest_request_list})


def request_view(request):
    ContractFormset = modelformset_factory(models.Contract, fields=('full_name', 'position'))
    RequestForm = modelform_factory(models.Request, fields=('it_manager_fullname',
                                                            'it_manager_position',
                                                            'it_manager_email',
                                                            'department_id'))
    if request.method == 'POST':
        request_form = RequestForm(request.POST)
        contract_formset = ContractFormset(request.POST)
        if contract_formset.is_valid() and request_form.is_valid():
            it_manager_request = request_form.save()
            contracts = contract_formset.save(commit=False)
            # try:
            # Синхронизируем локальную базу с данными в БГБиллинге
            models.Contract.sync_contracts_from_bgb(it_manager_request.department_id_id)
            for contract in contracts:
                contract.department_id = it_manager_request.department_id
                it_manager_request.contract_set.add(contract, bulk=False)
                contract.create_login()
                contract.create_password()
            # except Exception as e:
            #    logger.critical('Error in request creating <%s>' % e)
            #    return HttpResponse('При отправке данных возникла ошибка, '
            #                        'пожалуйста, обратитель к администратору системы <%s>' % e)
            return HttpResponse('Спасибо за использование нашей системы. '
                                'Введенные данные в ближайшее время '
                                'будут проверены администратором, '
                                'после чего на указанный e-mail '
                                'будет отправлен список логинов и паролей')
    else:
        dep = models.Department()
        dep.synchronize_with_bgb()
        contract_formset = ContractFormset(queryset=models.Contract.objects.none())
        request_form = RequestForm()
    return render(request, 'bgb_webcontract/request.html',
                  {'request_form': request_form, 'contract_formset': contract_formset})


def request_detail_view(request, request_id):
    req = get_object_or_404(models.Request, pk=request_id)
    ContractInlineFormset = inlineformset_factory(models.Request, models.Contract, extra=0,
                                                  fields=('full_name', 'position'))
    RequestForm = modelform_factory(models.Request, fields=('it_manager_fullname',
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
    req = get_object_or_404(models.Request, pk=request_id)
    ContractInlineFormset = inlineformset_factory(models.Request, models.Contract, extra=0,
                                                  fields=('full_name', 'position', 'login', 'password'))
    RequestForm = modelform_factory(models.Request, fields=('it_manager_fullname',
                                                            'it_manager_position',
                                                            'it_manager_email',
                                                            'department_id',
                                                            'rejection_reason'))
    if request.method == 'POST':
        request_form = RequestForm(request.POST, instance=req)
        contract_formset = ContractInlineFormset(request.POST, instance=req)
        if contract_formset.is_valid() and request_form.is_valid():
            if 'save_to_billing' in request.POST:
                req.accepted = True
                req.rejection_reason = ''
                # Сохраняем изменения
                req = request_form.save()
                contract_formset.save()
                # Получаем все договора для данной заявки (а не только из POST)
                contracts = models.Request.objects.get(pk=request_id).contract_set.all()
                # Формируем csv для отправки данных заявителю
                try:
                    for c in contracts:
                        bgb_contract = BGBContract()
                        # Создаем договор в БГБиллинге
                        bgb_cid = bgb_contract.create_university_contract(fullname=c.full_name,
                                                                          department=req.department_id.id,
                                                                          it_manager=' '.join([req.it_manager_fullname,
                                                                                               req.it_manager_position,
                                                                                               req.it_manager_email]),
                                                                          position=c.position,
                                                                          login=c.login,
                                                                          password=c.password, )
                        if bgb_cid:
                            action_info = "Данные сохранены и отправлены в БГБиллинг"
                            c.bgb_cid = bgb_cid
                            c.save()
                        else:
                            raise Exception('Error when creating contract in BGBilling')
                except Exception as e:
                    action_info = "При сохранении данных в БГБиллинг возникла ошибка %s" % e
                request_form = RequestForm(instance=req)
                contract_formset = ContractInlineFormset(instance=req)
                return render(request, 'bgb_webcontract/request_detail_backend.html',
                              {'contract_formset': contract_formset,
                               'request_form': request_form,
                               'request': req,
                               'action_info': action_info})
            elif 'save' in request.POST:
                contracts = contract_formset.save(commit=False)
                request_form.save()
                for contract in contracts:
                    contract.department_id = req.department_id
                    req.contract_set.add(contract, bulk=False)
                    contract.create_login()
                    contract.create_password()
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
                contracts = contract_formset.save(commit=False)
                # Получаем все договора для данной заявки
                # contracts = Request.objects.get(pk=request_id).contract_set.all()
                action_info = 'Отсутствуют договора для генерации логинов и паролей'
                # Синхронизируем локальную базу с данными в БГБиллинге
                models.Contract.sync_contracts_from_bgb(req.department_id_id)
                for contract in contracts:
                    contract.department_id = req.department_id
                    req.contract_set.add(contract, bulk=False)
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
            elif 'create_excel' in request.POST:
                # Сохраняем данные из POST
                contract_formset.save()
                # Получаем все договора для данной заявки
                contracts = models.Request.objects.get(pk=request_id).contract_set.all()
                action_info = 'Отсутствуют договора для создания excel файла'
                try:
                    req.create_excel()
                    action_info = 'Excel файл успешно сгенерирован'
                except Exception as e:
                    action_info = 'При excel файла возникла ошибка %s' % e
                # Будем отрисовывать формы с измененными данными
                request_form = RequestForm(instance=req)
                contract_formset = ContractInlineFormset(instance=req)
                return render(request, 'bgb_webcontract/request_detail_backend.html',
                              {'contract_formset': contract_formset,
                               'request_form': request_form,
                               'request': req,
                               'action_info': action_info})
            elif 'sendmail' in request.POST:
                message_subject = 'Список логинов и паролей для доступа к университетской WiFI сети'
                message_body = 'Список во вложении. Если у вас остались вопросы, напишите на адрес and@mrsu.ru ' \
                               '\nС уважением, команда Центра Интернет ФГБОУ ВО МГУ им. Н.П.Огарева' \
                               '\n Телефон технической поддержки: 8 (8342) 777-250'
                email = EmailMessage(
                    message_subject,
                    message_body,
                    'billing@mrsu.ru',
                    [req.it_manager_email],
                    reply_to=['and@mrsu.ru'],
                )
                if req.generated_file:
                    if os.path.exists(req.generated_file):
                        email.attach_file(req.generated_file)
                    else:
                        action_info = 'Файл с логинами и паролями не найден'
                        return render(request, 'bgb_webcontract/request_detail_backend.html',
                                      {'contract_formset': contract_formset,
                                       'request_form': request_form,
                                       'request': req,
                                       'action_info': action_info})
                else:
                    action_info = 'Файл с логинами и паролями не сгенерирован'
                    return render(request, 'bgb_webcontract/request_detail_backend.html',
                                  {'contract_formset': contract_formset,
                                   'request_form': request_form,
                                   'request': req,
                                   'action_info': action_info})
                try:
                    email.send()
                    action_info = 'E-mail успешно отправлен'
                except Exception as e:
                    action_info = 'При отправке email возникла ошибка <%s>' % e
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


def statistics_view(request):
    """Статистика по университеским договорам

    :param request:
    :return:
    """
    errors = []
    ccount_per_dep = {}
    total_contracts = 0
    # Синхронизируем с биллингом список подразделений
    models.Department().synchronize_with_bgb()
    # Подсчитываем количество договоров по подразделениям
    for dep in models.Department.objects.all():
        try:
            models.Contract.sync_contracts_from_bgb(department_id=dep.id)
        except Exception as e:
            errors.append(e)
            pass
        models.Contract.sync_contracts_from_bgb(department_id=dep.id)
        ccount = len(models.Contract.objects.filter(department_id=dep.id))
        ccount_per_dep[dep.name] = ccount
        total_contracts += ccount
    kwargs = {'ccount_per_dep': ccount_per_dep,
              'errors': errors,
              'total_contracts': total_contracts}
    return render(request, 'bgb_webcontract/backend_statistics.html', kwargs)
