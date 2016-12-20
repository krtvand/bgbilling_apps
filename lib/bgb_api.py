#!/usr/bin/python
# -*- coding: utf-8 -*-

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


class BGBilling(object):
    def __init__(self, bgb_server='http://10.60.0.10:8080', bgb_login='icticket', bgb_password='ic05102015'):
        config = configparser.ConfigParser()
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_file = project_dir + '/etc/bgbilling_apps.conf'
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
        :return: список из контрактов-словарей типа
        {'super': False, 'personType': 0, 'id': 10964, 'dependSubList': '',
        'password': 'nsfk3ssw', 'independSub': False,
        'paramGroupId': 0, 'status': 0, 'balanceLimit': 0.0,
        'dependSub': False, 'balanceSubMode': 0, 'hidden': False,
        'balanceMode': 1, 'dateTo': None, 'dateFrom': '2016-12-08',
        'groups': 2, 'superCid': 0, 'comment': 'Мочалова Татьяна Ивановна',
        'statusTimeChange': '2016-12-08', 'titlePatternId': 0,
        'sub': False, 'title': '0016208'}
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
                    bgb_contract = BGBContract(c['id'])
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
        bgb_contract.set_fullname(fullname=fullname)  # ФИО
        bgb_contract.setLstParam(pid=9, value_id=department)  # Факультет
        bgb_contract.set_str_param(pid=11, value=position)  # Должность
        bgb_contract.set_str_param(pid=10, value=it_manager)  # Отвественный
        bgb_contract.set_inet_info(login=login, passwd=password)

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

    def __init__(self, cid=0):
        self.cid = cid
        super().__init__()

    def set_fullname(self, fullname):
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

    def setLstParam(self, pid, value_id):
        """Установка параметра типа List

        :param cid: ID договора
        :param pid: ID параметра
        :param value_id: значение параметра
        """
        print(pid, value_id)
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

        :return:
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


if __name__ == '__main__':
    contract = BGBContract()
    contract.get_contracts_by_list_param('9', '22')
    # contract.setInetInfo(cid='10965', login='qwerasdt', passwd='asdfgddgf'