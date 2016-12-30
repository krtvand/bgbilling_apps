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
import string
from datetime import datetime, date, time

from .models import Request
from lib.bgb_api import BGBContract, BGBRecalculator, sbt


def recalculate_view(request):
	RequestForm = modelform_factory(Request, fields=('fullname',
                                                      'contract_number',
                                                      'date_begin',
                                                      'date_end',
                                                      'comment',
                                                    )
									)
	if request.method == 'POST':
		dicti = request.POST.copy()
		request_form = RequestForm(dicti)
		if request_form.is_valid():
			title = dicti.get('contract_number')
			date_begin = datetime.strptime(dicti.get('date_begin'), "%Y-%m-%d")
			date_end = datetime.strptime(dicti.get('date_end'), "%Y-%m-%d")
			res = sbt(title)
			dicti.update(fullname=res[1])
			request_form = RequestForm(dicti)
			recalculate = BGBRecalculator(res[0])
			message = recalculate.block(date_begin, date_end) + " " + res[1]
			recalculate_request = request_form.save()
			request_form = RequestForm()
			return render(request, 'recalculation/recalculate.html',
                  {'request_form' : request_form, 'message' : message})
	
		else:
			
			return render(request, 'recalculation/recalculate.html',
                  {'request_form' : request_form, 'message': 'Проверьте правильность введенных данных!'})
			
    		
       
	else:
		request_form = RequestForm()

	
		
		return render(request, 'recalculation/recalculate.html',
                  {'request_form' : request_form})
