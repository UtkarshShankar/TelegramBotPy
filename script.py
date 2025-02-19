import fitz  # PyMuPDF
import logging
import re
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
    try:
        pdf_document = fitz.open(pdf_path)
        text = ""
        for page_num in range(pdf_document.page_count):
            page = pdf_document.load_page(page_num)
            text += page.get_text("text") + "\n"

        if not text.strip():
            logger.error("Extracted text is empty. Check PDF formatting.")
            return None

        logger.info(f"Extracted text (first 500 chars): {text[:500]}")
        return text
    except Exception as e:
        logger.error(f"Error reading PDF: {e}")
        return None

# Function to find the question number for the matching text
def find_question_number(query, pdf_text):
    if not pdf_text:
        return None, None

    pdf_text_lower = pdf_text.lower()
    query_lower = query.lower()

    # Find all question numbers and their positions
    question_pattern = r"(Question\s*#?\d+)"
    matches = list(re.finditer(question_pattern, pdf_text, re.IGNORECASE))

    # Track the last seen question number
    last_question_number = None
    last_question_position = 0

    # Scan the document to find the matching query
    for match in matches:
        question_number = match.group()
        question_start_idx = match.start()

        # If we have already passed the search term, return the last question before it
        if query_lower in pdf_text_lower[last_question_position:question_start_idx]:
            return last_question_number, last_question_position

        # Update last seen question number
        last_question_number = question_number
        last_question_position = question_start_idx

    # Final check in case the query appears after the last question number
    if last_question_number and query_lower in pdf_text_lower[last_question_position:]:
        return last_question_number, last_question_position

    return None, None  # If no valid question number is found

# Telegram bot functions
async def start(update: Update, context: CallbackContext) -> None:
    logger.info("Received /start command")
    await update.message.reply_text("Send me a word or phrase, and I'll find its corresponding question number in the PDF.")

async def handle_message(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text.strip()
    logger.info(f"Received user input: {user_input}")

    question_number, position = find_question_number(user_input, pdf_text)

    if question_number:
        response = f"Found in PDF\nQuestion Number: {question_number}"
    else:
        response = "Not found in PDF"

    await update.message.reply_text(response)
    logger.info(f"Response sent: {response}")

# Main function to run the bot
if __name__ == '__main__':
    pdf_path = "questions.pdf"
    pdf_text = extract_text_from_pdf(pdf_path)

    application = Application.builder().token("8134757077:AAGvG0W5BCEt8R4uIlzZybXn-la5s9B7rVw").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Starting bot")
    application.run_polling()
