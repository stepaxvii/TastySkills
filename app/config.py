import os
from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "")

# JWT
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Telegram Bot
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL", "")
TELEGRAM_WEBHOOK_PATH = "/webhook/telegram"

# Admin settings
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", ""))

# Настройки для загрузки файлов
UPLOAD_DIR: str = "uploads"
MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5MB

# Настройки приложения
APP_NAME: str = "TastySkills"
DEBUG: bool = True 