"""
Unittesting for mlqda app
"""
from django.test import TestCase
from django.urls import reverse

from mlqda.views import save_file

from os.path import exists


class ViewTests(TestCase):
    def test_index(self):
        response = self.client.get(reverse('mlqda:index'))
        self.assertEqual(response.status_code, 200)

    def test_about(self):
        response = self.client.get(reverse('mlqda:about'))
        self.assertEqual(response.status_code, 200)

    def test_contact(self):
        response = self.client.get(reverse('mlqda:contact'))
        self.assertEqual(response.status_code, 200)
        
    def test_results(self):
        response = self.client.get(reverse('mlqda:analyser-results'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Connection')
        self.assertEqual(len(response.context['topics']), 2)
        
    def test_redirect(self):
        response = self.client.get(reverse('mlqda:analyser-redirect'))
        self.assertEqual(response.status_code, 200)

    def test_get_analyser_start(self):
        response = self.client.get(reverse('mlqda:analyser-start'))
        self.assertEqual(response.status_code, 200)
        
