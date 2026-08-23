import os
import sys
from pathlib import Path

os.environ.setdefault("CONSENT_JOURNAL_URL", "http://consent.test")
os.environ.setdefault("CONSENT_JOURNAL_API_KEY", "test-key")
os.environ.setdefault("CONSENT_PUBLIC_BASE", "http://consent.test/t/test")
os.environ.setdefault("API_KEY_BOT", "test-bot-key")
os.environ.setdefault("API_KEY_APP", "test-app-key")
os.environ.setdefault("API_KEY_SITE", "test-site-key")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_sous_chef",
)

# Добавляем папку backend в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))
