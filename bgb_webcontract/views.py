from django.shortcuts import render, get_object_or_404, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views import generic
from django.utils import timezone
from django.forms import inlineformset_factory
from django.forms import modelformset_factory, modelform_factory

from .models import Choice, Question, Request, Contract, Department

class IndexView(generic.ListView):
    template_name = 'bgb_webcontract/index.html'
    context_object_name = 'latest_question_list'

    def get_queryset(self):
        """
        Return the last five published questions (not including those set to be
        published in the future).
        """
        return Question.objects.filter(
            pub_date__lte=timezone.now()
        ).order_by('-pub_date')[:5]

def backend_view(request):
    new_request_list = Request.objects.filter(accepted=False).order_by('created_date')
    latest_request_list = Request.objects.filter(accepted=True).order_by('created_date')
    return render(request, 'bgb_webcontract/backend.html',
                  {'new_request_list': new_request_list,
                   'latest_request_list': latest_request_list})

class DetailView(generic.DetailView):
    model = Question
    template_name = 'bgb_webcontract/detail.html'

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())

class ResultsView(generic.DetailView):
    model = Question
    template_name = 'bgb_webcontract/results.html'

def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(request, 'bgb_webcontract/detail.html', {
            'question': question,
            'error_message': "You didn't select a choice.",
        })
    else:
        selected_choice.votes += 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('bgb_webcontract:results', args=(question.id,)))

def request_exists_view(request, request_id):
    try:
        it_manager_request = Request.objects.get(pk=request_id)
    except (KeyError):
        return render(request, 'bgb_webcontract/request_detail.html',
                      {'request_id': request_id,
                       'error_message': 'This request id does nor exist'})
    else:
        contarct_list = it_manager_request.contract_set.all()
        return render(request, 'bgb_webcontract/request_detail.html',
                      {'request_id': request_id,
                       'it_manager_fullname': it_manager_request.it_manager_fullname,
                       'it_manager_position': it_manager_request.it_manager_position,
                       'it_manager_email': it_manager_request.it_manager_email,
                       'created_date': it_manager_request.created_date,
                       'contract_list': contarct_list})

def request_view(request):
    ContractFormset = modelformset_factory(Contract, fields=('full_name', 'position'))
    RequestForm = modelform_factory(Request, fields=('it_manager_fullname',
                                                          'it_manager_position',
                                                          'it_manager_email',
                                                          'department_id'))
    if request.method == 'POST':
        request_form = RequestForm(request.POST)
        contract_formset = ContractFormset(request.POST)
        if contract_formset.is_valid() and request_form.is_valid():
            it_manager_request = request_form.save()
            contracts = contract_formset.save(commit=False)
            for contract in contracts:
                it_manager_request.contract_set.add(contract, bulk=False)
                contract.create_login()
                contract.create_password()
            return HttpResponseRedirect(reverse('bgb_webcontract:thanks'))
    else:
        contract_formset = ContractFormset(queryset=Contract.objects.none())
        request_form = RequestForm()
    return render(request, 'bgb_webcontract/request.html',
                  {'request_form' : request_form, 'contract_formset': contract_formset})

def request_detail_view(request, request_id):
    req = get_object_or_404(Request, pk=request_id)
    ContractInlineFormset = inlineformset_factory(Request, Contract, extra=5,
                                                  fields=('full_name', 'position'))
    RequestForm = modelform_factory(Request, fields=('it_manager_fullname',
                                                     'it_manager_position',
                                                     'it_manager_email',
                                                     'department_id'))
    if request.method == 'POST':
        request_form = RequestForm(request.POST, instance=req)
        contract_formset = ContractInlineFormset(request.POST, instance=req)
        if contract_formset.is_valid() and request_form.is_valid():
            contract_formset.save()
            request_form.save()
            return HttpResponseRedirect(reverse('bgb_webcontract:thanks'))
    else:
        request_form = RequestForm(instance=req)
        contract_formset = ContractInlineFormset(instance=req)
    return render(request, 'bgb_webcontract/request_detail.html',
                              {'contract_formset': contract_formset, 'request_form': request_form, 'request': req})

def request_detail_backend_view(request, request_id):
    req = get_object_or_404(Request, pk=request_id)
    ContractInlineFormset = inlineformset_factory(Request, Contract, extra=0,
                                                  fields=('full_name', 'position', 'login', 'password'))
    RequestForm = modelform_factory(Request, fields=('it_manager_fullname',
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
                req.rejection_reason
                request_form.save()
                contract_formset.save()
                req.create_csv()
                return HttpResponse('Data was saved in BGBiling')
            elif 'save' in request.POST:
                contract_formset.save()
                request_form.save()
                return HttpResponse('Data saved')
    else:
        request_form = RequestForm(instance=req)
        contract_formset = ContractInlineFormset(instance=req)
    return render(request, 'bgb_webcontract/request_detail_backend.html',
                  {'contract_formset': contract_formset, 'request_form': request_form, 'request': req})

def thanks(request):
    return HttpResponse("Thanks")