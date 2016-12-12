#!/usr/bin/python
# -*- coding: utf-8 -*-
#print("Content-Type: text/plain\r\n")

import requests
import urllib
import urllib.parse
import csv
import suds
import logging
import os
import sys
import xml.etree.ElementTree as ET
from suds.client import Client
from suds.transport.http import HttpAuthenticated


#logging.basicConfig(level=logging.DEBUG)


class BGBContract(object):


    # id договора
    id = 0
    # номер договора
    title = ""

    def __init__(self, bgb_server='http://10.60.0.10:8080', bgb_login='icticket', bgb_password='ic05102015'):
        self.bgb_server = bgb_server
        self.bgb_login = bgb_login
        self.bgb_password = bgb_password

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

        self.create_by_template(bgb_contract_template_id)  # Создание договора
        self.set_fullname(cid=self.id, fullname=fullname)  # ФИО
        self.setLstParam(cid=self.id, pid=9, value_id=department)  # Факультет
        self.setStrParam(cid=self.id, pid=11, value=position)  # Должность
        self.setStrParam(cid=self.id, pid=10, value=it_manager)  # Отвественный
        self.setInetInfo(cid=self.id, login=login, passwd=password)

    def create_by_template(self,template_id):
        """создание договора с использованием шаблона БГБиллинга

        :param template_id: ID шаблона
        """
        self.template_id=template_id
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
        for child in root:
            self.id = child.attrib['id']
            self.title = child.attrib['title']

    def set_fullname(self, cid, fullname):
        """ФИО договора

        :param cid:
        :param fullname:
        """
        payload = {
            'user': self.bgb_login,
            'pswd': self.bgb_password,
            'module': 'contract',
            'action': 'UpdateContractTitleAndComment',
            'cid': cid,
            'patid': '0',
            }
        r = requests.post(self.bgb_server + "/bgbilling/executer?comment=" + urllib.parse.quote(fullname),
            params=payload)
        root = ET.fromstring(str(r.text))
        if root.attrib['status'] == 'error':
            print("Error in method setFio: %s" % root.text)
            raise "Error in method setFio: %s" % root.text


    #Установка параметра типа строка(contract_parameter_type_1)принимает id договора,id параметра и значение параметра
    def setStrParam(self, cid, pid, value):
        payload = {
            'user': self.bgb_login,#логин
            'pswd': self.bgb_password,#пароль
            'module': 'contract',#модуль
            'action': 'UpdateParameterType1',#действие
            'cid': cid,
            'pid': pid
            }
        r=requests.post(self.bgb_server + "/bgbilling/executer?value=" +
            urllib.parse.quote(value),
            params=payload)
        root = ET.fromstring(str(r.text))
        if root.attrib['status'] == 'error':
            print("Error in method setStrParam: %s" % root.text)
            raise "Error in method setStrParam: %s" % root.text

    def setLstParam(self, cid, pid, value_id):
        """Установка параметра типа List

        :param cid: ID договора
        :param pid: ID параметра
        :param value_id: значение параметра
        """
        print(pid, value_id)
        payload = {
            'user': self.bgb_login,#логин
            'pswd': self.bgb_password,#пароль
            'module': 'contract',#модуль
            'action': 'UpdateListParam',#действие
            'cid': cid,
            'pid': pid,
            'value': value_id
            }
        r = requests.get(self.bgb_server + "/bgbilling/executer", params=payload)
        root = ET.fromstring(str(r.text))
        if root.attrib['status'] == 'error':
            print("Error in method setLstParam: %s" % root.text)
            raise "Error in method setLstParam: %s" % root.text

    def getInetInfo(self,cid):
        """Возвращает данные клиента в модуле Inet

        :param cid:
        :return:
        """
        url = self.bgb_server + "/bgbilling/executer/ru.bitel.bgbilling.modules.inet.api/8/InetServService?wsdl"
        t = HttpAuthenticated(username=self.bgb_login, password=self.bgb_password)
        client = Client(url, transport=t)
        try:
            res=client.service.inetServList(cid)
        except suds.WebFault as e:
            print('Error in getInetInfo: %s' % (e.fault.detail.exception._cls))
            sys.exit(-1)
        else:
            return res[0]

    def setInetInfo(self, cid, **kwargs):
        """Изменение параметров клиента в модуле Inet

        :param cid:
        :param kwargs:
        """
        url = self.bgb_server+"/bgbilling/executer/ru.bitel.bgbilling.modules.inet.api/8/InetServService?wsdl"
        t = HttpAuthenticated(username=self.bgb_login, password=self.bgb_password)
        client = Client(url, transport=t)
        res = self.getInetInfo(cid)
        if res!=None:
            id=res._id
            uname=res._uname
            passwd=res._passw
            typeId=res._typeId
            dateFrom = res._dateFrom
            sessCntLimit = res._sessCntLimit
            if 'login' in kwargs.keys():
                uname=str(kwargs['login'])
            if 'passwd' in kwargs.keys():
                passwd=kwargs['passwd']
            serv={
                "_cid": cid,
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
    directory = os.getcwd()
    with open(directory + '\\dep-study@adm.mrsu.ru.csv', 'r') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=';')
        for row in spamreader:
            if row[1]!="":
                print(row[0],row[1],row[2],row[3],row[4])
                contract.create_university_contract(28)
