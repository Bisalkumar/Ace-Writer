import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
import heapq
import logging
from collections import Counter

stopWords = set(stopwords.words("english"))


def nltk_summarizer(raw_text, max_sentence_length=30, num_sentences=3):
    if not raw_text:
        raise ValueError("Input text cannot be empty.")

    word_frequencies = Counter(
        word for word in word_tokenize(raw_text) if word not in stopWords
    )

    maximum_frequency = max(word_frequencies.values(), default=1)

    # Normalize word frequencies
    for word in word_frequencies.keys():
        word_frequencies[word] /= maximum_frequency

    sentence_list = sent_tokenize(raw_text)
    sentence_scores = {}

    for sent in sentence_list:
        for word in word_tokenize(sent.lower()):
            if word in word_frequencies and len(sent.split(" ")) < max_sentence_length:
                sentence_scores[sent] = (
                    sentence_scores.get(sent, 0) + word_frequencies[word]
                )

    summary_sentences = heapq.nlargest(
        num_sentences, sentence_scores, key=sentence_scores.get
    )

    summary = " ".join(summary_sentences)
    return summary
