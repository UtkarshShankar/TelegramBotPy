import fitz  # PyMuPDF
import re
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    pdf_document = fitz.open(pdf_path)
    text = ""
    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        text += page.get_text() + "\n"
    return text.strip()

# Function to extract answers from text file
def extract_answers_from_text(txt_path):
    with open(txt_path, 'r', encoding='utf-8') as file:
        text = file.read()
    
    answer_pattern = re.findall(r'\[(\d+)\]\s*([A-D])', text)  # Extracts [6] A format
    return {int(q_num): ans for q_num, ans in answer_pattern}

# Process PDF text into question dictionary
def preprocess_text(text):
    questions = {}
    pattern = r'Question\s*#(\d+)\s*(.*?)\n(A\..*?\nB\..*?\nC\..*?\nD\..*?)\n'
    matches = re.findall(pattern, text, re.DOTALL)
    
    for q_num, q_text, choices in matches:
        q_num = int(q_num)
        questions[q_num] = {'question': q_text.strip(), 'choices': choices.strip()}
    
    return questions

def preprocess_text_v2(text):
    questions = {}
    pattern = r'NEW QUESTION\s*(\d+)\s*-\s*\(Topic\s*\d+\)\s*(.*?)\n(A\..*?\nB\..*?\nC\..*?\nD\..*?|E\..*?|F\..*?|G\..*?|H\..*?)\nAnswer:\s*([A-H])'
    matches = re.findall(pattern, text, re.DOTALL)
    
    for q_num, q_text, choices, answer in matches:
        q_num = int(q_num)
        questions[q_num] = {
            'question': q_text.strip(),
            'choices': choices.strip(),
            'answer': answer.strip()
        }
    
    return questions

# Linear search for matching question
def find_matching_question(query, questions, answers):
    query = query.lower()
    
    for q_num, q_data in questions.items():
        if query in q_data['question'].lower():
            answer = answers.get(q_num, 'Answer not available')
            return q_num, q_data['question'], q_data['choices'], answer
    
    return None

# Telegram bot handlers
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Send me a word or phrase, and I will find the matching question and answer from the PDF.')

async def handle_message(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text
    logger.info(f"Received user input: {user_input}")
    result = find_matching_question(user_input, questions, answers)
    
    if result:
        q_num, question, choices, answer = result
        response = f"✅ Found in PDF\nQuestion #{q_num}: {question}\n{choices}\n\nCorrect Answer: {answer}"
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("❌ Not found in PDF")

# Main function to run the bot
if __name__ == '__main__':
    pdf_path = 'questions.pdf'
    # pdf_path2 = 'questions2.pdf'
    txt_path = 'answers.txt'
    
    pdf_text = extract_text_from_pdf(pdf_path)
    # pdf_text2 = extract_text_from_pdf(pdf_path2)
    questions = preprocess_text(pdf_text)
    # questions2 = preprocess_text_v2(pdf_text2)
    answers = extract_answers_from_text(txt_path)
    
    application = Application.builder().token("8134757077:AAGvG0W5BCEt8R4uIlzZybXn-la5s9B7rVw").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Starting bot")
    application.run_polling()
