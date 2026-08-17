import os
import sys
from pathlib import Path

os.environ.setdefault("CONSENT_JOURNAL_URL", "http://consent.test")
os.environ.setdefault("CONSENT_JOURNAL_API_KEY", "test-key")
os.environ.setdefault("CONSENT_PUBLIC_BASE", "http://consent.test/t/test")

# Добавляем папку backend в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))
