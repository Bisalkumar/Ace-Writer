from __future__ import unicode_literals

# Standard library imports
import os
import logging
import tempfile
import time
import concurrent.futures
from functools import wraps

# Third-party imports
import textstat
import spacy
from flask import Flask, render_template, request, send_file, jsonify, abort
from dotenv import load_dotenv
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import validators

# Local application/library-specific imports
from controllers.spacy_summarization import text_summarizer
from controllers.nltk_summarization import nltk_summarizer
from controllers.luhn_summarization import luhn_summarizer
from controllers.gpt_summarization import openai_summarizer
from controllers.plagiarism import process_documents
from utils import (
    get_text,
    setup_logging,
    extract_text,
    allowed_file,
    validate_file_size,
    reading_time,
    run_summarizer,
    word_to_pdf,
    pdf_to_word,
    image_to_pdf,
    pdf_to_image,
    word_to_image,
)

# Load environment variables
load_dotenv()

# Set up OpenAI API key
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("API key not found. Set the OPENAI_API_KEY environment variable.")

# Set up logging
logger = setup_logging()

# Create Flask application
app = Flask(__name__, static_url_path="/static", static_folder="static")
app.config["LOG_LEVEL"] = logging.DEBUG


# Utility function for error responses
def handle_error(message, code=400):
    logger.error(message)
    return render_template("error.html", message=message), code


# Error Handling
@app.before_request
def before_request():
    """Before every request, log basic info."""
    logger.debug("Request Method: %s, Path: %s", request.method, request.path)
    if request.method == "POST":
        if not request.files and not request.form:
            return handle_error("No input data provided.")


@app.errorhandler(404)
def not_found_error(error):
    return handle_error("Page not found! Please check the URL.", 404)


@app.errorhandler(500)
def internal_error(error):
    return handle_error("An internal error occurred! Please try again later.", 500)


@app.errorhandler(400)
def bad_request_error(error):
    return handle_error(str(error), 400)


def validate_url(url):
    """Validate URL format."""
    if not validators.url(url):
        raise ValueError("Invalid URL provided.")


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/index")
def index():
    return render_template("index.html")


@app.route("/aboutus")
def aboutus():
    return render_template("aboutus.html")


@app.route("/download")
def download():
    # Serve a downloadable file (example: a user manual or report)
    file_path = os.path.join(
        app.root_path, "static", "example_manual.pdf"
    )  # Example path
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return handle_error("Requested file not found.", 404)


@app.route("/analyze", methods=["GET", "POST"])
def analyze():
    start = time.time()
    rawtext = request.form.get("rawtext", "")
    if not rawtext:
        return handle_error("No text provided for analysis.")

    final_reading_time = reading_time(rawtext)
    final_summary = text_summarizer(rawtext)
    summary_reading_time = reading_time(final_summary)
    final_time = time.time() - start

    return render_template(
        "index.html",
        ctext=rawtext,
        final_summary=final_summary,
        final_time=final_time,
        final_reading_time=final_reading_time,
        summary_reading_time=summary_reading_time,
    )


@app.route("/analyze_url", methods=["GET", "POST"])
def analyze_url():
    start = time.time()
    raw_url = request.form.get("raw_url", "")
    if not raw_url:
        return handle_error("No URL provided for analysis.")

    try:
        validate_url(raw_url)
        rawtext = get_text(raw_url)
    except ValueError as e:
        return handle_error(str(e))

    final_reading_time = reading_time(rawtext)
    final_summary = text_summarizer(rawtext)
    summary_reading_time = reading_time(final_summary)
    final_time = time.time() - start

    return render_template(
        "index.html",
        ctext=rawtext,
        final_summary=final_summary,
        final_time=final_time,
        final_reading_time=final_reading_time,
        summary_reading_time=summary_reading_time,
    )


@app.route("/analyze_pdf", methods=["POST"])
def analyze_pdf():
    start = time.time()
    if "pdf_file" not in request.files:
        return handle_error("No file uploaded.")

    pdf_file = request.files["pdf_file"]
    if pdf_file.filename == "":
        return handle_error("No file selected for upload.")

    if pdf_file and allowed_file(pdf_file.filename) and validate_file_size(pdf_file):
        file_path = os.path.join(app.root_path, "input_files", pdf_file.filename)
        pdf_file.save(file_path)

        rawtext = extract_text(file_path)
        if rawtext:
            final_reading_time = reading_time(rawtext)
            final_summary = text_summarizer(rawtext)
            summary_reading_time = reading_time(final_summary)
            final_time = time.time() - start  # Ensure 'start' is defined

            return render_template(
                "index.html",
                ctext=rawtext,
                final_summary=final_summary,
                final_time=final_time,
                final_reading_time=final_reading_time,
                summary_reading_time=summary_reading_time,
            )

    return handle_error("Invalid file format or size. Please upload a valid PDF file.")


@app.route("/compare_summary")
def compare_summary():
    return render_template("compare_summary.html")


@app.route("/comparer", methods=["POST"])
def comparer():
    rawtext = request.form["rawtext"]
    final_reading_time = reading_time(rawtext)

    results = {}
    summarizers = [text_summarizer, nltk_summarizer, luhn_summarizer, openai_summarizer]

    # Use ThreadPoolExecutor for concurrent summarization
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(run_summarizer, summarizer, rawtext): summarizer.__name__
            for summarizer in summarizers
        }

        for future in concurrent.futures.as_completed(futures):
            summarizer_name = futures[future]
            try:
                summary, processing_time, reading_time_summary = future.result()
                results[summarizer_name] = {
                    "summary": summary,
                    "processing_time": processing_time,
                    "reading_time": reading_time_summary,
                }
            except Exception as e:
                # Capture any errors that occur during the summarization
                results[summarizer_name] = {
                    "summary": f"Error: {str(e)}",
                    "processing_time": 0,
                    "reading_time": 0,
                }

    return render_template(
        "compare_summary.html",
        rawtext=rawtext,
        final_reading_time=final_reading_time,
        final_summary_gpt=results.get("openai_summarizer", {}).get("summary", ""),
        summary_reading_time_gpt=results.get("openai_summarizer", {}).get(
            "reading_time", 0
        ),
        processing_time_gpt=results.get("openai_summarizer", {}).get(
            "processing_time", 0
        ),
        final_summary_nltk=results.get("nltk_summarizer", {}).get("summary", ""),
        summary_reading_time_nltk=results.get("nltk_summarizer", {}).get(
            "reading_time", 0
        ),
        processing_time_nltk=results.get("nltk_summarizer", {}).get(
            "processing_time", 0
        ),
        final_summary_spacy=results.get("text_summarizer", {}).get("summary", ""),
        summary_reading_time_spacy=results.get("text_summarizer", {}).get(
            "reading_time", 0
        ),
        processing_time_spacy=results.get("text_summarizer", {}).get(
            "processing_time", 0
        ),
        final_summary_luhn=results.get("luhn_summarizer", {}).get("summary", ""),
        summary_reading_time_luhn=results.get("luhn_summarizer", {}).get(
            "reading_time", 0
        ),
        processing_time_luhn=results.get("luhn_summarizer", {}).get(
            "processing_time", 0
        ),
    )


@app.route("/essaygrader", methods=["GET", "POST"])
def essaygrader():
    if request.method == "POST":
        essay = request.form.get("essaytext", "")
        if not essay:
            app.logger.warning("No essay text provided")
            return render_template("error.html", message="No essay text provided.")

        # Tokenization and initial analysis
        sentences = sent_tokenize(essay)
        words = word_tokenize(essay)
        stop_words = set(stopwords.words("english"))
        filtered_words = [word for word in words if word.casefold() not in stop_words]

        num_words = len(filtered_words)
        num_sentences = len(sentences)
        avg_sentence_length = num_words / num_sentences if num_sentences > 0 else 0

        # Grade level calculation
        grade_level = (
            0.39 * avg_sentence_length + 11.8 * (num_words / num_sentences) - 15.59
        )
        grade_level = max(0, min(grade_level, 15))  # Clamp between 0 and 15

        # Calculate grade percentage
        grade_percentage = round(
            ((grade_level) / 15) * 100
        )  # Ensure it does not exceed 100%

        # Readability Scores
        readability_score = textstat.textstat.flesch_kincaid_grade(essay)
        fk_grade = textstat.textstat.flesch_reading_ease(essay)

        # Suggestions for improvement
        suggestions = []

        # Sentence Length Improvement
        if avg_sentence_length < 10:
            suggestions.append(
                "Consider varying your sentence lengths. Longer, more complex sentences can demonstrate more sophisticated writing skills. Try to use a mix of short and long sentences to enhance readability."
            )
        elif avg_sentence_length > 20:
            suggestions.append(
                "Try to break down long sentences into shorter ones to improve readability and clarity. Use punctuation effectively to separate ideas and make your writing more accessible."
            )

        # Word Choice Improvement
        if len(filtered_words) / num_words < 0.6:
            suggestions.append(
                "Use a more diverse vocabulary to make your writing more engaging and precise. Avoid repetition and try to use synonyms to keep your writing fresh."
            )

        # Grammar and Clarity Improvement
        suggestions.append(
            "Ensure your grammar and punctuation are correct. Proofread your essay to eliminate errors and improve clarity. Consider using grammar-checking tools or having someone review your work."
        )

        # Overall Structure
        if num_sentences < 5:
            suggestions.append(
                "Your essay may benefit from a more structured approach. Consider breaking it into paragraphs with clear topic sentences and transitions to improve flow and organization."
            )

        # Readability
        if readability_score < 50:
            suggestions.append(
                f"Your essay's readability score is {readability_score:.2f}. Consider simplifying complex sentences and using more common words to improve readability."
            )

        if fk_grade > grade_level:
            suggestions.append(
                f"Your essay's Flesch-Kincaid grade level is {fk_grade:.2f}. Consider using simpler language and shorter sentences to better match the intended grade level."
            )

        return jsonify(
            {
                "grade_level": round(grade_level, 2),
                "grade_percentage": grade_percentage,
                "readability_score": readability_score,
                "fk_grade": fk_grade,
                "suggestions": suggestions,
            }
        )
    else:
        return render_template("essaygrader.html")


@app.route("/file_converter")
def file_converter_page():
    """Render the file converter page."""
    return render_template("file_converter.html")


@app.route("/file_converter", methods=["GET", "POST"])
def file_converter():
    """Handle file conversion requests."""
    if request.method == "POST":
        try:
            # Check for file in the request
            if "file" not in request.files:
                raise ValueError("No file uploaded.")

            file = request.files["file"]

            # Validate file selection
            if file.filename == "":
                raise ValueError("No file selected for upload.")
            if not allowed_file(file.filename):
                raise ValueError("Invalid file type provided.")
            if not validate_file_size(file):
                raise ValueError("File size exceeds the allowed limit.")

            # Save the uploaded file
            file_path = os.path.join(app.root_path, "input_files", file.filename)
            file.save(file_path)

            # Determine output file based on input file type
            if file.filename.endswith(".docx"):
                output_file_path = word_to_pdf(file_path)
            elif file.filename.endswith(".pdf"):
                output_file_path = pdf_to_word(file_path)
            elif file.filename.endswith((".png", ".jpg", ".jpeg")):
                output_file_path = image_to_pdf(file_path)
            else:
                raise ValueError("Unsupported file type.")

            return send_file(output_file_path, as_attachment=True)

        except Exception as e:
            logger.error(f"File conversion failed: {e}")  # Use the centralized logger
            return render_template("error.html", message=str(e))

    return render_template("file_converter.html")


@app.route("/plagiarism", methods=["GET", "POST"])
def plagiarism():
    """Handle plagiarism check requests."""
    if request.method == "POST":
        try:
            # Check for files in the request
            if "original" not in request.files or "check" not in request.files:
                return handle_error("No file part", 400)

            original_file = request.files["original"]
            check_file = request.files["check"]
            threshold = request.form.get("threshold", type=float)

            # Validate file selections
            if original_file.filename == "" or check_file.filename == "":
                return handle_error("No selected file", 400)

            if not original_file.filename.lower().endswith(
                ".pdf"
            ) or not check_file.filename.lower().endswith(".pdf"):
                return handle_error(
                    "Only PDF files are supported for plagiarism check", 400
                )

            # Create temporary files for the original and check files
            with tempfile.NamedTemporaryFile(
                delete=False
            ) as original_temp, tempfile.NamedTemporaryFile(delete=False) as check_temp:
                original_temp.write(original_file.read())
                check_temp.write(check_file.read())
                original_file_path = original_temp.name
                check_file_path = check_temp.name

            # Extract text from the PDF files
            original_text = extract_text(original_file_path)
            check_text = extract_text(check_file_path)

            # Handle text extraction errors
            if (
                "Error extracting text" in original_text
                or "Error extracting text" in check_text
            ):
                return handle_error(
                    f"Error extracting text from files: {original_text} or {check_text}",
                    400,
                )

            # Process plagiarism check
            plagiarism_percentage, plagiarized_sentences = process_documents(
                original_text, check_text, threshold
            )

            return jsonify(
                {
                    "plagiarism_percentage": plagiarism_percentage,
                    "plagiarized_sentences": plagiarized_sentences,
                }
            )

        except Exception as e:
            logger.error(
                f"Error processing plagiarism check: {e}"
            )  # Use centralized logger
            return handle_error("An error occurred during plagiarism checking.", 500)

    # Render the plagiarism checking page for GET requests
    return render_template("plagiarism.html")


if __name__ == "__main__":
    app.run(debug=True)
