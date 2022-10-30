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


class TopicModelling:
    """
    Class to handle topic modelling functions and data
    self.datafiles is a list of full texts. []
    """
    def __init__(self, datafiles: list):
        self.datafiles = datafiles
        self.processed_files = []
        self.structures = {}

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
        lda_model = gensim.models.ldamodel.LdaModel(corpus=self.structures['corpus'][:-1],
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
