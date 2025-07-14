#!/usr/bin/env python3
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import List

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent))

from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def check_environment() -> bool:
    """Проверка переменных окружения"""
    required_vars: List[str] = [
        "TELEGRAM_BOT_TOKEN",
        "ADMIN_ID"
    ]
    
    missing_vars: List[str] = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}")
        logger.error("Создайте файл .env на основе env.exemple")
        return False
    
    return True

def init_database() -> bool:
    """Инициализация базы данных"""
    try:
        from app.infrastructure.database.database import engine
        from app.domain.entities.models import Base
        
        # Создаем таблицы
        Base.metadata.create_all(bind=engine)
        logger.info("База данных инициализирована")
        return True
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
        return False

from app.presentation.telegram.bot import main

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 