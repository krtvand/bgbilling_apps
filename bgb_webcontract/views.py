# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse, reverse_lazy
from django.forms import inlineformset_factory
from django.forms import modelformset_factory, modelform_factory
from django.views.generic.edit import UpdateView
from django.views.generic import TemplateView, View, UpdateView, CreateView
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.core.mail import send_mail, EmailMessage
import logging
import sys
import os

from . import models
from .forms import ContractFormset, ContractModelForm, RequestForm
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
    return HttpResponseRedirect(reverse('bgb_webcontract:request_create'))


class SaveContractsMixin:
    def create_login_passwd(self, contracts, request_model):
        # Синхронизируем локальную базу с данными в БГБиллинге
        models.Contract.sync_contracts_from_bgb(request_model.department_id_id)
        res = []
        for contract in contracts:
            l = contract.create_login()
            p = contract.create_password()
            res.append((l, p))
        return res


class RequestCreateExample(SaveContractsMixin, View):
    """Создание заявки на создание договоров

    Используется 2 формы: модельная форма заявки и
    inlineformset для получения информации о ФИО и должностях.
    При сохранении договоров происходит генерация логинов и паролей
    с помощью метеда из mixin класса SaveContractsMixin
    """

    def post(self, http_req):
        request_form = RequestForm(http_req.POST)
        if request_form.is_valid():
            created_request = request_form.save(commit=False)
            contract_formset = ContractFormset(http_req.POST, instance=created_request)
            if contract_formset.is_valid():
                created_request.save()
                contracts = contract_formset.save()
                self.create_login_passwd(contracts, created_request)
                return HttpResponseRedirect(reverse('bgb_webcontract:request_create_success'))
        contract_formset = ContractFormset(http_req.POST)
        kwargs = {}
        kwargs['request_form'] = request_form
        kwargs['contract_formset'] = contract_formset
        return render(http_req, 'bgb_webcontract/request_create.html', kwargs)

    def get(self, http_req):
        models.Department().synchronize_with_bgb()
        request = models.Request()
        request_form = RequestForm(instance=request)
        contract_formset = ContractFormset()
        return render(http_req, 'bgb_webcontract/request_create.html',
                      {'request_form': request_form, 'contract_formset': contract_formset})


class RequestCreate(SaveContractsMixin, CreateView):
    """Создание заявки на создание договоров. Реализация на основе Generic CBV

    Используется 2 формы: модельная форма заявки и
    inlineformset для получения информации о ФИО и должностях.
    При сохранении договоров происходит генерация логинов и паролей
    с помощью метеда из mixin класса SaveContractsMixin
    """
    form_class = RequestForm
    success_url = reverse_lazy('bgb_webcontract:request_create_success')
    template_name = 'bgb_webcontract/request_create.html'

    def get(self, request, *args, **kwargs):
        # для внутренного машинария
        self.object = None
        # Синхронизируем список подразделений с Биллингом
        models.Department().synchronize_with_bgb()
        contract_formset = ContractFormset()
        # Форму, которая строится на базе self.formclass
        # можно не передавать в контекст, по умолчанию
        # она будет доступна в шаблоне по имени "form",
        # но для дружелюбного контекста можно переопределять ее имя
        # request_form = self.get_form(self.form_class)
        # self.render_to_response(self.get_context_data(contract_formset=contract_formset,
        #                                               request_form=request_form))
        # p.s. self.context_object_name не работает
        return self.render_to_response(self.get_context_data(contract_formset=contract_formset))

    def form_valid(self, form):
        self.object = form.save(commit=False)
        contract_formset = ContractFormset(self.request.POST, instance=self.object)
        if contract_formset.is_valid():
            self.object.save()
            contracts = contract_formset.save()
            self.create_login_passwd(contracts, self.object)
            return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        contract_formset = ContractFormset(self.request.POST)
        return self.render_to_response(self.get_context_data(contract_formset=contract_formset))

    # Эту часть CreateView делает сам, хотя в исходниках я так и не нашел как именно
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     if 'contract_formset' in kwargs:
    #         context['contract_formset'] = kwargs['contract_formset']
    #     return context


def request_update_redirect(http_req, pk):
    return HttpResponseRedirect(reverse('bgb_webcontract:request_update', kwargs={'pk': pk}))


class RequestUpdate(SaveContractsMixin, UpdateView):
    model = models.Request
    fields = ['it_manager_fullname', 'it_manager_position',
              'it_manager_email', 'department_id']
    success_url = reverse_lazy('bgb_webcontract:request_create_success')
    template_name = 'bgb_webcontract/request_update.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        contract_formset = ContractFormset(instance=self.object)
        return self.render_to_response(self.get_context_data(contract_formset=contract_formset))

    def form_valid(self, form):
        self.object = form.save(commit=False)
        contract_formset = ContractFormset(self.request.POST, instance=self.object)
        if contract_formset.is_valid():
            self.object.save()
            contracts = contract_formset.save()
            self.create_login_passwd(contracts, self.object)
            return super().form_valid(form)

    def form_invalid(self, form):
        contract_formset = ContractFormset(self.request.POST)
        return self.render_to_response(self.get_context_data(contract_formset=contract_formset))


def backend_view(request):
    new_request_list = models.Request.objects.filter(accepted=False).order_by('created_date')
    latest_request_list = models.Request.objects.filter(accepted=True).order_by('created_date')
    return render(request, 'bgb_webcontract/backend.html',
                  {'new_request_list': new_request_list,
                   'latest_request_list': latest_request_list})


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
        request_form = RequestForm()
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


def request_create_success(request):
    kwargs = {}
    return render(request, 'bgb_webcontract/request_create_success.html', kwargs)
