import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    # Project Paths
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/signal_digest.db")

    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")

    # App Settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DRY_RUN = os.getenv("DRY_RUN", "False").lower() == "true"

    # Agent Settings
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))

    @classmethod
    def validate(cls):
        """Check for critical missing configuration."""
        missing = []
        if not cls.OPENAI_API_KEY and not cls.GEMINI_API_KEY:
            missing.append("LLM API Key (OPENAI_API_KEY or GEMINI_API_KEY)")
        if not cls.TWILIO_ACCOUNT_SID or not cls.TWILIO_AUTH_TOKEN:
             # Check if we are in dry run, maybe not critical? But good to warn.
            if not cls.DRY_RUN:
                missing.append("Twilio Credentials")
        
        if missing:
            print(f"WARNING: Missing configuration key(s): {', '.join(missing)}")

# Ensure directories exist
Config.DATA_DIR.mkdir(exist_ok=True)
Config.LOGS_DIR.mkdir(exist_ok=True)
