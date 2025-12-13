import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_CSV = os.path.join(BASE_DIR, "..", "dataset", "99_magic_listings_scored_final.csv")
CHROMA_DIR = os.path.join(BASE_DIR, "..", "data", "chroma_db")
DOCS_JSONL = os.path.join(BASE_DIR, "..", "data", "docs.jsonl")
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

groq_client = Groq(api_key=GROQ_API_KEY)
GROQ_MODEL = "llama-3.3-70b-versatile"
