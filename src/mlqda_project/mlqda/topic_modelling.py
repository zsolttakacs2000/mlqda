"""
This file includes the class that handles the topic modelling from MLQDA
Inspiration of the processes and steps were taken from:
    - https://www.machinelearningplus.com/nlp/topic-modeling-gensim-python/
    - https://github.com/wjbmattingly/topic_modeling_textbook/find/main
    - https://radimrehurek.com/gensim/index.html
"""
import gensim
import gensim.corpora as corpora
from gensim.utils import simple_preprocess
import spacy
from nltk.corpus import stopwords
import json
from django.conf import settings
import os
from mlqda.models import FileCollector, FileContainer
import re
from zipfile import ZipFile


class TopicModelling:
    """
    Class to handle topic modelling functions and data
    self.datafiles is a list of full texts. []
    """
    def __init__(self, datafiles: list, collector_id):
        self.datafiles = datafiles
        self.collector_id = collector_id
        self.processed_files = []
        self.structures = {}
        self.result_dict = {}

    def __str___(self):
        return str(self.datafiles)

    def process_files(self):
        """
        function to help with pre-processing. Transforms files into list of words.
        Then lemmatizes and removes stopwords from those lists.
        """
        postags = ["NOUN", "ADJ", "VERB", "ADV"]
        my_stopwords = stopwords.words("english")
        nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])

        for current_text in self.datafiles:
            current_document = nlp(current_text)
            lemmatized_words = []

            for word in current_document:
                if word.pos_ in postags:
                    if str(word) not in my_stopwords and str(word.lemma_) not in my_stopwords:
                        lemmatized_words.append(word.lemma_)

            lemmatized_text = " ".join(lemmatized_words)

            preprocessed_text = simple_preprocess(lemmatized_text, deacc=True)

            self.processed_files.append(preprocessed_text)

    def create_helper_datastructures(self):
        """
        function to create all data structures that are required to run an LDA
        """
        processed_files = self.processed_files

        word_pairs = gensim.models.Phrases(processed_files, min_count=5, threshold=5)
        word_trios = gensim.models.Phrases(word_pairs[processed_files], threshold=5)

        bigram = gensim.models.phrases.Phraser(word_pairs)
        trigram = gensim.models.phrases.Phraser(word_trios)

        trigram_texts = []
        bigram_texts = []
        for text in processed_files:
            current_bigram = bigram[text]
            current_trigram = trigram[bigram[text]]
            bigram_texts.append(current_bigram)
            trigram_texts.append(current_trigram)

        self.structures['bigram_texts'] = bigram_texts
        self.structures['trigram_texts'] = trigram_texts

        id2word = corpora.Dictionary(trigram_texts)

        corpus = []
        for text in trigram_texts:
            bag_of_words = id2word.doc2bow(text)
            corpus.append(bag_of_words)

        self.structures['id2word'] = id2word
        self.structures['corpus'] = corpus

    def tf_idf_removal(self):
        """
        Exclude words that would be prevelant in all topics using their tf-idf score
        """
        return True

    def run_lda(self):
        """
        function to an LDA with preet parameters
        accessing and saving data and results from the object attribute
        """
        lda_model = gensim.models.ldamodel.LdaModel(corpus=self.structures['corpus'],
                                                    id2word=self.structures['id2word'],
                                                    num_topics=4,
                                                    random_state=100,
                                                    update_every=1,
                                                    chunksize=100,
                                                    passes=10,
                                                    alpha="auto")
        self.lda_model = lda_model

    def get_lda_output(self):
        topics = self.lda_model.print_topics()
        return topics

    def compile_reuslts(self):
        for topic in self.get_lda_output():
            topic_contrib = []
            contrib_string = str(topic[1])
            contrib_string = re.sub("'", "", contrib_string)
            contrib_string = re.sub('"', '', contrib_string)
            contrib_string = re.sub(" ", "", contrib_string)
            values = contrib_string.split("+")
            for contribution in values:
                contrib_list = contribution.split('*')
                contrib_tuple = (float(contrib_list[0]), str(contrib_list[1]).strip())
                topic_contrib.append(contrib_tuple)

            self.result_dict[str(int(topic[0])+1)] = topic_contrib

        collector = FileCollector.objects.get(collector_id=self.collector_id)
        path = os.path.join(settings.MEDIA_ROOT, str(str(self.collector_id)+str('_results.json')))
        with open(path, 'w') as output:
            json.dump(self.result_dict, output)

        self.zip_name = str(str(self.collector_id)+str('_results.zip'))
        zip_path = os.path.join(settings.MEDIA_ROOT, self.zip_name)
        with ZipFile(zip_path, 'w') as zip_results:
            zip_results.write(path, str(os.path.basename(str(path))))

        result_file = FileContainer.objects.create(first_name=collector, file=path)
        result_file.save()
        zip_model = FileContainer.objects.create(first_name=collector, file=zip_path)
        zip_model.save()
