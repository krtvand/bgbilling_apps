import datetime
import string
import os
import csv
from random import choice

from django.db import models
from django.utils import timezone
import xlwt

from lib.bgb_api import BGBilling


class Department(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200, verbose_name='Факультет/Подразделение')

    def create_department(self, d_id, name):
        dep = Department()
        dep.id = d_id
        dep.name = name
        dep.save()
        return dep

    def synchronize_with_bgb(self):
        BGB_CATALOG_PID = 9
        bgbilling = BGBilling()
        bgb_deps = bgbilling.get_bgb_catalog_list(BGB_CATALOG_PID)
        cur_deps = {d.id: d.name for d in Department.objects.all()}
        for d_id, name in bgb_deps.items():
            if d_id not in cur_deps:
                self.create_department(d_id, name)

    def __str__(self):
        return self.name


class Request(models.Model):
    it_manager_fullname = models.CharField(max_length=200, verbose_name='ФИО заявителя полностью')
    it_manager_email = models.EmailField(verbose_name='Email заявителя')
    it_manager_position = models.CharField(max_length=200, verbose_name='Должность заявителя')
    created_date = models.DateTimeField(auto_now=True)
    accepted = models.BooleanField(default=False)
    rejection_reason = models.CharField(max_length=200, blank=True, default='Заявка не обработана')
    department_id = models.ForeignKey(Department, on_delete=models.CASCADE,
                                      verbose_name='Факультет/Подразделение')


    def create_csv(self):
        if self.it_manager_email:
            file_name = self.it_manager_email + '_' + str(self.created_date.date()) + '.csv'
        else:
            raise Exception('Email is not defined')
        directory = os.getcwd() + '/bgb_webcontract/generated_files/'
        if not os.path.exists(directory):
            os.makedirs(directory)
        else:
            with open(directory + file_name, 'w', newline='') as f:
                wr = csv.writer(f, delimiter=';')
                header = ['ФИО', 'Должность', 'Ответственный за IT',
                          'Логин', 'Пароль']
                #wr.writerow(header)
                for contract in self.contract_set.all():
                    row = ['' for x in range(len(header))]
                    row[0] = contract.full_name
                    row[1] = contract.position
                    row[2] = contract.request_id.it_manager_fullname
                    row[3] = contract.login
                    row[4] = contract.password
                    wr.writerow(row)

    def create_excel(self):
        WIFI_SSID = 'MRSU'
        if self.it_manager_email:
            file_name = self.it_manager_email + '_' + str(self.created_date.date()) + '.xls'
        else:
            raise Exception('Email is not defined')
        directory = os.getcwd() + '/bgb_webcontract/generated_files/'
        if not os.path.exists(directory):
            os.makedirs(directory)
        else:
            wb = xlwt.Workbook()
            ws = wb.add_sheet('WiFi MRSU')
            ws.write(0, 0, 'WiFi сеть')
            ws.write(0, 1, 'ФИО')
            ws.write(0, 2, 'Должность')
            ws.write(0, 3, 'Логин')
            ws.write(0, 4, 'Пароль')
            for num, contract in enumerate(self.contract_set.all()):
                ws.write(num + 1, 0, WIFI_SSID)
                ws.write(num + 1, 1, contract.full_name)
                ws.write(num + 1, 2, contract.position)
                ws.write(num + 1, 3, contract.login)
                ws.write(num + 1, 4, contract.password)
            wb.save(directory + file_name)

    def __str__(self):
        return ' '.join([str(self.department_id), self.it_manager_fullname,])


class Contract(models.Model):
    full_name = models.CharField(max_length=200, verbose_name='ФИО без сокращений')
    position = models.CharField(max_length=200, verbose_name='Должность')
    login = models.CharField(max_length=10, blank=True, null=True)
    password = models.CharField(max_length=10, blank=True, null=True)
    request_id = models.ForeignKey(Request, on_delete=models.CASCADE, null=True, blank=True)
    bgb_cid = models.CharField(max_length=10, blank=True, null=True, verbose_name='ID в БГБиллинге')
    department_id = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return self.full_name

    def create(self, full_name, position, department_id, **kwargs):
        c = Contract()
        c.full_name = full_name
        c.position = position
        c.department_id_id = department_id
        if 'bgb_cid' in kwargs:
            c.bgb_cid = kwargs['bgb_cid']
        if 'login' in kwargs:
            c.login = kwargs['login']
        if 'password' in kwargs:
            c.password = kwargs['password']
        if 'request_id' in kwargs:
            c.request_id = kwargs['request_id']
        c.save()
        return c

    def sync_contracts_from_bgb(self, department_id):
        """Извлечение информации из БГБиллинга о существующих
        договорах в рамках одного подразделения
        в целях синхронизации данных с локальной базой данных

        Возможны случаи, когда договора создаются напрямую в Биллинге,
        а для правильного формирования логинов необходимо
        знать список использованных логинов для факультета,
        поскольку логин - есть следущее порядковое 6-ти значное число

        """
        # ID списка (например справочник типа список "Факультет/Подразделение" - с id 9)
        LIST_ID = 9
        # ID параметра договора в БГБиллинге. Например "11" - "Должность"
        POSITION_PID = 11
        bgb = BGBilling()
        bgb_contracts = bgb.get_contracts_by_list_param(list_elem_id=department_id, list_id=LIST_ID)
        local_contracts = Contract.objects.filter(department_id=department_id)
        local_cid_list = [c.bgb_cid for c in local_contracts]
        for c in bgb_contracts:
            if c.cid not in local_cid_list:
                inet_info = c.get_inet_info()
                contract = Contract().create(full_name=c.get_comment(),
                                             position=c.get_str_param(POSITION_PID),
                                             department_id=department_id,
                                             bgb_cid=c.cid,
                                             login=inet_info['_uname'],
                                             password=inet_info['_passw'])

    def create_login(self):
        """Создание логина для УЖЕ СОХРАНЕННОГО в базе контракта

         Сгенерированный логин - следующее по порядку значение
         от самого большего (как число) существующего логина
         для данного подразделения.
        :return: Значение логина
        """

        # Сохранен ли объект в базе
        if self.request_id:
            # может у него уже есть логин?
            if self.login:
                return self.login
            siblings = Contract.objects.filter(department_id=self.department_id,
                                               login__isnull=False)
            login_list = []
            if siblings:
                for c in siblings:
                    if c.login:
                        try:
                            #записываем последние 4 символа из логина
                            # (начиная с третьего символа) т.к. первые
                            # два разряда определяют подразделение
                            login_list.append(int(c.login[2:]))
                        except Exception as e:
                            pass
                d_id = self.request_id.department_id_id
                self.login = str(d_id).zfill(2) + str(sorted(login_list)[-1] + 1).zfill(4)
            else:
                d_id = self.request_id.department_id_id
                self.login = str(d_id).zfill(2) + str(1).zfill(4)
            self.save()
            return self.login
        else:
            raise Exception("Can't create login, contract should be saved in DB")

    def create_password(self):
        if not self.password:
            CHARS = string.ascii_lowercase + string.digits
            LENGTH = 6
            self.password = ''.join(choice(CHARS) for _ in range(LENGTH))
            self.save()
        return self.password
