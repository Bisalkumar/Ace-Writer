from __future__ import unicode_literals

import logging
import openai
import time
import spacy
import PyPDF2
import nltk
import io
import subprocess
import os

from flask import Flask, render_template, request, send_file
from typing import List, Tuple
from bs4 import BeautifulSoup
from urllib.request import urlopen
from io import StringIO
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer
from controllers.spacy_summarization import text_summarizer
from controllers.nltk_summarization import nltk_summarizer
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize
from img2pdf import convert as convert_image_to_pdf
from PIL import Image
from docx2pdf import convert as docx2pdf_convert
from PyPDF2 import PdfReader, PdfWriter, PdfMerger

from controllers.spacy_summarization import text_summarizer
from controllers.nltk_summarization import nltk_summarizer
from controllers.luhn_summarization import luhn_summarizer
from controllers.gpt_summarization import openai_summarizer

nlp = spacy.load("en_core_web_sm")

app = Flask(__name__, static_url_path='/static', static_folder='static')
app.config['LOG_LEVEL'] = logging.DEBUG

openai.api_key = "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"


# Sumy
def sumy_summary(docx: str) -> str:
    parser = PlaintextParser.from_string(docx, Tokenizer("english"))
    lex_summarizer = LexRankSummarizer()
    summary = lex_summarizer(parser.document, 3)
    summary_list = [str(sentence) for sentence in summary]
    result = ' '.join(summary_list)
    return result


# Reading Time
def readingTime(mytext: str) -> float:
    total_words = len([token.text for token in nlp(mytext)])
    estimated_time = total_words/200.0
    return estimated_time


# Fetch Text From Url
def get_text(url: str) -> str:
    page = urlopen(url)
    soup = BeautifulSoup(page)
    fetched_text = ' '.join(map(lambda p: p.text, soup.find_all('p')))
    return fetched_text


# Extract text from PDF
def extract_text(docx: str) -> str:
    pdfFileObj = open(docx, 'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    total_pages = pdfReader.numPages
    text = ''
    for page in range(total_pages):
        pageObj = pdfReader.getPage(page)
        text += pageObj.extractText()
    return text 


@app.route('/')
def home():
    return render_template('home.html')

#->
@app.route('/index')
def index():
	return render_template('index.html')

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    start = time.time()
    if request.method == 'POST':
        rawtext = request.form['rawtext']
        final_reading_time = readingTime(rawtext)
        # Text summarization - GPT3
        final_summary = text_summarizer(rawtext)
        summary_reading_time = readingTime(final_summary)
        end = time.time()
        final_time = end-start
    return render_template('index.html', ctext=rawtext, final_summary=final_summary, final_time=final_time, final_reading_time=final_reading_time, summary_reading_time=summary_reading_time)



@app.route('/analyze_url', methods=['GET', 'POST'])
def analyze_url():
    start = time.time()
    if request.method == 'POST':
        raw_url = request.form['raw_url']
        rawtext = get_text(raw_url)
        final_reading_time = readingTime(rawtext)
        # Text summarization - GPT3
        final_summary = text_summarizer(rawtext)
        summary_reading_time = readingTime(final_summary)
        end = time.time()
        final_time = end-start
    return render_template('index.html', ctext=rawtext, final_summary=final_summary, final_time=final_time, final_reading_time=final_reading_time, summary_reading_time=summary_reading_time)



@app.route('/analyze_pdf', methods=['GET', 'POST'])
def analyze_pdf():
    start = time.time()
    if request.method == 'POST':
        pdf_file = request.files['pdf_file']
        file_contents = StringIO()
        file_contents.write(pdf_file.read().decode('utf-8'))
        rawtext = extract_text(file_contents)
        final_reading_time = readingTime(rawtext)
        final_summary = text_summarizer(rawtext)
        summary_reading_time = readingTime(final_summary)
        end = time.time()
        final_time = end-start
    return render_template('index.html', ctext=rawtext, final_summary=final_summary, final_time=final_time, final_reading_time=final_reading_time, summary_reading_time=summary_reading_time)

#<-

#-->

@app.route('/compare_summary')
def compare_summary():
    return render_template('compare_summary.html')


@app.route('/comparer',methods=['GET','POST'])
def comparer():
	start = time.time()
	if request.method == 'POST':
		rawtext = request.form['rawtext']
		final_reading_time = readingTime(rawtext)
		final_summary_spacy = text_summarizer(rawtext)
		summary_reading_time = readingTime(final_summary_spacy)
		# Gpt-3 Summarizer
		final_summary_gpt = openai_summarizer(rawtext)
		summary_reading_time_gpt = readingTime(final_summary_gpt)
		# NLTK
		final_summary_nltk = nltk_summarizer(rawtext)
		summary_reading_time_nltk = readingTime(final_summary_nltk)
		# LUHN
		final_summary_luhn = luhn_summarizer(rawtext)
		summary_reading_time_luhn = readingTime(final_summary_luhn)  

		end = time.time()
		final_time = end-start
	return render_template('compare_summary.html',ctext=rawtext,final_summary_spacy=final_summary_spacy,final_summary_gpt=final_summary_gpt,final_summary_nltk=final_summary_nltk,final_time=final_time,final_reading_time=final_reading_time,summary_reading_time=summary_reading_time,summary_reading_time_gpt=summary_reading_time_gpt,final_summary_sumy=final_summary_luhn,summary_reading_time_sumy=summary_reading_time_luhn,summary_reading_time_nltk=summary_reading_time_nltk)


#<--

#-->

@app.route('/essaygrader', methods=['GET', 'POST'])
def essaygrader():
    if request.method == 'GET':
        # Display input form
        return render_template('essaygrader.html')
    else:
        # Grade the essay
        essay = request.form['essay']
        sentences = sent_tokenize(essay)
        words = nltk.word_tokenize(essay)
        stop_words = set(stopwords.words("english"))
        words = [word for word in words if word.casefold() not in stop_words]
        num_words = len(words)
        num_sentences = len(sentences)
        avg_sentence_length = num_words / num_sentences
        grade_level = 0.39 * avg_sentence_length + 11.8 * (len(words) / num_sentences) - 15.59
        grade_percentage = round(((grade_level - 1) / 15) * 100)
        grade_letter = chr(ord('A') + min(4, grade_percentage // 10))
        feedbacks = []
        if grade_level >= 13:
            feedbacks.append("Your essay is very advanced.")
        elif grade_level >= 10:
            feedbacks.append("Your essay is at a high school reading level.")
        elif grade_level >= 7:
            feedbacks.append("Your essay is at a middle school reading level.")
        else:
            feedbacks.append("Your essay is at an elementary school reading level.")
        if 'essay' in words:
            feedbacks.append("Try to use more synonyms instead of repeating the word 'essay'.")
        feedbacks_str = ''.join(['<li>{}</li>'.format(feedback) for feedback in feedbacks])

        # Display graded result
        return render_template('essaygrader.html', grade_percentage=grade_percentage, grade_letter=grade_letter, feedbacks_str=feedbacks_str)
    
#<--

#--->

def word_to_pdf(word_file_path):
    output_pdf_file_path = os.path.join(app.root_path, 'output_files', os.path.splitext(
        os.path.basename(word_file_path))[0] + '.pdf')
    docx2pdf_convert(word_file_path, output_pdf_file_path)
    return output_pdf_file_path


def pdf_to_word(pdf_file_path):
    pdf_reader = PdfReader(open(pdf_file_path, "rb"))
    output_word_file_path = os.path.join(app.root_path, 'output_files', os.path.splitext(
        os.path.basename(pdf_file_path))[0] + '.docx')
    pdf_writer = PdfWriter()
    annotations = []
    for page in range(len(pdf_reader.pages)):
        annotations += [pdf_reader.pages[page].extract_text()]
    pdf_writer.add_page(pdf_reader.pages[0])
    with open(output_word_file_path, 'wb') as output:
        pdf_writer.write(output)
    return output_word_file_path


def image_to_pdf(image_file_path):
    subprocess.call(['convert', image_file_path, os.path.join(
        app.root_path, 'output_files', os.path.splitext(os.path.basename(image_file_path))[0] + '.pdf')])
    output_pdf_file_path = os.path.join(app.root_path, 'output_files', os.path.splitext(
        os.path.basename(image_file_path))[0] + '.pdf')
    return output_pdf_file_path


def pdf_to_image(pdf_file_path):
    subprocess.call(['convert', '-density', '150', '-quality', '90', pdf_file_path, os.path.join(
        app.root_path, 'output_files', os.path.splitext(os.path.basename(pdf_file_path))[0] + '.png')])
    output_image_file_path = os.path.join(app.root_path, 'output_files', os.path.splitext(
        os.path.basename(pdf_file_path))[0] + '.png')
    return output_image_file_path


def word_to_image(word_file_path):
    pdf_file_path = word_to_pdf(word_file_path)
    return pdf_to_image(pdf_file_path)


@app.route('/file_converter')
def file_converter():
    return render_template('file_converter.html')


@app.route('/converted', methods=['POST'])
def convert():
    if not os.path.exists('input_files'):
        os.makedirs('input_files')
    file = None  # set initial value to None
    if 'file' in request.files:  # check if file was uploaded
        file = request.files['file']
    conversion_type = request.form['conversion_type']
    if file:
        # continue with file processing
        input_file_path = os.path.join(
            app.root_path, 'input_files', file.filename)
        file.save(input_file_path)
        if conversion_type == 'word_to_pdf':
            converted_file_path = word_to_pdf(input_file_path)
        elif conversion_type == 'pdf_to_word':
            converted_file_path = pdf_to_word(input_file_path)
        elif conversion_type == 'image_to_pdf':
            converted_file_path = image_to_pdf(input_file_path)
        elif conversion_type == 'pdf_to_image':
            converted_file_path = pdf_to_image(input_file_path)
        elif conversion_type == 'word_to_image':
            converted_file_path = word_to_image(input_file_path)
        else:
            return 'Invalid conversion type'
        # create download link for the converted file
        download_link = f'/download?file={os.path.basename(converted_file_path)}'
        return render_template('converted.html', download_link=download_link)
    else:
        return 'No file selected'


@app.route('/download')
def download():
    file_name = request.args.get('file')
    file_path = os.path.join(app.root_path, 'output_files', file_name)
    return send_file(file_path, as_attachment=True)


#<---
@app.route('/plagarism')
def plagarism():
    return render_template('plagarism.html')

#<---


#---->
@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')
#<----




if __name__ == '__main__':
    app.run(debug=True)