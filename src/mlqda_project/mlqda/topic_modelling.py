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
from mlqda.utils import get_datafiles
import re
from zipfile import ZipFile
import statistics
from pylatex import Document, Section, Package, Command, Itemize, LargeText, NoEscape
from pylatex.base_classes import Arguments
from pylatex.utils import bold
import unidecode
import matplotlib.pyplot as plt
import matplotlib.ticker
import pyLDAvis.gensim_models
import subprocess
from distutils.spawn import find_executable
import threading
import csv
import nltk
nltk.download('stopwords')


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
        self.models = []
        self.post_tags = ["NOUN", "ADJ", "VERB", "ADV"]
        self.my_stopwords = nltk.corpus.stopwords.words("english")
        self.nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])

    def filter_and_lemmatize(self, entries):
        current_document = self.nlp(entries)
        lemmatized_words = []

        for word in current_document:
            if word.pos_ in self.post_tags:
                if str(word) not in self.my_stopwords:
                    if str(word.lemma_) not in self.my_stopwords:
                        lemmatized_words.append(word.lemma_)

        lemmatized_text = " ".join(lemmatized_words)
        return lemmatized_text

    def process_files(self):
        """
        function to help with pre-processing. Transforms files into list of words.
        Then lemmatizes and removes stopwords from those lists.
        """
        for current_text in self.datafiles:
            entries = re.sub(r'@\w+', '', current_text)
            entries = re.sub(r'http\S+', '', entries)

            file_path = self.datafile_paths[self.datafiles.index(current_text)]
            file_name = os.path.basename(file_path)

            if file_name.endswith((".xlsx", '.csv')):
                entries = entries.split('MLQDAdataBreak')
                for entry in entries:
                    lemmatized_text = self.filter_and_lemmatize(entry)
                    preprocessed_text = simple_preprocess(lemmatized_text, deacc=True)
                    self.processed_files.append(preprocessed_text)
            else:
                lemmatized_text = self.filter_and_lemmatize(entries)
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
        self.models.append(lda_model)
        return lda_model

    def dynamic_lda(self):
        """
        Function to dynamically run multiple lda models at the same time.
        Creating threads for each possible model and start them at the same time.
        When all of them have finished, save the one with the highest coherence score.
        """
        if len(self.datafiles) < 4:
            topic_number = 5
        elif len(self.datafiles) < 12:
            topic_number = len(self.datafiles)+1
        else:
            topic_number = 12

        coherence_scores = []
        threads = []

        for i in range(2, topic_number):
            current_thread = threading.Thread(target=self.run_lda, args=(i, ))
            threads.append(current_thread)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for current_model in self.models:
            current_coherence = CoherenceModel(model=current_model,
                                               texts=self.structures['trigram_texts'],
                                               coherence='u_mass')
            coherence_scores.append(current_coherence.get_coherence())

        max_coherence = max(coherence_scores)
        max_index = coherence_scores.index(max_coherence)
        max_model = self.models[max_index]

        self.lda_model = max_model

    def get_lda_output(self):
        """
        Function to extract the required information from the best model.
        Saves the information as a nested a dictionary, where every topic is a key
        to anoter dictionary with word and contribution pairs.
        """
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
        """
        Function to compile a pdf with the higlighted results.
        Adds explanatory paragrpahs to hepl the user interpret the results.
        Orders every document in the corpus to its own paragraph where each sentence is a row.
        Next the, the user can find any of the topic words present in that sentence.
        If at least one word is present, the sentence is highlighted.
        """

        highlight_paths = []
        topics = list(self.result_dict.values())

        double_esc = NoEscape("\\")+NoEscape("\\")
        for contrib_list in topics:
            word_list = []
            col_id = str(self.collector_id)
            topic_index = str(topics.index(contrib_list)+1)
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
            doc.packages.append(Package('ltablex'))
            doc.preamble.append(Command('sethlcolor', 'yellow'))
            doc.append(LargeText(bold("Topic modelling reuslts")))

            with doc.create(
                    Section('Most important words for topic ' + str(topic_index))
                    ):
                with doc.create(Itemize()) as itemize:
                    for contirb_tuple in contrib_list:
                        current_item = str(contirb_tuple[1]) + "--" + str(contirb_tuple[0])
                        word_list.append(str(contirb_tuple[1]))
                        itemize.add_item(current_item)
                    doc.append("\n\n\n")
                    text = "Sentences that contain any of these words are highlighted below."
                    doc.append(text)
                    doc.append("\n")

            for file in self.datafiles:
                with doc.create(
                        Section('Highlights from text '+str(self.datafiles.index(file)+1))
                        ):
                    tabular_args = Arguments('tabularx', NoEscape(r'\textwidth'), '|X|X|')
                    doc.append(Command("begin", arguments=tabular_args))

                    topic_words = NoEscape(Command("textbf", arguments="Topic Words").dumps())
                    sente = NoEscape(Command("textbf", arguments="Sentence").dumps())
                    header = "&".join([topic_words, sente])+double_esc
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

                    for sentence in sentences:
                        row = []

                        present = [word for word in word_list if word in sentence]
                        present_words = ", ".join(present)
                        row.append(present_words)

                        if any(word in str(sentence) for word in word_list):
                            unaccented_string = unidecode.unidecode(str(sentence))
                            highlight = Command("hl", arguments=unaccented_string).dumps()
                            row.append(NoEscape(highlight+double_esc))
                        else:
                            row.append(str(unidecode.unidecode(str(sentence)))+double_esc)
                        doc.append(NoEscape(" & ".join(row)))
                        doc.append(Command("hline"))

                    doc.append(Command("end", arguments=Arguments('tabularx')))

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

            self.highlight_paths = highlight_paths

    def create_csv_results(self):
        fields = ['File Name', 'Entry']
        topics = list(self.result_dict.values())

        for contrib_list in topics:
            topic_name = "Topic " + str(topics.index(contrib_list))
            fields.append(topic_name)

        rows = []
        for file in self.datafiles:
            file_path = self.datafile_paths[self.datafiles.index(file)]
            file_name = os.path.basename(file_path)

            if file_name.endswith((".xlsx", '.csv')):
                sentences = file.split('MLQDAdataBreak')
            else:
                sentences = file.split(". ")

            for sentence in sentences:
                current_row = {'File Name': file_name,
                               'Entry': unidecode.unidecode(str(sentence))}

                topics = list(self.result_dict.values())
                for contrib_list in topics:
                    word_list = []
                    for contirb_tuple in contrib_list:
                        word_list.append(str(contirb_tuple[1]))

                    present = [word for word in word_list if word in sentence]

                    topic_name = "Topic " + str(topics.index(contrib_list))
                    current_row[topic_name] = " - ".join(present)
                rows.append(current_row)

        col_id = str(self.collector_id)
        path = os.path.join(settings.MEDIA_DIR, str(col_id + "_" + "results.csv"))
        with open(path, "w", newline='') as results:
            writer = csv.DictWriter(results, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

        self.csv_path = path

    def create_visualisations(self):
        """
        Function to manually create visualisation to the lda topic models.
        """

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
        """
        Function to create interactive visualisations to the lda topic models.
        """

        p = pyLDAvis.gensim_models.prepare(self.lda_model,
                                           self.structures['corpus'],
                                           self.structures['id2word'])
        path = os.path.join(settings.MEDIA_DIR,
                            str(self.collector_id)+str('_result_interactive_visualisation.html'))

        pyLDAvis.save_html(p, path)
        return path

    def compile_results(self):
        """
        Function to compile a zip file with all the results.
        Uses data provided by get_lda_output, create_highlights, create_highlights,
        create_interactive_visualisation
        Deletes every file apart from the zip file before returning a peth to the zip file.
        """

        self.get_lda_output()
        self.create_highlights()
        self.create_csv_results()
        viz_path = self.create_visualisations()
        collector = FileCollector.objects.get(collector_id=self.collector_id)
        path = os.path.join(settings.MEDIA_DIR, str(str(self.collector_id)+str('_results.json')))
        csv_path = self.csv_path
        with open(path, 'w+') as output:
            json.dump(self.result_dict, output)

        id_to_word_path = os.path.join(settings.MEDIA_DIR,
                                       str(str(self.collector_id)+str('id2word.txt')))
        with open(id_to_word_path, 'w'):
            self.structures['id2word'].save_as_text(id_to_word_path)

        corpus_path = os.path.join(settings.MEDIA_DIR,
                                   str(str(self.collector_id)+str('corpus.txt')))
        with open(corpus_path, 'w') as corpus_text:
            corpus_text.write(str(self.structures['corpus']))

        self.zip_name = str(str(self.collector_id)+str('_results.zip'))
        zip_path = os.path.join(settings.MEDIA_DIR, self.zip_name)
        with ZipFile(zip_path, 'w') as zip_results:
            zip_results.write(path, str(os.path.basename(str(path))))
            zip_results.write(viz_path, str(os.path.basename(str(viz_path))))
            zip_results.write(csv_path, str(os.path.basename(str(csv_path))))
            zip_results.write(id_to_word_path, str(os.path.basename(str(id_to_word_path))))
            zip_results.write(corpus_path, str(os.path.basename(str(corpus_path))))

            os.remove(path)
            os.remove(viz_path)
            os.remove(csv_path)
            os.remove(id_to_word_path)
            os.remove(corpus_path)

            for highlight_file in self.highlight_paths:
                zip_results.write(str(highlight_file)+".pdf",
                                  str(os.path.basename(str(highlight_file)+".pdf")))
                os.remove(str(highlight_file)+".pdf")

        zip_model = FileContainer.objects.create(first_name=collector, file=zip_path)
        zip_model.save()

        for file_path in self.datafile_paths:
            if "test" not in str(file_path):
                os.remove(file_path)
