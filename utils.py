from __future__ import unicode_literals
import os
import time
import subprocess
import concurrent.futures

import logging  # <-- Add this import
from logging import handlers  # <-- Also ensure this is imported
from flask import current_app as app
from docx2pdf import convert as docx2pdf_convert
from urllib.request import urlopen
from PyPDF2 import PdfReader, PdfWriter
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

import tempfile


# Function for setting up logging
def setup_logging():
    logger = logging.getLogger("AppLogger")
    logger.setLevel(logging.DEBUG)

    if not os.path.exists("logs"):
        os.makedirs("logs")

    handler = handlers.RotatingFileHandler(
        "logs/app.log", maxBytes=1000000, backupCount=5
    )
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


# Function for extracting text from PDFs
def extract_text(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text if text else "No text found in the PDF."
    except Exception as e:
        return f"Error extracting text: {str(e)}"


# File validation helpers
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {"pdf", "docx", "png", "jpg", "jpeg"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_file_size(file):
    MAX_FILE_SIZE_MB = 5
    file.seek(0, os.SEEK_END)
    file_size_mb = file.tell() / (1024 * 1024)
    file.seek(0)
    return file_size_mb <= MAX_FILE_SIZE_MB


# Reading time calculation
def reading_time(text):
    words_per_minute = 200
    num_words = len(text.split())
    return round(num_words / words_per_minute, 2)


# Utility to get text content from URL
def get_text(url):
    try:
        response = urlopen(url)
        soup = BeautifulSoup(response, "html.parser")
        return soup.get_text()
    except Exception as e:
        return f"Error fetching text from URL: {str(e)}"


# File conversion functions
def word_to_pdf(word_file_path):
    output_pdf_file_path = os.path.join(
        app.root_path,
        "output_files",
        os.path.splitext(os.path.basename(word_file_path))[0] + ".pdf",
    )
    docx2pdf_convert(word_file_path, output_pdf_file_path)
    return output_pdf_file_path


def pdf_to_word(pdf_file_path):
    pdf_reader = PdfReader(open(pdf_file_path, "rb"))
    output_word_file_path = os.path.join(
        app.root_path,
        "output_files",
        os.path.splitext(os.path.basename(pdf_file_path))[0] + ".docx",
    )
    pdf_writer = PdfWriter()
    annotations = []
    for page in range(len(pdf_reader.pages)):
        annotations += [pdf_reader.pages[page].extract_text()]
    pdf_writer.add_page(pdf_reader.pages[0])
    with open(output_word_file_path, "wb") as output:
        pdf_writer.write(output)
    return output_word_file_path


def image_to_pdf(image_file_path):
    output_pdf_file_path = os.path.join(
        app.root_path,
        "output_files",
        os.path.splitext(os.path.basename(image_file_path))[0] + ".pdf",
    )
    subprocess.call(
        [
            "convert",
            image_file_path,
            output_pdf_file_path,
        ]
    )
    return output_pdf_file_path


def pdf_to_image(pdf_file_path):
    output_image_file_path = os.path.join(
        app.root_path,
        "output_files",
        os.path.splitext(os.path.basename(pdf_file_path))[0] + ".png",
    )
    subprocess.call(
        [
            "convert",
            "-density",
            "150",
            "-quality",
            "90",
            pdf_file_path,
            output_image_file_path,
        ]
    )
    return output_image_file_path


def word_to_image(word_file_path):
    pdf_file_path = word_to_pdf(word_file_path)
    return pdf_to_image(pdf_file_path)


# Summarization helper
def run_summarizer(summarizer, text):
    try:
        start_time = time.time()
        summary = summarizer(text)
        processing_time = time.time() - start_time
        reading_time_summary = reading_time(summary)
        return summary, processing_time, reading_time_summary
    except Exception as e:
        return (
            f"Error occurred during summarization with {summarizer.__name__}: {str(e)}",
            0,
            0,
        )
