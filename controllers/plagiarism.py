import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple, Any

# Define the default threshold for Jaccard similarity
DEFAULT_JACCARD_THRESHOLD = 0.5  # Example value, adjust as needed


def process_documents(
    original_text: str, check_text: str, threshold: float = DEFAULT_JACCARD_THRESHOLD
) -> Tuple[float, List[str]]:
    """
    Process two documents to calculate the plagiarism percentage based on cosine similarity.

    Args:
        original_text (str): The original document text to check against.
        check_text (str): The document text that is being checked for plagiarism.
        threshold (float): The threshold for cosine similarity above which a sentence is considered plagiarized.

    Returns:
        Tuple[float, List[str]]: A tuple containing the plagiarism percentage and a list of plagiarized sentences.
    """
    try:
        # Edge case handling for empty documents
        if not original_text or not check_text:
            print("Error: One or both documents are empty.")
            return 0, []

        # Tokenize sentences
        original_sentences = re.split(r"(?<=[.!?]) +", original_text)
        check_sentences = re.split(r"(?<=[.!?]) +", check_text)

        # Edge case handling for documents with no valid sentences
        if not original_sentences or not check_sentences:
            print("Error: No valid sentences found in one or both documents.")
            return 0, []

        # Vectorization using TF-IDF
        vectorizer = TfidfVectorizer()
        all_sentences = original_sentences + check_sentences
        tfidf_matrix = vectorizer.fit_transform(all_sentences)

        # Split the TF-IDF matrix into original and check matrices
        original_vector = tfidf_matrix[: len(original_sentences)]
        check_vector = tfidf_matrix[len(original_sentences) :]

        plagiarized_sentences = []
        for i, check_sentence in enumerate(check_sentences):
            # Calculate cosine similarity between the check sentence and all original sentences
            similarity = cosine_similarity(check_vector[i], original_vector).flatten()

            # Use the configurable threshold for plagiarism detection
            if np.any(similarity > threshold):
                plagiarized_sentences.append(check_sentence)

        plagiarism_percentage = (
            (len(plagiarized_sentences) / len(check_sentences)) * 100
            if check_sentences
            else 0
        )

        return plagiarism_percentage, plagiarized_sentences

    except Exception as e:
        print(f"Error processing documents: {e}")
        return 0, []  # Return zero plagiarism and empty list on error
