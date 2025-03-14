import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4-turbo")

# App settings
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CATEGORIES_PATH = os.path.join(DATA_DIR, "categories.csv")
READINGS_PATH = os.path.join(DATA_DIR, "readings.csv")