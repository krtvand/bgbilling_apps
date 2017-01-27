from django.test.utils import setup_test_environment
from django.test import Client, TestCase
from django.core.urlresolvers import reverse

from .models import Request, Department


class RequestViewTests(TestCase):
    def test_request_view(self):
        response = self.client.get(reverse('bgb_webcontract:request'))
        self.assertEqual(response.status_code, 200)


class BackendViewTests(TestCase):
    def test_backend_view(self):
        response = self.client.get(reverse('bgb_webcontract:backend'))
        self.assertEqual(response.status_code, 200)


class RequestCreateTest(TestCase):
    def setUp(self):
        dep = Department(name='test_dep')
        dep.save()
        self.request = {'it_manager_fullname': 'ФИО Тест',
                        'it_manager_position': 'Должность тест',
                        'it_manager_email': 'test@email.ru',
                        'department_id': dep.id}
        self.contract = {'form-0-full_name': 'test fullname',
                         'form-0-position': 'test position'}
        self.managementform = {'form-TOTAL_FORMS': 1,
                               'form-INITIAL_FORMS': 0,
                               'form-MIN_NUM_FORMS': 0,
                               'form-MAX_NUM_FORMS': 1000}
        self.data = {}
        self.data.update(self.request)
        self.data.update(self.contract)
        self.data.update(self.managementform)
        self.cur_req_count = Request.objects.count()

    def test_create_request(self):
        response = self.client.post(reverse('bgb_webcontract:request_create_class'), data=self.data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('bgb_webcontract:request_create_success'))
        self.assertEqual(Request.objects.count(), self.cur_req_count + 1)
