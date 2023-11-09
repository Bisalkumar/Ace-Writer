import nltk
from nltk.corpus import stopwords
import numpy as np
import spacy
import networkx as nx
from spacy.lang.en.stop_words import STOP_WORDS
from spacy.lang.en import English
from string import punctuation

# load spacy's english language model
nlp = English()
nlp = spacy.load('en_core_web_sm')

# function to calculate similarity between two sentences
def sentence_similarity(sent1, sent2):
    sent1 = nlp(sent1)
    sent2 = nlp(sent2)
    return sent1.similarity(sent2)

# function to summarize text using Luhn's algorithm
def luhn_summarizer(text):
    stop_words = set(stopwords.words("english"))
    new_words = []
    sentence_list = nltk.sent_tokenize(text)
    for i in sentence_list:
        words = nltk.word_tokenize(i)
        words = [word for word in words if word.lower() not in stop_words]
        new_words.append(words)

    # create word frequency dictionary
    word_frequencies = {}
    for sentence in new_words:
        for word in sentence:
            if word not in word_frequencies:
                word_frequencies[word] = 1
            else:
                word_frequencies[word] += 1

    # calculate sentence scores based on words frequency
    sentence_scores = {}
    for i, sentence in enumerate(new_words):
        sentence_scores[i] = 0
        for word in sentence:
            if word in word_frequencies:
                sentence_scores[i] += word_frequencies[word]

    # create the similarity matrix
    similarity_matrix = np.zeros((len(sentence_list), len(sentence_list)))
    for i in range(len(sentence_list)):
        for j in range(len(sentence_list)):
            if i != j:
                similarity_matrix[i][j] = sentence_similarity(sentence_list[i], sentence_list[j])

    # create the sentence similarity graph
    sentence_similarity_graph = nx.from_numpy_array(similarity_matrix)

    # calculate the PageRank scores
    scores = nx.pagerank(sentence_similarity_graph)

    # rank the sentences based on their scores
    ranked_sentences = sorted(((scores[i], s) for i, s in enumerate(sentence_list)), reverse=True)

    # get the top 3 sentences
    summary = []
    for i in range(3):
        summary.append(ranked_sentences[i][1])

    summary = ' '.join(summary)
    return summary
