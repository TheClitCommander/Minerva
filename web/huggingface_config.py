# Hugging Face Integration Configuration
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get HF API key from environment variables
HF_API_KEY = os.getenv('HUGGINGFACE_API_TOKEN')

# Configure models
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
DEFAULT_TEXT_GENERATION_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"

# Cache settings
ENABLE_MODEL_CACHING = True
CACHE_DIR = os.path.expanduser("~/.minerva/models")
