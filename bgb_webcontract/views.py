from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views import generic
from django.utils import timezone
from django.forms import inlineformset_factory
from django.forms import modelformset_factory

from .models import Choice, Question, Request, Contract, Department
from .forms import RequestForm

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
        return render(request, 'bgb_webcontract/request_exists.html',
                      {'request_id': request_id,
                       'error_message': 'This request id does nor exist'})
    else:
        contarct_list = it_manager_request.contract_set.all()
        return render(request, 'bgb_webcontract/request_exists.html',
                      {'request_id': request_id,
                       'it_manager_fullname': it_manager_request.it_manager_fullname,
                       'it_manager_position': it_manager_request.it_manager_position,
                       'it_manager_email': it_manager_request.it_manager_email,
                       'created_date': it_manager_request.created_date,
                       'contract_list': contarct_list})

def request_view(request):
    ContractFormset = modelformset_factory(Contract, fields=('full_name', 'position'))
    if request.method == 'POST':
        header_form = RequestForm(request.POST)
        contract_formset = ContractFormset(request.POST)
        if contract_formset.is_valid() and header_form.is_valid():
            it_manager_request = header_form.save()
            contracts = contract_formset.save(commit=False)
            for contract in contracts:
                it_manager_request.contract_set.add(contract, bulk=False)
                contract.create_login()
                contract.create_password()
            return HttpResponseRedirect(reverse('bgb_webcontract:thanks'))
    else:
        contract_formset = ContractFormset(queryset=Contract.objects.none())
        header_form = RequestForm()
    return render(request, 'bgb_webcontract/request.html', {'header_form' : header_form, 'contract_formset': contract_formset})

def thanks(request):
    return HttpResponse("Thanks")