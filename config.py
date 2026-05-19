import os

# 必须在 huggingface_hub 被导入前设置，否则镜像不生效
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from dotenv import load_dotenv

load_dotenv()

# DeepSeek API
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-8c98728a7996492ea4bed9db7d0fd3c2")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

# ChromaDB
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "chroma_data")
CHROMA_COLLECTION = "hotspot_memory"
EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"

# GitHub
GITHUB_REPO_PATH = os.path.dirname(__file__)
GITHUB_REMOTE = "origin"
GITHUB_BRANCH = "main"

# Email (SMTP)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.163.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")

# Report
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
MAX_HISTORY_DAYS = 30
MAX_ITEMS_PER_SOURCE = 10
