import os
from dotenv import load_dotenv

load_dotenv()

NOTION_KEY = os.getenv("NOTION_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")