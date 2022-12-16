"""
This file includes the class that handles the sentiment analysis from MLQDA
Inspiration of the processes and steps were taken from:
    - https://realpython.com/python-nltk-sentiment-analysis/
"""
from django.conf import settings
import os
from mlqda.models import FileCollector, FileContainer
from pylatex import Document, Section, Package, Command, LargeText, NoEscape
from pylatex.base_classes import Arguments
from pylatex.utils import bold
import unidecode
import subprocess
from distutils.spawn import find_executable
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
nltk.download('vader_lexicon')


def get_datafiles(path_list):
    full_text = []
    for file_path in path_list:
        with open(file_path, 'r', encoding="utf8") as f:
            text = f.read().replace('\n', ' ')
            full_text.append(text)
    return full_text


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
        file_path = os.path.join(settings.MEDIA_DIR, location)
        collector = FileCollector.objects.get(collector_id=self.collector_id)
        result_model = FileContainer.objects.create(first_name=collector, file=file_path)
        result_model.save()

    def remove_input_files(self):
        for file in self.datafile_paths:
            if "test" not in str(file):
                os.remove(file)

    def run_sentiment_analyser(self):
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
            corpus_sentiment_mean = corpus_sentiment_sum/len(self.datafiles)
            corpus_result = "This set of documents has an avarge of {avg:.2f} sentiment score."
            sentiment_description = """
                Sentiment scores can be found on the left-hand side of the table.
            These scores are called 'compound sentiment scores' as
            they are calculated from negative, neutral and positive
            sentiment scores. The displayed scores range from -1 to 1,
            so in essence you can interpret them as percentages.
            For example a score of +0.25 could be interpreted as 25% positive.
            When compiling the document, the system calculates the sentiment score
            for every sentence. These sentence-sentiment scores are then aggregated
            into a document and a corpora wide sentiemnt score. This way,
            you end up with an avarge sentiment score for each of your uploaded
            document and with one avarge sentiment score for all of your documents."""
            doc.append(corpus_result.format(avg=corpus_sentiment_mean))
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

                sentences = file.split(". ")

                sum_sentence_sentiment = 0
                for sentence in sentences:
                    row = []
                    sentiment_analyser = SentimentIntensityAnalyzer()
                    sentiment_scores = sentiment_analyser.polarity_scores(str(sentence))
                    compound_score = sentiment_scores['compound']
                    sum_sentence_sentiment += compound_score
                    row.append(str(compound_score))

                    unaccented_string = unidecode.unidecode(str(sentence))
                    row.append(str(unaccented_string)+double_esc)

                    doc.append(NoEscape("&".join(row)))
                    doc.append(Command("hline"))

                doc.append(Command("end", arguments=Arguments('tabularx')))
                avg_sentence_sentiment = sum_sentence_sentiment/len(sentences)
                corpus_sentiment_sum += avg_sentence_sentiment
                sentence_result = "This document has an avarge of {avg:.2f} sentiment score."
                doc.append(sentence_result.format(avg=avg_sentence_sentiment))

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
        [os.remove(path+ext) for ext in ['.log', '.tex', '.aux']]

        result_location = doc_name+'.pdf'
        self.create_model(result_location)
        self.remove_input_files()
        return result_location
