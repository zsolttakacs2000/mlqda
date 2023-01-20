import PyPDF2
import docx
import os
import time

from django.conf import settings

from mlqda.models import FileCollector, FileContainer


def read_txt(file_path):
    """
    utility function to read in a txt file and return the contents of the file
    """
    with open(file_path, 'r', encoding="utf8") as f:
        text = f.read().replace('\n', ' ')
        return text


def read_pdf(file_path):
    """
    utility function to read in a pdf file and return the contents of the file
    """
    document = []
    pdf_file = open(file_path, 'rb')
    pdf_reader = PyPDF2.PdfFileReader(pdf_file)

    for page in range(pdf_reader.numPages):
        page_object = pdf_reader.getPage(page)
        page_text = page_object.extractText()
        document.append(page_text)

    pdf_file.close()
    text = " ".join(document)
    return text


def read_docx(file_path):
    """
    utility function to read in a .docx file and return the contents of the file
    """
    document = docx.Document(file_path)
    document_text = []

    for paragraph in document.paragraphs:
        document_text.append(paragraph.text)

    text = ' '.join(document_text)
    return text


def get_datafiles(path_list):
    """
    utility function to read in a list of files and return all their content
    """
    full_text = []
    for file_path in path_list:
        if file_path.endswith(".txt"):
            text = read_txt(file_path)
        elif file_path.endswith(".pdf"):
            text = read_pdf(file_path)
        elif file_path.endswith(".docx"):
            text = read_docx(file_path)

        full_text.append(text)

    return full_text


def get_test_files(extension=".txt"):
    """
    Utility function to return all the available files in the test folder.
    Automatically filters for txt files, but passing an empty strings returns all the files.txt

    @param extension: string representation of the required extension of files to return
    @return: A list of paths
    """
    test_path = os.path.relpath(settings.TEST_DIR, start=os.curdir)
    test_paths = []
    for file in sorted(os.listdir(test_path)):
        file_path = os.path.join(test_path, file)
        if os.path.isfile(file_path) and file_path.endswith(extension):
            test_paths.append(file_path)
    return test_paths


def delete_all_uploaded_files():
    """
    Utility function to gather all files and delete them if they are older than 10 minutes.
    """
    collectors = FileCollector.objects.all()
    print("deleted files:")

    for collector in collectors:
        files = FileContainer.objects.filter(first_name=collector)

        for file in files:
            if os.path.exists(str(file.file)):
                creation = os.path.getmtime(str(file.file))
                current = time.time()
                age = (current - creation)/60
                if age > 10:
                    print(str(file.file))
                    os.remove(str(file.file))
                    file.delete()
                    collector.delete()
