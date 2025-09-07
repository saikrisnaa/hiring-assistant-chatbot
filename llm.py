import openai
import os
from dotenv import load_dotenv

# Load API Key from .env 
load_dotenv()
openai.api_key = os.getenv("GROQ_API_KEY")
openai.api_base = "https://api.groq.com/openai/v1"

LLM_MODEL = "llama-3.1-8b-instant"

