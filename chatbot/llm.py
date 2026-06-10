import os, time, requests, logging
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

GROQ_URL  = "https://api.groq.com/openai/v1/chat/completions"
TOGETHER_URL = "https://api.together.xyz/v1/chat/completions"

MODELOS = {
    "groq":    "llama-3.3-70b-versatile",
    "together": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
}

