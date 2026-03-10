import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./timelist.db")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
