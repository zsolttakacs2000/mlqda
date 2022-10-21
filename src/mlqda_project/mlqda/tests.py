"""
Unittesting for mlqda app
"""
from django.test import TestCase
from django.urls import reverse


class ViewTests(TestCase):
    """
    Class to collect basic view unit test definitions
    @param TestCase: inheriting form django.test.TesCase
    """
    def test_index(self):
        """
        Testing if index page loads correctly
        """
        response = self.client.get(reverse('mlqda:index'))
        self.assertEqual(response.status_code, 200)

    def test_about(self):
        """
        Testing if about page loads correctly
        """
        response = self.client.get(reverse('mlqda:about'))
        self.assertEqual(response.status_code, 200)

    def test_contact(self):
        """
        Testing if contact page loads correctly
        """
        response = self.client.get(reverse('mlqda:contact'))
        self.assertEqual(response.status_code, 200)

    def test_results(self):
        """
        Testing if results page loads correctly
        """
        response = self.client.get(reverse('mlqda:analyser-results'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Connection')
        self.assertEqual(len(response.context['topics']), 2)

    def test_redirect(self):
        """
        Testing if redirect page loads correctly
        """
        response = self.client.get(reverse('mlqda:analyser-redirect'))
        self.assertEqual(response.status_code, 200)

    def test_get_analyser_start(self):
        """
        Testing of analyser starting page loads correctly
        """
        response = self.client.get(reverse('mlqda:analyser-start'))
        self.assertEqual(response.status_code, 200)
