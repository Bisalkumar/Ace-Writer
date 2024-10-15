import nltk
from nltk.corpus import stopwords
import numpy as np
import spacy
import networkx as nx
import logging
from collections import Counter

# Load SpaCy's English language model
nlp = spacy.load("en_core_web_lg")

# Define stop words once at the module level
stop_words = set(stopwords.words("english"))


def sentence_similarity(sent1, sent2):
    """Calculates similarity between two sentences."""
    sent1 = nlp(sent1)
    sent2 = nlp(sent2)
    return sent1.similarity(sent2)


def luhn_summarizer(text, num_sentences=3):
    if not text:
        raise ValueError("Input text cannot be empty.")

    sentence_list = nltk.sent_tokenize(text)
    new_words = [
        [
            word
            for word in nltk.word_tokenize(sentence)
            if word.lower() not in stop_words
        ]
        for sentence in sentence_list
    ]

    # Create word frequency dictionary
    word_frequencies = Counter(word for sentence in new_words for word in sentence)

    # Calculate sentence scores based on word frequencies
    sentence_scores = {
        i: sum(word_frequencies[word] for word in sentence)
        for i, sentence in enumerate(new_words)
    }

    # Create the similarity matrix
    similarity_matrix = np.zeros((len(sentence_list), len(sentence_list)))
    for i in range(len(sentence_list)):
        for j in range(len(sentence_list)):
            if i != j:
                similarity_matrix[i][j] = sentence_similarity(
                    sentence_list[i], sentence_list[j]
                )

    # Create the sentence similarity graph
    sentence_similarity_graph = nx.from_numpy_array(similarity_matrix)

    # Calculate the PageRank scores
    scores = nx.pagerank(sentence_similarity_graph)

    # Rank the sentences based on their scores
    ranked_sentences = sorted(
        ((scores[i], s) for i, s in enumerate(sentence_list)), reverse=True
    )

    # Get the top sentences
    summary = [
        ranked_sentences[i][1] for i in range(min(num_sentences, len(ranked_sentences)))
    ]
    return " ".join(summary)
