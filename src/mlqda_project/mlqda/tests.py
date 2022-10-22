"""
Unittesting for mlqda app
"""
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile


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
        self.assertContains(response,
                            'Welcome to the Machine Learning Qualitative Data Analyzer')

    def test_about(self):
        """
        Testing if about page loads correctly
        """
        response = self.client.get(reverse('mlqda:about'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
                            'This app is a container for a code to enable')

    def test_contact(self):
        """
        Testing if contact page loads correctly
        """
        response = self.client.get(reverse('mlqda:contact'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
                            'This web app and the underlying topic modelling')

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
        self.assertContains(response,
                            'Your files are being processed currently')

    def test_get_analyser_start(self):
        """
        Testing of analyser starting page loads correctly
        """
        response = self.client.get(reverse('mlqda:analyser-start'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
                            'Please upload your files to the')

    def test_post_analyser_start(self):
        test_content = "this is the test content"
        test_doc = SimpleUploadedFile('test_text.txt', test_content.encode(), 'text/plain')
        response = self.client.post(reverse('mlqda:analyser-start'), {'file': test_doc})
        self.assertEqual(response.status_code, 302)

    def test_faq(self):
        """
        Testing if about page loads correctly
        """
        response = self.client.get(reverse('mlqda:faq'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
                            'How do I remove these unnecesarry texts?')
