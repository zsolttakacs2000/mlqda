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
from gensim.models import TfidfModel, CoherenceModel
import spacy
import json
from django.conf import settings
import os
from mlqda.models import FileCollector, FileContainer
import re
from zipfile import ZipFile
import statistics
from pylatex import Document, Section, Package, Command, Itemize, LargeText
from pylatex.utils import bold
import unidecode
import matplotlib.pyplot as plt
import matplotlib.ticker
import pyLDAvis.gensim_models
import subprocess
from distutils.spawn import find_executable
import nltk
nltk.download('stopwords')


def get_datafiles(path_list):
    full_text = []
    for file_path in path_list:
        with open(file_path, 'r', encoding="utf8") as f:
            text = f.read().replace('\n', ' ')
            full_text.append(text)
    return full_text


class TopicModelling:
    """
    Class to handle topic modelling functions and data
    self.datafiles is a list of full texts. []
    """
    def __init__(self, datafile_paths: list, collector_id):
        self.datafile_paths = datafile_paths
        self.datafiles = get_datafiles(datafile_paths)
        self.collector_id = collector_id
        self.processed_files = []
        self.structures = {}
        self.result_dict = {}

    def process_files(self):
        """
        function to help with pre-processing. Transforms files into list of words.
        Then lemmatizes and removes stopwords from those lists.
        """
        postags = ["NOUN", "ADJ", "VERB", "ADV"]
        my_stopwords = nltk.corpus.stopwords.words("english")
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
        Save existing ids
        Find low ids of low value words and create new list without them
        Save new list to object attribute
        """
        tf_idf_scores = TfidfModel(self.structures['corpus'], id2word=self.structures['id2word'])

        all_tfidf_vals = []
        for bow in self.structures['corpus']:
            for id, value in tf_idf_scores[bow]:
                all_tfidf_vals.append(float(value))

        median_tfidf = statistics.median(sorted(all_tfidf_vals))

        low_value = median_tfidf
        words = []
        my_missing_words = []
        for bow in self.structures['corpus']:
            low_score_words = []

            all_tfidfs = []
            for id, value in tf_idf_scores[bow]:
                all_tfidfs.append(id)

            all_bows = []
            for id, value in bow:
                all_bows.append(id)

            low_score_words = []
            for id, value in tf_idf_scores[bow]:
                if value < low_value:
                    low_score_words.append(id)

            drops = low_score_words+my_missing_words
            for item in drops:
                words.append(self.structures['id2word'][item])

            my_missing_words = []
            for id in all_bows:
                if id not in all_tfidfs:
                    my_missing_words.append(id)

            filtered_bow = []
            for b in bow:
                if b[0] not in low_score_words and b[0] not in my_missing_words:
                    filtered_bow.append(b)

            current_index = self.structures['corpus'].index(bow)
            self.structures['corpus'][current_index] = filtered_bow

    def run_lda(self, num):
        """
        function to an LDA with preet parameters
        accessing and saving data and results from the object attribute
        """
        lda_model = gensim.models.ldamodel.LdaModel(corpus=self.structures['corpus'],
                                                    id2word=self.structures['id2word'],
                                                    num_topics=num,
                                                    random_state=100,
                                                    update_every=1,
                                                    chunksize=100,
                                                    passes=10,
                                                    alpha="auto")
        return lda_model

    def dynamic_lda(self):
        models = []
        coherence_scores = []
        for i in range(2, len(self.datafiles)+1):
            current_model = self.run_lda(i)
            current_coherence = CoherenceModel(model=current_model,
                                               texts=self.structures['trigram_texts'],
                                               coherence='c_v')
            models.append(current_model)
            coherence_scores.append(current_coherence.get_coherence())

        max_coherence = max(coherence_scores)
        max_index = coherence_scores.index(max_coherence)
        max_model = models[max_index]

        self.lda_model = max_model

    def get_lda_output(self):
        topics = self.lda_model.print_topics()
        for topic in topics:
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

        return self.result_dict

    def create_highlights(self):
        highlight_paths = []
        words = []
        for topic, contrib_list in self.result_dict.items():
            words.append([contribution_tuple[1] for contribution_tuple in contrib_list])

        for topic in words:
            col_id = str(self.collector_id)
            topic_index = str(words.index(topic)+1)
            doc_name = str(col_id+"_topic"+topic_index+str('_highlights'))
            path = os.path.join(settings.MEDIA_DIR, doc_name)
            highlight_paths.append(path)
            geometry_options = {"tmargin": "1in",
                                "lmargin": "1in",
                                "bmargin": "1in",
                                "rmargin": "1in"}
            doc = Document(geometry_options=geometry_options, lmodern=True, textcomp=True)
            doc.packages.append(Package('soul'))
            doc.packages.append(Package('xcolor'))
            doc.preamble.append(Command('sethlcolor', 'yellow'))
            doc.append(LargeText(bold("Topic modelling reuslts")))

            with doc.create(
                    Section('Most important words for topic ' + str(words.index(topic)+1))
                    ):
                with doc.create(Itemize()) as itemize:
                    for word in topic:
                        itemize.add_item(word)
                    doc.append("\n\n\n")
                    text = "Sentences that contain any of these words are highlighted below."
                    doc.append(text)
                    doc.append("\n")

            for file in self.datafiles:
                with doc.create(
                        Section('Highlights from text '+str(self.datafiles.index(file)+1))
                        ):
                    sentences = file.split(". ")

                    for sentence in sentences:
                        if any(word in str(sentence) for word in topic):
                            unaccented_string = unidecode.unidecode(str(sentence))
                            doc.append(Command("hl", arguments=unaccented_string))
                            doc.append("\n")
                        else:
                            doc.append(str(sentence) + "\n")
            doc.generate_tex(path)

            my_pdf_latex = find_executable('pdflatex')
            compile_command = " ".join([my_pdf_latex,
                                        '-interaction=nonstopmode',
                                        doc_name+".tex"])
            destination_dir = os.path.relpath(settings.MEDIA_DIR, start=os.curdir)
            switch_cwd = " ".join(['cd', destination_dir])
            command = " & ".join([switch_cwd, 'ls', compile_command])
            print(command)
            proc = subprocess.Popen(command, shell=True)
            proc.wait()

            self.highlight_paths = highlight_paths

    def create_visualisations(self):
        collector = str(self.collector_id)
        path = os.path.join(settings.MEDIA_DIR,
                            collector+str('_result_visualisation.png'))
        words = []
        contrib = []
        for topic, contrib_list in self.result_dict.items():
            sorted_contrib = sorted(contrib_list, key=lambda x: x[0])
            words.append([contribution_tuple[1] for contribution_tuple in sorted_contrib])
            contrib.append([contribution_tuple[0]*100 for contribution_tuple in sorted_contrib])

        fig, axes = plt.subplots(len(words), 1, figsize=(16, 10),
                                 sharey=False, sharex=True, dpi=160)
        for i, ax in enumerate(axes.flatten()):
            ax.barh(words[i], contrib[i])
            ax.set_ylabel("Topic "+str(i+1))
            ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter())
        fig.supylabel("Topics")
        desc = "Percentage contribution of each word towards their distinct topic. "
        note = "These are the top 10 words only, so they do not necessarily add up to 100%"
        fig.supxlabel('Contribution in percentages \n\n\n' + desc + note)
        fig.suptitle("Word contribution to each topic")
        plt.savefig(path)
        return path

    def create_interactive_visualisation(self):
        p = pyLDAvis.gensim_models.prepare(self.lda_model,
                                           self.structures['corpus'],
                                           self.structures['id2word'])
        path = os.path.join(settings.MEDIA_DIR,
                            str(self.collector_id)+str('_result_interactive_visualisation.html'))

        pyLDAvis.save_html(p, path)
        return path

    def compile_results(self):
        self.get_lda_output()
        self.create_highlights()
        viz_path = self.create_visualisations()
        interactive_viz = self.create_interactive_visualisation()
        self.create_interactive_visualisation()
        collector = FileCollector.objects.get(collector_id=self.collector_id)
        path = os.path.join(settings.MEDIA_DIR, str(str(self.collector_id)+str('_results.json')))
        with open(path, 'w+') as output:
            json.dump(self.result_dict, output)

        self.zip_name = str(str(self.collector_id)+str('_results.zip'))
        zip_path = os.path.join(settings.MEDIA_DIR, self.zip_name)
        with ZipFile(zip_path, 'w') as zip_results:
            zip_results.write(path, str(os.path.basename(str(path))))
            zip_results.write(viz_path, str(os.path.basename(str(viz_path))))
            zip_results.write(interactive_viz, str(os.path.basename(str(interactive_viz))))
            os.remove(path)
            os.remove(viz_path)
            os.remove(interactive_viz)
            for highlight_file in self.highlight_paths:
                zip_results.write(str(highlight_file)+".pdf",
                                  str(os.path.basename(str(highlight_file)+".pdf")))
                os.remove(str(highlight_file)+".pdf")

        zip_model = FileContainer.objects.create(first_name=collector, file=zip_path)
        zip_model.save()

        for file_path in self.datafile_paths:
            if "test" not in str(file_path):
                os.remove(file_path)
