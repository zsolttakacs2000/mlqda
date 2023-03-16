"""
This file includes the class that handles the sentiment analysis from MLQDA
Inspiration of the processes and steps were taken from:
    - https://realpython.com/python-nltk-sentiment-analysis/
"""
from django.conf import settings
import os
from mlqda.models import FileCollector, FileContainer
from mlqda.utils import get_datafiles, write_sentiemnt_csv_file
from pylatex import Document, Section, Package, Command, LargeText, NoEscape
from pylatex.base_classes import Arguments
from pylatex.utils import bold
import re
import unidecode
import subprocess
import csv
from zipfile import ZipFile
from distutils.spawn import find_executable
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
nltk.download('vader_lexicon')


class SentimentAnalyser:
    """
    Class to handle topic modelling functions and data
    self.datafiles is a list of full texts. []
    """
    def __init__(self, datafile_paths: list, collector_id):
        self.datafile_paths = datafile_paths
        self.datafiles = get_datafiles(datafile_paths)
        self.collector_id = collector_id

    def create_model(self, location):
        """
        Function to create model representation of files as FileContainers
        """
        file_path = os.path.join(settings.MEDIA_DIR, location)
        collector = FileCollector.objects.get(collector_id=self.collector_id)
        result_model = FileContainer.objects.create(first_name=collector, file=file_path)
        result_model.save()

    def remove_input_files(self):
        """
        Function to remove uploaded files after processing them
        """
        for file in self.datafile_paths:
            if "test" not in str(file):
                os.remove(file)

    def create_pdf_results(self):
        """
        Function to compile result pdf. Adds explanatory paragraphs.
        Sentiment scores calculated on a per sentence basis.
        """
        double_esc = NoEscape("\\")+NoEscape("\\")
        corpus_sentiment_sum = 0
        col_id = str(self.collector_id)
        doc_name = str(col_id+"_sentiment_analysis")
        path = os.path.join(settings.MEDIA_DIR, doc_name)

        geometry_options = {"tmargin": "1in",
                            "lmargin": "1in",
                            "bmargin": "1in",
                            "rmargin": "1in"}
        doc = Document(geometry_options=geometry_options, lmodern=True, textcomp=True)
        doc.packages.append(Package('soul'))
        doc.packages.append(Package('xcolor'))
        doc.packages.append(Package('ltablex'))
        doc.preamble.append(Command('sethlcolor', 'yellow'))
        doc.append(LargeText(bold("Sentiment Analysis results")))

        with doc.create(Section('Sentiment Analysis')):
            sentiment_description = """
            The sentiment scores are present on the left-hand side of the table.
            The analyser uses compound sentiment scores calculated from positive,
            negative and neutral sentiment scores. The displayed scores range from -1 to 1,
            which you can interpret as percentages. For example, you can interpret a score
            of +0.25 as 25% positive sentiment. When compiling the document, the system calculates
            the sentiment score for every sentence.
            """
            doc.append(sentiment_description.replace('\n', ' '))

        for file in self.datafiles:
            with doc.create(
                    Section('Sentiments from text '+str(self.datafiles.index(file)+1))
                    ):
                tabular_args = Arguments('tabularx', NoEscape(r'\textwidth'), '|l|X|')
                doc.append(Command("begin", arguments=tabular_args))

                senti = NoEscape(Command("textbf", arguments="Sentiment").dumps())
                sente = NoEscape(Command("textbf", arguments="Sentence").dumps())
                header = "&".join([senti, sente])+double_esc
                doc.append(Command("hline"))
                doc.append(NoEscape(header))
                doc.append(Command("hline"))
                doc.append(Command("hline"))
                doc.append(Command("endhead"))
                next_footer_args = Arguments('2', 'r', 'Continued on Next Page')
                doc.append(Command("multicolumn", arguments=next_footer_args))
                doc.append(Command("endfoot"))
                last_footer_args = Arguments('2', 'r', 'End of section')
                doc.append(Command("multicolumn", arguments=last_footer_args))
                doc.append(Command("endlastfoot"))

                file_path = self.datafile_paths[self.datafiles.index(file)]
                file_name = os.path.basename(file_path)

                if file_name.endswith((".xlsx", '.csv')):
                    sentences = file.split('MLQDAdataBreak')
                else:
                    sentences = file.split(". ")

                sum_sentence_sentiment = 0
                for sentence in sentences:
                    tag_removed_text = re.sub(r'@\w+', '', sentence)
                    row = []
                    sentiment_analyser = SentimentIntensityAnalyzer()
                    sentiment_scores = sentiment_analyser.polarity_scores(str(tag_removed_text))
                    compound_score = sentiment_scores['compound']
                    sum_sentence_sentiment += compound_score
                    row.append(str(compound_score))

                    unaccented_string = unidecode.unidecode(str(sentence))
                    row.append(str(unaccented_string)+double_esc)

                    doc.append(NoEscape(" & ".join(row)))
                    doc.append(Command("hline"))

                doc.append(Command("end", arguments=Arguments('tabularx')))
                avg_sentence_sentiment = sum_sentence_sentiment/len(sentences)
                corpus_sentiment_sum += avg_sentence_sentiment
                sentence_result = "This document has an avarge of {avg:.2f} sentiment score."
                doc.append(sentence_result.format(avg=avg_sentence_sentiment))

        with doc.create(Section('Overall sentiment score')):
            corpus_sentiment_mean = corpus_sentiment_sum/len(self.datafiles)
            corpus_result = "This set of documents has an average of {avg:.2f} sentiment score."
            doc.append(corpus_result.format(avg=corpus_sentiment_mean))

        doc.generate_tex(path)

        my_pdf_latex = find_executable('pdflatex')
        compile_command = " ".join([my_pdf_latex,
                                    '-interaction=nonstopmode',
                                    doc_name+".tex"])
        destination_dir = os.path.relpath(settings.MEDIA_DIR, start=os.curdir)
        switch_cwd = " ".join(['cd', destination_dir])
        command = " && ".join([switch_cwd, compile_command])
        proc = subprocess.Popen(command, shell=True)
        proc.wait()

        proc = subprocess.Popen(command, shell=True)
        proc.wait()

        [os.remove(path+ext) for ext in ['.log', '.tex', '.aux']]

        result_location = str(path)+'.pdf'
        self.create_model(result_location)
        self.pdf_result = result_location

    def create_csv_results(self):
        rows = []
        for file in self.datafiles:
            file_path = self.datafile_paths[self.datafiles.index(file)]
            file_name = os.path.basename(file_path)

            if file_name.endswith((".xlsx", '.csv')):
                sentences = file.split('MLQDAdataBreak')
            else:
                sentences = file.split(". ")

            for sentence in sentences:
                tag_removed_text = re.sub(r'@\w+', '', sentence)
                sentiment_analyser = SentimentIntensityAnalyzer()
                sentiment_scores = sentiment_analyser.polarity_scores(str(tag_removed_text))
                compound_score = sentiment_scores['compound']
                row = {"File Name": file_name,
                       "Entry": unidecode.unidecode(str(sentence)),
                       "Sentiment Score": compound_score}
                rows.append(row)

        path = write_sentiemnt_csv_file(self.collector_id, rows)
        self.create_model(path)
        self.csv_result = path

    def compile_results(self):
        self.zip_name = str(str(self.collector_id)+str('_results.zip'))
        zip_path = os.path.join(settings.MEDIA_DIR, self.zip_name)

        with ZipFile(zip_path, 'w') as zip_results:
            zip_results.write(self.pdf_result, str(os.path.basename(str(self.pdf_result))))
            zip_results.write(self.csv_result, str(os.path.basename(str(self.csv_result))))
            os.remove(self.pdf_result)
            os.remove(self.csv_result)

        self.remove_input_files()
        self.create_model(zip_path)

        return self.zip_name
