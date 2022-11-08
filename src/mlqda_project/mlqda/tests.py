"""
Unittesting for mlqda app
"""
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

import os
import json
from zipfile import ZipFile

from mlqda.topic_modelling import TopicModelling
from mlqda.models import FileCollector, FileContainer


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

    # def test_results(self):
    #     """
    #     Testing if results page loads correctly
    #     """
    #     response = self.client.get(reverse('mlqda:analyser-results'))
    #     self.assertEqual(response.status_code, 200)
    #     self.assertContains(response, 'Connection')
    #     self.assertEqual(len(response.context['topics']), 2)

    def test_redirect(self):
        """
        Testing if redirect page loads correctly
        """
        collector = FileCollector(first_name="test_files.txt")
        collector.save()
        test_path = os.path.relpath(settings.TEST_DIR, start=os.curdir)

        for file in os.listdir(test_path):
            file_path = os.path.join(test_path, file)
            if os.path.isfile(file_path):
                with open(file_path, 'r') as f:
                    test_content = f.read().encode('utf-8')
                    test_doc = SimpleUploadedFile(file_path, test_content)
                    current_file = FileContainer(file=test_doc, first_name=collector)
                    current_file.save()

        response = self.client.get(reverse('mlqda:analyser-redirect',
                                           kwargs={'collector_id': collector.collector_id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The script identified 5 topics in your files.")

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


class TopicModellingTests(TestCase):
    """
    Class to collect test regarding the topic modelling script
    """

    def get_test_files(self):
        test_path = os.path.relpath(settings.TEST_DIR, start=os.curdir)
        test_datafiles = []
        for file in os.listdir(test_path):
            file_path = os.path.join(test_path, file)
            if os.path.isfile(file_path):
                with open(file_path, 'r') as f:
                    text = f.read().replace('\n', '')
                    test_datafiles.append(text)
        return test_datafiles

    def test_constructor(self):
        test_files = self.get_test_files()
        test_tm = TopicModelling(test_files, 1)
        print(test_tm.datafiles[1])

        self.assertTrue('overtakes' in test_tm.datafiles[1])
        self.assertEqual(len(test_tm.datafiles), len(test_files))
        self.assertTrue('marketing' in test_tm.datafiles[1])

    def test_preprocess(self):
        test_files = self.get_test_files()
        test_tm = TopicModelling(test_files, 1)
        test_tm.process_files()

        self.assertEqual(len(test_tm.processed_files), len(test_files))
        self.assertTrue('overtakes' in test_tm.datafiles[1])
        self.assertTrue('overtake' in test_tm.processed_files[1])
        self.assertFalse('overtakes' in test_tm.processed_files[1])
        self.assertTrue('the' in test_tm.datafiles[1])
        self.assertFalse('the' in test_tm.processed_files[1])

    def test_creating_helper_datastructures(self):
        test_files = self.get_test_files()
        test_tm = TopicModelling(test_files, 1)
        test_tm.process_files()
        test_tm.create_helper_datastructures()

        self.assertEqual(len(test_tm.structures['bigram_texts']), len(test_files))
        self.assertEqual(len(test_tm.structures['trigram_texts']), len(test_files))
        self.assertTrue(len(test_tm.structures['id2word']) > len(test_tm.structures['corpus']))
        self.assertEqual(len(test_tm.structures['corpus']), len(test_files))

    def test_tf_idf_removal(self):
        test_files = self.get_test_files()
        test_tm = TopicModelling(test_files, 1)
        test_tm.process_files()
        test_tm.create_helper_datastructures()

        old_corpus_lengths = [len(corpora) for corpora in test_tm.structures['corpus']]
        old_len = len(test_tm.structures['corpus'][1])

        test_tm.tf_idf_removal()
        new_corpus_lengths = [len(corpora) for corpora in test_tm.structures['corpus']]

        self.assertTrue(len(test_tm.structures['corpus'][1]) < old_len)
        self.assertNotEqual(old_corpus_lengths, new_corpus_lengths)

    def test_run_lda(self):
        test_files = self.get_test_files()
        test_tm = TopicModelling(test_files, 1)
        test_tm.process_files()
        test_tm.create_helper_datastructures()
        test_tm.tf_idf_removal()
        test_model = test_tm.run_lda(3)

        self.assertEqual(len(test_model.get_topics()), 3)

    def test_dynamic_lda(self):
        test_files = self.get_test_files()
        test_tm = TopicModelling(test_files, 1)
        test_tm.process_files()
        test_tm.create_helper_datastructures()
        test_tm.tf_idf_removal()
        test_tm.dynamic_lda()

        self.assertEqual(len(test_tm.lda_model.get_topics()), 5)

    def test_compile_results(self):
        test_files = self.get_test_files()

        collector = FileCollector(first_name="test_files.txt")
        collector.save()
        for file in test_files:
            current_file = FileContainer.objects.create(file=file, first_name=collector)
            current_file.save()

        test_tm = TopicModelling(test_files, collector.collector_id)
        test_tm.process_files()
        test_tm.create_helper_datastructures()
        test_tm.tf_idf_removal()
        test_tm.dynamic_lda()
        test_tm.compile_results()

        test_result_path = os.path.join(os.path.relpath(settings.MEDIA_ROOT, start=os.curdir),
                                        str(test_tm.collector_id)+str('_results.json'))
        test_zip_path = os.path.join(os.path.relpath(settings.MEDIA_ROOT,
                                                     start=os.curdir),
                                     test_tm.zip_name)

        with open(test_result_path, 'r') as test_result_file:
            test_result = json.load(test_result_file)

        with ZipFile(test_zip_path, 'r') as test_zip_results:
            zip_collector_id = str(test_tm.collector_id)
            zipped_test_result = test_zip_results.read(zip_collector_id+str('_results.json'))
            unzipped_test_result = json.loads(zipped_test_result.decode("utf-8"))

        self.assertEqual(len(test_result), len(test_tm.lda_model.get_topics()))
        self.assertEqual(len(unzipped_test_result), len(test_tm.lda_model.get_topics()))
        self.assertEqual(len(test_result), len(unzipped_test_result))
        os.remove(test_result_path)
        os.remove(test_zip_path)
