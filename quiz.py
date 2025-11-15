import google.generativeai as genai
from langchain.text_splitter import RecursiveCharacterTextSplitter
import PyPDF2
import io

def extract_text_from_pdf(pdf_bytes):
    pdf_file = io.BytesIO(pdf_bytes)
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def generate_flashcards(notes_text, num_cards=10):
    prompt = f"""Create {num_cards} flashcards from these notes:
    {notes_text}
    
    Format:
    Front: [question/concept]
    Back: [answer/explanation]
    XP: [10 points each]
    """
    
    response = genai.GenerativeModel('gemini-1.5-flash').generate_content(prompt)
    return parse_flashcards(response.text)

def parse_quiz_response(quiz_text):
    # Parse Gemini response into structured quiz format
    questions = []
    # Add parsing logic here
    return questions
