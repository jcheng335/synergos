import os
import logging
import pypdf
import requests
from bs4 import BeautifulSoup

# Set up logging
logger = logging.getLogger(__name__)

def extract_text_from_document(filepath):
    """
    Extract text from various document types (PDF, DOC, DOCX, TXT)
    Returns the extracted text as a string
    """
    logger.info(f"Extracting text from file: {filepath}")
    filename = os.path.basename(filepath)
    file_extension = os.path.splitext(filename)[1].lower()

    try:
        # PDF File
        if file_extension == '.pdf':
            logger.info("Processing as PDF")
            pdf = pypdf.PdfReader(filepath)
            content = ""
            number_of_pages = len(pdf.pages)
            for idx in range(number_of_pages):
                page = pdf.pages[idx]
                content += f"### Page {idx+1} ###\n"
                content += page.extract_text()
            return content

        # Word Document (.doc, .docx)
        elif file_extension in ['.doc', '.docx']:
            logger.info("Processing as Word document")
            try:
                import docx2txt  # For .docx files
                content = docx2txt.process(filepath)
                if content.strip():
                    return content
            except ImportError:
                logger.warning("docx2txt not installed, trying python-docx")
            except Exception as e:
                logger.warning(f"docx2txt failed: {str(e)}, trying other methods")

            # If docx2txt fails or returns empty content, try python-docx (for .docx files)
            try:
                from docx import Document
                doc = Document(filepath)
                content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                if content.strip():
                    return content
            except ImportError:
                logger.warning("python-docx not installed, trying textract")
            except Exception as e:
                logger.warning(f"python-docx failed: {str(e)}, trying other methods")

            # If both methods fail or it's a .doc file, try textract as a fallback
            try:
                import textract
                content = textract.process(filepath).decode('utf-8')
                return content
            except ImportError:
                logger.error("textract not installed")
                raise ValueError("No suitable library installed to extract text from Word documents")
            except Exception as e:
                logger.error(f"All Word extraction methods failed: {str(e)}")
                raise ValueError(f"Could not extract text from Word document: {str(e)}")

        # Text file
        elif file_extension in ['.txt', '.text', '.md', '.rtf']:
            logger.info("Processing as text file")
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return content

        # Unsupported file type
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")

    except Exception as e:
        logger.error(f"Error extracting text from {filepath}: {str(e)}")
        raise


def extract_text_from_url(url):
    """
    Extract text content from a URL
    Handles job postings, articles, and other web content
    """
    logger.info(f"Extracting text from URL: {url}")
    
    try:
        # Send a GET request to the URL
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        
        # Get text
        text = soup.get_text(separator='\n')
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        logger.info(f"Successfully extracted text from URL: {url}")
        return text
        
    except Exception as e:
        logger.error(f"Error extracting text from URL {url}: {str(e)}")
        raise ValueError(f"Failed to extract text from URL: {str(e)}")


def clean_text(text):
    """Clean and normalize text for analysis"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove special characters (keeping alphanumeric, punctuation, and whitespace)
    # This is a basic cleanup - may need adjustment based on requirements
    
    return text 