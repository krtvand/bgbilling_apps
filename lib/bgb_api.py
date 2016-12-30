#!/usr/bin/python
# -*- coding: utf-8 -*-
import datetime
import urllib
import urllib.parse
import logging
import sys
import os
import json
import xml.etree.ElementTree as ET
import requests
import suds
from suds.client import Client
from suds.transport.http import HttpAuthenticated
import configparser
from array import *
from calendar import monthrange


class BGBilling(object):
    def __init__(self, bgb_server='http://10.60.0.10:8080', bgb_login='icticket', bgb_password='ic05102015'):
        config = configparser.ConfigParser()
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_file = project_dir + '/etc/example.conf'
        config.read(config_file)
        self.bgb_server = 'http://' + config.get('bgbilling', 'BGBILLING_HOST') + ':' + config.get('bgbilling',
                                                                                                   'BGBILLING_PORT')
        self.bgb_login = config.get('bgbilling', 'BGBILLING_LOGIN')
        self.bgb_password = config.get('bgbilling', 'BGBILLING_PASSWORD')

    def get_bgb_catalog_list(self, pid):
        """ Получение содержимого списка из справочника БГБиллинга по его ID

        :param pid: ID элемента справочника в БГБиллинге.
        Значение можно получить через клиент биллинга
        раздел "Справочники" -> "Другие"
        """
        payload = {
            'user': self.bgb_login,  # логин
            'pswd': self.bgb_password,  # пароль
            'module': 'admin',  # модуль
            'action': 'ListValues',  # действие
            'pid': pid,
        }
        r = requests.get(self.bgb_server + "/bgbilling/executer", params=payload)
        root = ET.fromstring(r.text)
        results = {}
        for values in root:
            for el in values:
                results[int(el.get('id'))] = el.get('title')
        return results

    def get_contracts_by_list_param(self, list_id, list_elem_id):
        """
        :param list_id: ID списка (например справочник типа список "Факультет/Подразделение" - с id 9)
        :param list_elem_id:ID элемента в списке (2 - Аграрный)
        :return: список из объектов типа Contract
        """
        param = {"method": "contractList",
                 "user": {"user": "icticket", "pswd": "ic05102015"},
                 "params": {"fc": -1,
                            "groupMask": 0,
                            "subContracts": False,
                            "closed": True,
                            "hidden": False,
                            "page": {"pageIndex": 0, "pageSize": 0},
                            "entityFilter": [{"type": "List",
                                              "entitySpecAttrIds": [list_elem_id], "value": list_id
                                              }]
                            }
                 }
        url = self.bgb_server + '/bgbilling/executer/json/ru.bitel.bgbilling.kernel.contract.api/ContractService'
        r = requests.post(url, json=param)
        resp = r.json()
        contract_list = []
        if resp['status'] == 'ok':
            for c in resp['data']['return']:
                if c['id']:
                    bgb_contract = BGBContract(str(c['id']))
                    contract_list.append(bgb_contract)
            return contract_list
        else:
            if resp['exception']:
                raise Exception('Error while get contract list %s' % resp['exception'])
            else:
                raise Exception('Unknown error while get contract list')

    def create_university_contract(self, fullname, department,
                                   position, it_manager, login,
                                   password, bgb_contract_template_id=28):
        """Создание договора в БГБиллинге для сотрудника университета

        :param bgb_contract_template_id: ID шаблона договора в БГБиллинге.
        Проверяется в клиенте биллинга "Договор" -> "Шаблоны"
        """
        # try:
        #     self.create_by_template(bgb_contract_template_id)  # Создание договора
        # except Exception as e:
        #     return False
        # try:
        #     self.set_fullname(self.id, fullname)  # ФИО
        # except Exception as e:
        #     # TODO Delete contract when create failed
        #     return False
        # try:
        #     self.setLstParam(self.id, pid=9, value_id=department)  # Факультет
        # except Exception as e:
        #     # TODO Delete contract when create failed
        #     return False
        # try:
        #     self.setStrParam(self.id, pid=11, value=position)  # Должность
        # except Exception as e:
        #     # TODO Delete contract when create failed
        #     return False
        # try:
        #     self.setStrParam(self.id, pid=10, value=it_manager)  # Отвественный
        # except Exception as e:
        #     # TODO Delete contract when create failed
        #     return False
        # try:
        #     self.setInetInfo(self.id, login=login, passwd=password)
        # except Exception as e:
        #     # TODO Delete contract when create failed
        #     return False
        bgb_contract = self.create_by_template(bgb_contract_template_id)  # Создание договора
        bgb_contract.set_comment(fullname=fullname)  # ФИО
        bgb_contract.set_lst_param(pid=9, value_id=department)  # Факультет
        bgb_contract.set_str_param(pid=11, value=position)  # Должность
        bgb_contract.set_str_param(pid=10, value=it_manager)  # Отвественный
        bgb_contract.set_inet_info(login=login, passwd=password)
        return bgb_contract.cid

    def create_by_template(self, template_id):
        """создание договора с использованием шаблона БГБиллинга

        :param template_id: ID шаблона
        """
        self.template_id = template_id
        payload = {
            'user': self.bgb_login,  # логин
            'pswd': self.bgb_password,  # пароль
            'module': 'contract',  # модуль
            'action': 'NewContract',  # действие
            'sub_mode': '0',  # суб договорор
            'pattern_id': template_id,
        }
        r = requests.get(self.bgb_server + "/bgbilling/executer", params=payload)
        root = ET.fromstring(str(r.text))
        #TODO remove cycle
        for child in root:
            bgb_contract = BGBContract(child.attrib['id'])
            return bgb_contract
        raise Exception('Error in creating contract by template')


class BGBContract(BGBilling):
    # номер договора
    title = ""

    def __init__(self, cid='0'):
        self.cid = cid
        super().__init__()

    def get_comment(self):
        """Получение названия договора. В нашем случае - это ФИО

        :return: string - comment of contract
        """
        payload = {
            'user': self.bgb_login,
            'pswd': self.bgb_password,
            'module': 'contract',
            'action': 'ContractInfo',
            'cid': 2949,
        }
        r = requests.post(self.bgb_server + "/bgbilling/executer", params=payload)
        """  Пример XML ответа:
            <data secret="6561AF7BA41E95F39E468ED1CA1EB14D" status="ok">
                <contract comment="Т Леонид Петрович" comments="0" date1="23.03.2016" date2=""
                del="0" fc="0" gr="2" hierarchy="independent" limit="0.00"
                mode="1" objects="0/0" status="Активен" title="0014927"/>
                <info>
                    <groups>
                        <item id="1" title="Университет"/>
                    </groups>
                    <tariff>
                        <item id="73" title="Университет 10Мб/с"/>
                    </tariff>
                    <balance mm="12" summa1="0.00" summa2="0.00" summa3="0.00"
                    summa4="0.00" summa5="0.00" summa6="0.00" summa7="0.00" yy="2016"/>
                    <modules>
                        <item id="8" package="ru.bitel.bgbilling.modules.inet.api.client"
                        status="" title="Inet"/>
                    </modules>
                    <script/>
                    <plugins/>
                </info>
            </data>
        """
        root = ET.fromstring(str(r.text))
        print (root.find('contract').get('comment'))

    def set_comment(self, fullname):
        """ФИО договора

        :param fullname:
        """
        payload = {
            'user': self.bgb_login,
            'pswd': self.bgb_password,
            'module': 'contract',
            'action': 'UpdateContractTitleAndComment',
            'cid': self.cid,
            'patid': '0',
        }
        r = requests.post(self.bgb_server + "/bgbilling/executer?comment=" + urllib.parse.quote(fullname),
                          params=payload)
        root = ET.fromstring(str(r.text))
        if root.attrib['status'] == 'error':
            print("Error in method setFio: %s" % root.text)
            raise "Error in method setFio: %s" % root.text

    def get_str_param(self, pid):
        """Получение значений параметра договора в БГБиллинге

        :param pid: ID параметра договора в БГБиллинге. Например "11" - "Должность"
        :return: string Значение параметра договора
        """
        payload = {
            'user': self.bgb_login,  # логин
            'pswd': self.bgb_password,  # пароль
            'module': 'contract',  # модуль
            'action': 'ContractParameters',  # действие
            'cid': self.cid
        }
        r = requests.post(self.bgb_server + "/bgbilling/executer", params=payload)
        """Пример XML ответа
        <data secret="1F177C3AC7AC80D417006CF3DE4AFD64" status="ok">
            <parameters>
                <parameter alwaysVisible="false" history="loopa" pid="13" pt="1" title="№ Общежития" value=""/>
                <parameter alwaysVisible="false" history="loopa" pid="14" pt="1" title="№ Комнаты" value=""/>
                <parameter alwaysVisible="false" history="loopa" pid="3" pt="9" title="Телефон абонента" value=""/>
                <parameter alwaysVisible="false" history="loopa" pid="17" pt="1" title="Email" value=""/>
                <parameter alwaysVisible="false" history="loopa" pid="4" pt="1" title="Комментарий" value=""/>
                <parameter alwaysVisible="false" history="loopa" pid="2" pt="2" title="Адрес абонента" value=""/>
                <parameter alwaysVisible="false" history="loopa" pid="9" pt="7" title="Факультет/Подразделение" value="Аграрный"/>
                <parameter alwaysVisible="false" history="loopa" pid="10" pt="1" title="Ответственный за IT по факультету" value=""/>
                <parameter alwaysVisible="false" history="loopa" pid="11" pt="1" title="Должность" value="Профессор кафедры морфологии и физиологии животных "/>
                <parameter alwaysVisible="false" history="loopa_fade" pid="18" pt="1" title="Размер абонентской платы" value=""/>
            </parameters>
            <condel pgid="0"/>
        </data>
        """
        root = ET.fromstring(str(r.text))

        return root.find('./parameters/parameter[@pid="' + str(pid) + '"]').get('value')

    # Установка параметра типа строка(contract_parameter_type_1)принимает id договора,id параметра и значение параметра
    def set_str_param(self, pid, value):
        payload = {
            'user': self.bgb_login,  # логин
            'pswd': self.bgb_password,  # пароль
            'module': 'contract',  # модуль
            'action': 'UpdateParameterType1',  # действие
            'cid': self.cid,
            'pid': pid
        }
        r = requests.post(self.bgb_server + "/bgbilling/executer?value=" +
                          urllib.parse.quote(value),
                          params=payload)
        root = ET.fromstring(str(r.text))
        if root.attrib['status'] == 'error':
            print("Error in method setStrParam: %s" % root.text)
            raise "Error in method setStrParam: %s" % root.text

    def set_lst_param(self, pid, value_id):
        """Установка параметра типа List

        :param cid: ID договора
        :param pid: ID параметра
        :param value_id: значение параметра
        """
        payload = {
            'user': self.bgb_login,  # логин
            'pswd': self.bgb_password,  # пароль
            'module': 'contract',  # модуль
            'action': 'UpdateListParam',  # действие
            'cid': self.cid,
            'pid': pid,
            'value': value_id
        }
        r = requests.get(self.bgb_server + "/bgbilling/executer", params=payload)
        root = ET.fromstring(str(r.text))
        if root.attrib['status'] == 'error':
            print("Error in method setLstParam: %s" % root.text)
            raise "Error in method setLstParam: %s" % root.text

    def get_inet_info(self):
        """Возвращает данные клиента в модуле Inet

        :return: dictionaty Пример: {   _typeId = 3   _typeTitle = "INTERNET-UNIVER"   _vlan = -1
           _uname = "220003"   _devOpts = "0"   _devState = 1   _ipResId = 0   _sessCntLimit = 1
           _cid = 11006   _dateFrom = 2016-12-13 00:00:00+03:00   _passw = "7mgbu"   _scid = 0
           _title = "220003"   _did = 3   _status = 0   _ipResSubsriptionId = 0   _id = 11802
           _deviceTitle = "Access+Accounting: IPoE-Univer"   _ifaceId = -1   _accessCode = 0
           _parentId = 0   _coid = 0   accessCodeTitle = "Ok"   comment = None
           identifierList = ""   macList = "" }
        """
        url = self.bgb_server + "/bgbilling/executer/ru.bitel.bgbilling.modules.inet.api/8/InetServService?wsdl"
        t = HttpAuthenticated(username=self.bgb_login, password=self.bgb_password)
        client = Client(url, transport=t)
        try:
            res = client.service.inetServList(self.cid)
        except suds.WebFault as e:
            print('Error in get_inet_info: %s' % (e.fault.detail.exception._cls))
            sys.exit(-1)
        else:
            return res[0]

    def set_inet_info(self, **kwargs):
        """Изменение параметров клиента в модуле Inet

        :param kwargs:
        """
        url = self.bgb_server + "/bgbilling/executer/ru.bitel.bgbilling.modules.inet.api/8/InetServService?wsdl"
        t = HttpAuthenticated(username=self.bgb_login, password=self.bgb_password)
        client = Client(url, transport=t)
        res = self.get_inet_info()
        if res != None:
            id = res._id
            uname = res._uname
            passwd = res._passw
            typeId = res._typeId
            dateFrom = res._dateFrom
            sessCntLimit = res._sessCntLimit
            if 'login' in kwargs.keys():
                uname = str(kwargs['login'])
            if 'passwd' in kwargs.keys():
                passwd = kwargs['passwd']
            serv = {
                "_cid": self.cid,
                "_id": id,
                "_passw": str(passwd),
                "_typeId": typeId,
                "_uname": uname,
                "_title": uname,
                "_dateFrom": dateFrom,
                "_sessCntLimit": sessCntLimit
            }
            try:
                res = client.service.inetServUpdate(serv, '', False, False, 0)
            except suds.WebFault as e:
                print('Error in setInetInfo: %s' % (e.fault.detail.exception._cls))
                sys.exit(-1)
            else:
                print('SetInetInfo:success')
        else:
            print('setInetInfo: Error while call getInetInfo()')
            sys.exit(-1)

    def set_status(self, statusId, dateFrom, dateTo, comment):
        url = self.bgb_server + "/bgbilling/executer/ru.bitel.bgbilling.kernel.contract.status/ContractStatusMonitorService?wsdl"
        t = HttpAuthenticated(username=self.bgb_login, password=self.bgb_password)
        client = Client(url, transport=t)

        try:
            res = client.service.changeContractStatus(self.cid, statusId, dateFrom, dateTo, comment)
        except suds.WebFault as e:
            print('Error in SetStatus: %s' % (e.fault.detail.exception._cls))
            sys.exit(-1)
        else:
            print('SetStatus:success')

    def payment_set(self, summ, comment):
        param_dict = {
            '_contractId': self.cid,
            '_date': datetime.datetime.now(),
            '_sum': summ,
            '_typeId': 4,
            '_userId': 1,
            'comment': comment
        }

        url = self.bgb_server + "/bgbilling/executer/ru.bitel.bgbilling.kernel.contract.balance/PaymentService?wsdl"
        t = HttpAuthenticated(username=self.bgb_login, password=self.bgb_password)
        client = Client(url, transport=t)
        try:
            res = client.service.paymentUpdate(param_dict)
        except suds.WebFault as e:
            print('Error in SetStatus: %s' % (e.fault.detail.exception._cls))
            sys.exit(-1)
        else:
            print('Counter_set:success')

    def get_pay_id(self):
        url = self.bgb_server + "/bgbilling/executer/ru.bitel.bgbilling.kernel.contract.balance/PaymentService?wsdl"
        t = HttpAuthenticated(username=self.bgb_login, password=self.bgb_password)
        client = Client(url, transport=t)
        try:
            res = client.service.paymentList(self.cid,'',1)
        except suds.WebFault as e:
            print('Error in SetStatus: %s' % (e.fault.detail.exception._cls))
            sys.exit(-1)
        else:
            print('GetPayId:success')
            return int(res[0][-1]["_id"])

    def payment_delete(self):
        url = self.bgb_server + "/bgbilling/executer/ru.bitel.bgbilling.kernel.contract.balance/PaymentService?wsdl"
        t = HttpAuthenticated(username=self.bgb_login, password=self.bgb_password)
        client = Client(url, transport=t)

        try:
            res = client.service.paymentDelete(self.cid, contract.get_pay_id())
        except suds.WebFault as e:
            print('Error in SetStatus: %s' % (e.fault.detail.exception._cls))
            sys.exit(-1)
        else:
            print('Counter_delete:success')


class BGBRecalculator(BGBContract):
    def __init__(self, cid):
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.contract = BGBContract(cid)
        self.tarif = int(self.contract.get_str_param(18))

    def recalculation(self):
        nowdate = datetime.datetime.now()
        day = nowdate.day - 1
        days_in_month = monthrange(nowdate.year, nowdate.month)[1]
        summ = (self.tarif * day) // days_in_month
        contract.payment_set(nowdate, summ, "Перерасчет балансного договора")
        print("recalculation: success")

    def block(self,date_begin,date_end):

        period = date_end - date_begin
        limit = monthrange(date_begin.year, date_begin.month)[1]
        if date_begin.month == 12:
            limit += monthrange(date_end.year, date_end.month)[1] + monthrange(date_end.year, date_end.month + 1)[1]
        elif date_begin.month == 11:
            limit += monthrange(date_begin.year, date_begin.month + 1)[1] + monthrange(date_end.year, date_end.month)[1]
        else:
            limit += monthrange(date_begin.year, date_begin.month + 1)[1] + monthrange(date_begin.year, date_begin.month + 2)[1]

        if period.days < 10 or period.days > limit:
            return 'Период приостановки интернета не может быть менше 10 дней или более 3-x месяцев!'
        if date_begin.day == 1 and date_end.day == monthrange(date_end.year, date_end.month)[1]:
            comment = "Приостановка договора по заявлению пользователя от " + str(date_end.date())
            self.contract.set_status(4,date_begin, date_end, comment) # ставить статус "приостановлен" и НИЧЕГО не начислять
            return (comment + " выполнена")
        else:
            if date_begin.month == date_end.month:
                summ = (self.tarif * (date_end.day - date_begin.day + 1)) // monthrange(date_end.year, date_end.month)[1]
                self.contract.payment_set(summ, "Начислили по заявлению пользователя")
                return(str(summ) + " рублей начисленo по заявлению пользователя")
            else:
                summ = (self.tarif * (monthrange(date_begin.year, date_begin.month)[1] - date_begin.day + 1)) // monthrange(date_begin.year, date_begin.month)[1]
                summ += (self.tarif * date_end.day) // monthrange(date_end.year, date_end.month)[1]
                self.contract.payment_set(summ, "Начислили по заявлению пользователя")
                return(str(summ) + " рублей начисленo по заявлению пользователя!!")
            self.contract.set_status(4,date_begin, date_end, "Приостановка договора по заявлению пользователя")
        # устанавливаем статус "приостановлен"  и начисляем sum

def sbt(title):
    param = {"method": "contractList",
             "user": {"user": "icticket", "pswd": "ic05102015"},
             "params": {
                        "title": title,
                        "fc": -1,
                        "groupMask": 0,
                        "subContracts": False,
                        "closed": True,
                        "hidden": False,
                        "page": {"pageIndex": 0, "pageSize": 0},

                        }
             }
    url = 'http://10.60.0.10:8080/bgbilling/executer/json/ru.bitel.bgbilling.kernel.contract.api/ContractService'
    r = requests.post(url, json=param)
    resp = r.json()
    return resp['data']['return'][0]['id'], resp['data']['return'][0]['comment']


if __name__ == '__main__':
    cid = 10904
    contract = BGBContract(cid)
    recalculator = BGBRecalculator(cid)
    ##################print(sbt('0016161')[1])
    ##################recalculator.block(datetime.datetime(2016,11,1),datetime.datetime(2016,12,31))
    ##################recalculator.recalculation()
    ##################contract.get_pay_id()
    ##################contract.payment_delete()
    ##################contract.set_status(4, datetime.datetime(2016,11,26),datetime.datetime(2016,11,28),'привет')
    ##################contract.payment_set(datetime.datetime.now(), 3333, "дратути!")
