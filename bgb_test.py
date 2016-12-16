#!/usr/bin/python
# -*- coding: utf-8 -*-
print "Content-Type: text/plain\r\n"

import requests
import urllib
import csv
import suds
import logging
import elementtree.ElementTree as ET
from elementtree import SimpleXMLTreeBuilder
import datetime

ET.XMLTreeBuilder = SimpleXMLTreeBuilder.TreeBuilder

logging.basicConfig(level=logging.DEBUG)

class Contract(object):


	id=0 #id договора
	title="" # номер договора


	def __init__(self,server,login,password):
		self.server=server
		self.login=login
		self.password=password

	#создание договора
	def create(self,pattern):

		self.pattern=pattern
		payload = {
			'user': self.login,#логин
			'pswd': self.password,#пароль
			'module':'contract',#модуль
			'action':'NewContract',#действие
			'sub_mode':'0',#суб договорор
			'pattern_id':pattern,#номер шаблона(28 шаблон для служебных)
			}
		r = requests.get(self.server+"/bgbilling/executer", params=payload)
		root = ET.fromstring(str(r.text))
		for child in root:
			self.id=child.attrib['id']
			self.title=child.attrib['title']


	#ФИО договора
	def setFIO(self,cid,FIO):
		payload = {
			'user': self.login,#логин
			'pswd': self.password,#пароль
			'module':'contract',#модуль
			'action':'UpdateContractTitleAndComment',#действие
			'cid':cid,
			'patid':'0',
			}
		r=requests.post(self.server+"/bgbilling/executer?comment="+
			urllib.quote(FIO) ,
			params=payload)

		root = ET.fromstring(str(r.text))
		if root.attrib['status'] =='error':
			print "Error in method setFio: %s"%root.text


	#Установка параметра типа строка(contract_parameter_type_1)принимает id договора,id параметра и значение параметра
	def setStrParam(self,cid,pid,value):
		payload = {
			'user': self.login,#логин
			'pswd': self.password,#пароль
			'module':'contract',#модуль
			'action':'UpdateParameterType1',#действие
			'cid':cid,
			'pid':pid
			}
		r=requests.post(self.server+"/bgbilling/executer?value="+
			urllib.quote(value) ,
			params=payload)

		root = ET.fromstring(str(r.text))
		if root.attrib['status'] =='error':
			print "Error in method setStrParam: %s"%root.text



	#Установка параметра типа List
	def setLstParam(self,cid,pid,value_id):
		payload = {
			'user': self.login,#логин
			'pswd': self.password,#пароль
			'module':'contract',#модуль
			'action':'UpdateListParam',#действие
			'cid':cid,
			'pid':pid,
			'value':value_id
			}
		r=requests.get(self.server+"/bgbilling/executer", params=payload)
		root = ET.fromstring(str(r.text))
		if root.attrib['status'] =='error':
			print "Error in method setLstParam: %s"%root.text


	#Возвращает данные клиента в модуле Inet
	def getInetInfo(self,cid):
		t = suds.transport.http.HttpAuthenticated(username=self.login, password=self.password)
		wurl = self.server+"/bgbilling/executer/ru.bitel.bgbilling.modules.inet.api/8/InetServService?wsdl"
		client = suds.client.Client(wurl,transport=t)

		try:
   			res=client.service.inetServList(cid)
		except suds.WebFault, e:
			print 'Error in getInetInfo: %s'%(e.fault.detail.exception._cls)
  		else:
			return res[0]

	#Изменение параметров клиента в модуле Inet
	def setInetInfo(self,cid,**kwargs):
		t = suds.transport.http.HttpAuthenticated(username=self.login, password=self.password)
		wurl = self.server+"/bgbilling/executer/ru.bitel.bgbilling.modules.inet.api/8/InetServService?wsdl"
		client = suds.client.Client(wurl,transport=t)

		res=self.getInetInfo(cid)

		if res!=None:
			id=res._id
			uname=res._uname
			passwd=res._passw
			typeId=res._typeId

			dateFrom=res._dateFrom
			sessCntLimit=res._sessCntLimit

			if 'login' in kwargs.keys():
				uname=str(kwargs['login'])

			if 'passwd' in kwargs.keys():
				passwd=kwargs['passwd']

			serv={
				"_cid":cid,
			    "_id":id,
				"_passw":str(passwd),
				"_typeId":typeId,
				"_uname":uname,
				"_title":uname,

				"_dateFrom":dateFrom,
				"_sessCntLimit":sessCntLimit
			}
			try:
				res=client.service.inetServUpdate(serv, '', False, False, 0 )
			except suds.WebFault, e:
				print 'Error in setInetInfo: %s'%(e.fault.detail.exception._cls)
			else:
				print 'SetInetInfo:success'
		else:
			print 'setInetInfo: Error while call getInetInfo()'


	def searchInetInfo(self, login):
		t = suds.transport.http.HttpAuthenticated(username=self.login, password=self.password)
		wurl = self.server+"/bgbilling/executer/ru.bitel.bgbilling.modules.inet.api/8/InetServService?wsdl"
		client = suds.client.Client(wurl,transport=t)

		res=client.service.searchInetServ(login)

		inc = True

		if res:
			for i in res:
				if i._title == login:
					inc = False

		return inc




#---------------------------------------------------------------------------------------
#шаблон 28
#11-Должность
#10-Ответственный
#9-факультет 1 -биологический
#			 2-Агроном
#		     3-медфак
#		     5-ФЭТ
#		     6-Отдел Инт собственности
#		     7-ДКИ
#		     8-ИНК
#		     9-Геофак
#		     10-ИМЭ
#		     11-Ин.яз
#		     13-Волонтеры 2018
#		     16-Юр.Фак
#			 18-Центр развития дистанционного образования
#			 20-ФМиИТ
#			 21-ИСИ
#			 22-УМУ




contract=Contract('http://10.60.0.10:8080','icticket','ic05102015')

#Открытие файла csv
"""
with open('ur.csv', 'rb') as csvfile:
	spamreader = csv.reader(csvfile, delimiter=';')
	for row in spamreader:
		if row[1]!="":
			print row[0],row[1],row[2],row[3],row[4]
			contract.create(28)#Создание договора
			contract.setFIO(contract.id,row[0])#ФИО
			contract.setLstParam(contract.id,9,16)#Факультет
			contract.setStrParam(contract.id,11,row[1])#Должность
			contract.setStrParam(contract.id,10,row[2])#Отвественный
			contract.setInetInfo(contract.id,login=row[3],passwd=row[4])
			print contract.id,contract.title
"""

with open('umu2.csv', 'rb') as csvfile:
	spamreader = csv.reader(csvfile, delimiter=';')
	for row in spamreader:
		if row[1]!="":
			print row[0],row[1],row[2],row[3],row[4]
			if contract.searchInetInfo(row[3]):
				contract.create(28) #Создание договора
				print contract.id,contract.title
				contract.setFIO(contract.id,row[0])#ФИО
				contract.setLstParam(contract.id,9,22)#Факультет
				contract.setStrParam(contract.id,11,row[1])#Должность
				contract.setStrParam(contract.id,10,row[2])#Отвественный
				contract.setInetInfo(contract.id,login=row[3],passwd=row[4])
			else:
				print 'Error: такой логин уже существует!\n'
