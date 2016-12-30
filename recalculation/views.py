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
		request_form = RequestForm(request.POST)
		
		if request_form.is_valid():
			recalculate_request = request_form.save()
			title = request.POST.get('contract_number')
			date_begin = datetime.strptime(request.POST.get('date_begin'), "%Y-%m-%d")
			date_end = datetime.strptime(request.POST.get('date_end'), "%Y-%m-%d")
			cid = sbt(title)
			recalculate = BGBRecalculator(cid)
			message = recalculate.block(date_begin, date_end)
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
