from heapq import nlargest
from spacy.lang.en.stop_words import STOP_WORDS
import spacy
import logging
from collections import Counter

# Load SpaCy's English model
nlp = spacy.load("en_core_web_lg")


def text_summarizer(raw_docx, num_sentences=7, max_sentence_length=30):
    if not raw_docx:
        raise ValueError("Input text cannot be empty.")

    docx = nlp(raw_docx)
    stopwords = list(STOP_WORDS)

    # Build Word Frequency
    word_frequencies = Counter(word.text for word in docx if word.text not in stopwords)

    maximum_frequency = max(word_frequencies.values(), default=1)

    # Normalize frequencies
    for word in word_frequencies.keys():
        word_frequencies[word] /= maximum_frequency

    # Sentence Tokens
    sentence_list = [sentence for sentence in docx.sents]

    # Sentence Scores
    sentence_scores = {}
    for sent in sentence_list:
        for word in sent:
            if (
                word.text.lower() in word_frequencies
                and len(sent.text.split(" ")) < max_sentence_length
            ):
                sentence_scores[sent] = (
                    sentence_scores.get(sent, 0) + word_frequencies[word.text.lower()]
                )

    summarized_sentences = nlargest(
        num_sentences, sentence_scores, key=sentence_scores.get
    )
    final_sentences = [w.text for w in summarized_sentences]
    summary = " ".join(final_sentences)

    return summary
