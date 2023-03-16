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
from mlqda.sentiment_analyser import SentimentAnalyser
from mlqda.models import FileCollector, FileContainer
from mlqda import utils


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

    def test_topicmodelling_results(self):
        """
        Testing if redirect page loads correctly
        """
        collector = FileCollector(first_name="test_files.txt")
        collector.save()
        test_path = os.path.relpath(settings.TEST_DIR, start=os.curdir)

        for file in os.listdir(test_path):
            file_path = os.path.join(test_path, file)
            if os.path.isfile(file_path) and file_path.endswith(".txt"):
                with open(file_path, 'r') as f:
                    test_content = f.read().encode('utf-8')
                    test_doc = SimpleUploadedFile(file_path, test_content)
                    current_file = FileContainer(file=test_doc, first_name=collector)
                    current_file.save()

        response = self.client.get(reverse('mlqda:topic-modelling-results',
                                           kwargs={'collector_id': collector.collector_id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The script identified")

    def test_get_topicmodelling_start(self):
        """
        Testing of analyser starting page loads correctly
        """
        response = self.client.get(reverse('mlqda:topic-modelling-start'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
                            'Please upload your files to the')

    def test_post_topicmodelling_start(self):
        test_content = "this is the test content"
        test_doc = SimpleUploadedFile('test_text.txt', test_content.encode(), 'text/plain')
        response = self.client.post(reverse('mlqda:topic-modelling-start'), {'file': test_doc})
        self.assertEqual(response.status_code, 302)

    def test_faq(self):
        """
        Testing if faq page loads correctly
        """
        response = self.client.get(reverse('mlqda:faq'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
                            'How do I remove these unnecessary texts?')

    def test_sentiment_start(self):
        """
        Testing that sentiment analyser starting page loads correctly
        """
        response = self.client.get(reverse('mlqda:sentiment-start'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
                            'Please upload your files to the')
        self.assertContains(response,
                            'Sentiment Analyser')

    def test_post_sentiment_start(self):
        """
        Testing if start page of sentiment analyser correctly redirects
        """
        test_content = "this is the test content"
        test_doc = SimpleUploadedFile('test_text.txt', test_content.encode(), 'text/plain')
        response = self.client.post(reverse('mlqda:sentiment-start'), {'file': test_doc})
        self.assertEqual(response.status_code, 302)

    def test_sentiment_result(self):
        """
        Testing if sentiment results page loads correctly
        """
        collector = FileCollector(first_name="test_files.txt")
        collector.save()
        test_path = os.path.relpath(settings.TEST_DIR, start=os.curdir)

        for file in os.listdir(test_path):
            file_path = os.path.join(test_path, file)
            if os.path.isfile(file_path) and file_path.endswith(".txt"):
                with open(file_path, 'r') as f:
                    test_content = f.read().encode('utf-8')
                    test_doc = SimpleUploadedFile(file_path, test_content)
                    current_file = FileContainer(file=test_doc, first_name=collector)
                    current_file.save()

        response = self.client.get(reverse('mlqda:sentiment-results',
                                           kwargs={'collector_id': collector.collector_id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sentiment Analysis Results")
        self.assertContains(response, "Next to the sentences, you can")


class TopicModellingTests(TestCase):
    """
    Class to collect test regarding the topic modelling script
    """

    def test_constructor(self):
        test_files = utils.get_test_files()
        test_tm = TopicModelling(test_files, 1)

        self.assertTrue('overtakes' in test_tm.datafiles[1])
        self.assertEqual(len(test_tm.datafiles), len(test_files))
        self.assertTrue('marketing' in test_tm.datafiles[1])

    def test_preprocess(self):
        test_files = utils.get_test_files()
        test_tm = TopicModelling(test_files, 1)
        test_tm.process_files()

        self.assertEqual(len(test_tm.processed_files), len(test_files))
        self.assertTrue('overtakes' in test_tm.datafiles[1])
        self.assertTrue('overtake' in test_tm.processed_files[1])
        self.assertFalse('overtakes' in test_tm.processed_files[1])
        self.assertTrue('the' in test_tm.datafiles[1])
        self.assertFalse('the' in test_tm.processed_files[1])

    def test_creating_helper_datastructures(self):
        test_files = utils.get_test_files()
        test_tm = TopicModelling(test_files, 1)
        test_tm.process_files()
        test_tm.create_helper_datastructures()

        self.assertEqual(len(test_tm.structures['bigram_texts']), len(test_files))
        self.assertEqual(len(test_tm.structures['trigram_texts']), len(test_files))
        self.assertTrue(len(test_tm.structures['id2word']) > len(test_tm.structures['corpus']))
        self.assertEqual(len(test_tm.structures['corpus']), len(test_files))

    def test_tf_idf_removal(self):
        test_files = utils.get_test_files()
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
        test_files = utils.get_test_files()
        test_tm = TopicModelling(test_files, 1)
        test_tm.process_files()
        test_tm.create_helper_datastructures()
        test_tm.tf_idf_removal()
        test_model = test_tm.run_lda(3)

        self.assertEqual(len(test_model.get_topics()), 3)

    def test_dynamic_lda(self):
        test_files = utils.get_test_files()
        test_tm = TopicModelling(test_files, 1)
        test_tm.process_files()
        test_tm.create_helper_datastructures()
        test_tm.tf_idf_removal()
        test_tm.dynamic_lda()

        self.assertEqual(len(test_tm.lda_model.get_topics()), 4)

    def test_compile_results(self):
        test_files = utils.get_test_files()

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

        test_zip_path = utils.get_test_zip_path(test_tm)

        with ZipFile(test_zip_path, 'r') as test_zip_results:
            zip_collector_id = str(test_tm.collector_id)
            zipped_test_result = test_zip_results.read(zip_collector_id+str('_results.json'))
            unzipped_test_result = json.loads(zipped_test_result.decode("utf-8"))

        self.assertEqual(len(unzipped_test_result), len(test_tm.lda_model.get_topics()))
        os.remove(test_zip_path)

    def test_create_highlights(self):
        test_files = utils.get_test_files()

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

        self.assertEqual(len(test_tm.highlight_paths), len(test_tm.lda_model.get_topics()))
        test_zip_path = utils.get_test_zip_path(test_tm)
        os.remove(test_zip_path)

    def test_visualisations(self):
        test_files = utils.get_test_files()

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
        test_viz_path = test_tm.create_visualisations()
        test_interactive_path = test_tm.create_interactive_visualisation()

        self.assertTrue(os.path.exists(test_viz_path))
        self.assertTrue(os.path.exists(test_interactive_path))
        test_zip_path = utils.get_test_zip_path(test_tm)
        os.remove(test_viz_path)
        os.remove(test_zip_path)
        os.remove(test_interactive_path)

    def test_create_csv_results(self):
        test_files = utils.get_test_files((".txt", ".csv"))

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
        test_tm.get_lda_output()
        test_tm.create_csv_results()

        self.assertTrue(os.path.exists(test_tm.csv_path))


class SentimentAnalysisTests(TestCase):

    def test_constructor(self):
        test_files = utils.get_test_files()
        test_sa = SentimentAnalyser(test_files, 2)

        self.assertTrue('overtakes' in test_sa.datafiles[1])
        self.assertEqual(len(test_sa.datafiles), len(test_files))
        self.assertTrue('marketing' in test_sa.datafiles[1])

    def test_create_file_models(self):
        test_file_collector = FileCollector(2, "test")
        test_file_collector.save()
        test_files = utils.get_test_files()
        test_sa = SentimentAnalyser(test_files, int(test_file_collector.collector_id))

        for path in test_files:
            test_sa.create_model(path)

        test_objects = FileContainer.objects.filter(first_name=test_file_collector.collector_id)

        self.assertEqual(len(test_objects), len(test_files))

    def test_create_pdf_results(self):
        test_file_collector = FileCollector(2, "test")
        test_file_collector.save()
        test_files = utils.get_test_files()
        test_sa = SentimentAnalyser(test_files, int(test_file_collector.collector_id))

        test_sa.create_pdf_results()

        self.assertTrue(os.path.isfile(str(test_sa.pdf_result)))

    def test_create_csv_results(self):
        test_file_collector = FileCollector(2, "test")
        test_file_collector.save()
        test_files = utils.get_test_files()
        test_sa = SentimentAnalyser(test_files, int(test_file_collector.collector_id))

        test_sa.create_csv_results()

        self.assertTrue(os.path.isfile(str(test_sa.csv_result)))

    def test_compile_results(self):
        test_file_collector = FileCollector(2, "test")
        test_file_collector.save()
        test_files = utils.get_test_files(extension=(".txt", ".csv"))

        test_sa = SentimentAnalyser(test_files, int(test_file_collector.collector_id))
        test_sa.create_pdf_results()
        test_sa.create_csv_results()
        test_sa.compile_results()

        test_zip_path = utils.get_test_zip_path(test_sa)

        with ZipFile(test_zip_path, 'r') as test_zip_results:
            number_of_files = len(test_zip_results.namelist())

        self.assertTrue(os.path.isfile(test_zip_path))
        self.assertEqual(number_of_files, 2)
        os.remove(test_zip_path)


class UtilsTests(TestCase):
    def test_read_txt(self):
        test_folder = os.path.relpath(settings.TEST_DIR, start=os.curdir)
        test_path = os.path.join(test_folder, "bbc1.txt")
        test_content = utils.read_txt(test_path)
        expected = """The SNP said Ms Braverman's "incendiary language makes a mockery of"""

        self.assertTrue(expected in test_content)

    def test_read_pdf(self):
        test_folder = os.path.relpath(settings.TEST_DIR, start=os.curdir)
        test_path = os.path.join(test_folder, "bbc1.pdf")
        test_content = utils.read_pdf(test_path)
        expected = """The SNP said Ms Braverman's "incendiary language makes a mockery of"""

        self.assertTrue(expected in test_content)

    def test_read_docs(self):
        test_folder = os.path.relpath(settings.TEST_DIR, start=os.curdir)
        test_path = os.path.join(test_folder, "bbc1.docx")
        test_content = utils.read_docx(test_path)
        expected = """The SNP said Ms Braverman's "incendiary language makes a mockery of"""

        self.assertTrue(expected in test_content)

    def test_read_csv(self):
        test_folder = os.path.relpath(settings.TEST_DIR, start=os.curdir)
        test_path = os.path.join(test_folder, "bbc1.csv")
        test_content = utils.read_csv(test_path)
        expected = """The SNP said Ms Braverman's "incendiary language makes a mockery of"""
        self.assertTrue(expected in test_content)

    def test_read_xlsx(self):
        test_folder = os.path.relpath(settings.TEST_DIR, start=os.curdir)
        test_path = os.path.join(test_folder, "bbc1.xlsx")
        test_content = utils.read_xlsx(test_path)
        expected = """The SNP said Ms Braverman's "incendiary language makes a mockery of"""
        self.assertTrue(expected in test_content)

    def test_get_datafiles(self):
        test_file_list = utils.get_test_files("")
        corpus = utils.get_datafiles(test_file_list)

        self.assertEqual(len(corpus), 9)

    def test_get_test_files(self):
        test_file_list = utils.get_test_files()

        self.assertEqual(len(test_file_list), 5)

    def test_calculate_topic_number(self):
        less_than_four = utils.calculate_topic_number(3)
        between_five_and_twelve = utils.calculate_topic_number(6)
        larger_than_twelve = utils.calculate_topic_number(15)

        self.assertEqual(5, less_than_four)
        self.assertEqual(7, between_five_and_twelve)
        self.assertEqual(12, larger_than_twelve)

    def test_write_sentiemnt_csv_file(self):
        row = {"File Name": "test file",
               "Entry": "test sentence",
               "Sentiment Score": 0}

        path = utils.write_sentiemnt_csv_file("test", [row])
        self.assertTrue(os.path.exists(str(path)))
