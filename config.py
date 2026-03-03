import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # LLM Settings (DeepSeek)
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1") # Corrected variable name
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    # Dify Settings
    DIFY_DATASET_API_KEY = os.getenv("DIFY_DATASET_API_KEY")
    DIFY_BASE_URL = os.getenv("DIFY_BASE_URL", "https://api.dify.ai/v1")
    DIFY_DATASET_ID = os.getenv("DIFY_DATASET_ID")

    # Database Settings
    SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smart_nutrition.db")

config = Config()
