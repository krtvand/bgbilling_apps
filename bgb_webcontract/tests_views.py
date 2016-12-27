from django.test.utils import setup_test_environment
from django.test import Client, TestCase
from django.core.urlresolvers import reverse


class RequestViewTests(TestCase):
    def test_request_view(self):
        response = self.client.get(reverse('bgb_webcontract:request'))
        self.assertEqual(response.status_code, 200)


class BackendViewTests(TestCase):
    def test_backend_view(self):
        response = self.client.get(reverse('bgb_webcontract:backend'))
        self.assertEqual(response.status_code, 200)