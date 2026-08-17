from pathlib import Path

from haystack.components.converters import PyPDFToDocument
from haystack.components.preprocessors import (
    DocumentCleaner,
    DocumentSplitter,
)


def convert_pdf(file_path: str):
    """
    Convert a PDF file into Haystack Document objects.
    """

    #pdf_path = Path("data/sample.pdf")
    pdf_path = Path(file_path)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF file was not found: {pdf_path}"
        )

    converter = PyPDFToDocument()

    result = converter.run(
        sources=[pdf_path]
    )

    documents = result["documents"]

    return documents

def clean_documents(documents):
    """
    Clean extracted document text.
    """

    cleaner = DocumentCleaner(
        remove_empty_lines=True,
        remove_extra_whitespaces=True,
    )

    result = cleaner.run(
        documents=documents
    )

    cleaned_documents = result["documents"]

    return cleaned_documents

def split_documents(documents):
    """
    Split documents into smaller overlapping chunks.
    """

    splitter = DocumentSplitter(
        split_by="word",
        split_length=50,
        split_overlap=7,
    )

    result = splitter.run(
        documents=documents
    )

    chunks = result["documents"]

    return chunks


def process_pdf(file_path: str):
    """
    Complete PDF preprocessing flow.

    PDF
      -> conversion
      -> cleaning
      -> chunking
    """

    documents = convert_pdf(
        file_path
    )

    cleaned_documents = clean_documents(
        documents
    )

    chunks = split_documents(
        cleaned_documents
    )

    return chunks