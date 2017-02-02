from django.test.utils import setup_test_environment
from django.test import Client, TestCase
from django.core.urlresolvers import reverse

from .models import Request, Department, Contract


class RequestViewTests(TestCase):
    def test_request_view(self):
        response = self.client.get(reverse('bgb_webcontract:request_create'))
        self.assertEqual(response.status_code, 200)


class BackendViewTests(TestCase):
    def test_backend_view(self):
        response = self.client.get(reverse('bgb_webcontract:backend'))
        self.assertEqual(response.status_code, 200)

class RequestFormTest(TestCase):
    contract_set_managementform = {'contract_set-TOTAL_FORMS': 1,
                                        'contract_set-INITIAL_FORMS': 0,
                                        'contract_set-MIN_NUM_FORMS': 0,
                                        'contract_set-MAX_NUM_FORMS': 1000}


class RequestCreateTest(RequestFormTest):
    def setUp(self):
        dep = Department(name='test_dep', id=1)
        dep.save()
        self.request = {'it_manager_fullname': 'ФИО Тест',
                        'it_manager_position': 'Должность тест',
                        'it_manager_email': 'test@email.ru',
                        'department_id': dep.id}
        self.contract = {'form-0-full_name': 'test fullname',
                         'form-0-position': 'test position'}
        self.data = {}
        self.data.update(self.request)
        self.data.update(self.contract)
        self.data.update(self.contract_set_managementform)
        self.cur_req_count = Request.objects.count()

    def test_create_valid_request(self):
        response = self.client.post(reverse('bgb_webcontract:request_create'), data=self.data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('bgb_webcontract:request_create_success'))
        self.assertEqual(Request.objects.count(), self.cur_req_count + 1)

class RequestUpdateTest(RequestFormTest):
    def setUp(self):
        self.department = Department(id=1, name='Биологический')
        self.department.save()
        self.request = Request(it_manager_fullname='ФИО заявителя полностью',
                          it_manager_email='test@email.com',
                          it_manager_position='Должность заявителя',
                          department_id=self.department)
        self.request.save()
        self.assertEqual(self.request.id, 1)
        contract = Contract(full_name='ФИО без сокращений',
                            position='Должность',
                            request_id=self.request,
                            department_id=self.department)
        contract.save()
        self.assertEqual(self.request.contract_set.count(), 1)

    def test_fullname_field_update(self):
        """ Тестирование изменения заявки через форму
        """
        update_url = reverse('bgb_webcontract:request_update', kwargs={'pk': self.request.id})
        self.assertTrue(update_url)

        # GET the form
        r = self.client.get(update_url)

        # retrieve form data as dict
        form = r.context['form']
        # contract_formset = r.context['contract_formset']
        data = form.initial  # form is unbound but contains data
        # contract_formset_data = contract_formset.initial

        # manipulate some data
        data['it_manager_fullname'] = 'updated name surname'

        # POST to the form
        data.update(self.contract_set_managementform)
        r = self.client.post(update_url, data)

        # retrieve again
        r = self.client.get(update_url)
        self.assertEqual(r.context['form'].initial['it_manager_fullname'], 'updated name surname')
