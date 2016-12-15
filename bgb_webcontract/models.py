import datetime
import string
import os
import csv
from random import choice

from django.db import models
from django.utils import timezone

from lib.bgb_api import BGBilling


class Department(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200, verbose_name='Факультет/Подразделение')

    def __init__(self):
        self.synchronize_with_bgb()

    def synchronize_with_bgb(self):
        BGB_CATALOG_PID = 9
        bgbilling = BGBilling()
        bgb_deps = bgbilling.get_bgb_catalog_list(BGB_CATALOG_PID)
        cur_deps = {d.id: d.name for d in self.objects.all()}
        for d in bgb_deps:
            if d not in cur_deps:
                print(d)



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
            file_name = self.it_manager_email + '.csv'
        else:
            raise Exception('Email is not defined')
        directory = os.getcwd() + '\\bgb_webcontract\generated_files\\'
        if not os.path.exists(directory):
            raise Exception('Directory is not exist')
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

    def __str__(self):
        return ' '.join([str(self.department_id), self.it_manager_fullname,])


class Contract(models.Model):
    full_name = models.CharField(max_length=200, verbose_name='ФИО без сокращений')
    position = models.CharField(max_length=200, verbose_name='Должность')
    login = models.CharField(max_length=10, blank=True, null=True)
    password = models.CharField(max_length=10, blank=True)
    request_id = models.ForeignKey(Request, on_delete=models.CASCADE)

    def __str__(self):
        return self.full_name

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
            siblings = Contract.objects.filter(request_id__department_id=self.request_id.department_id,
                                               login__isnull=False)
            login_list = []
            if siblings:
                for c in siblings:
                    if c.login:
                        login_list.append(int(c.login))
                        self.login = str(sorted(login_list)[-1] + 1)
            else:
                d_id = self.request_id.department_id_id
                self.login = str(d_id) + '0001'
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
