import datetime
import string
import os
import csv
from random import choice
from datetime import datetime, date, time
from django.db import models
import xlwt

class Request(models.Model):
	fullname = models.CharField(max_length=100, verbose_name='ФИО заявителя полностью', blank=True, null=True)
	contract_number = models.CharField(max_length=20,verbose_name='Номер договора')
	date_begin = models.DateTimeField(verbose_name='Дата начала (гггг-мм-дд)')
	date_end = models.DateTimeField(verbose_name='Дата окончания (гггг-мм-дд)')
	created_date = models.DateTimeField(auto_now=True, verbose_name='Дата создания заявки')
	comment = models.CharField(max_length=100, verbose_name='Комментарий оператора',blank = True, null = True, default = "По заявлению от " + str(datetime.now().date()))


