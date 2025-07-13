from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from typing import Dict, Any
from app.infrastructure.database.database import engine
from app.domain.entities.models import Base
from app.config import UPLOAD_DIR, APP_NAME
from app.presentation.api import auth, restaurants, sections, categories, products
from app.presentation.web.web import router as web_router

# Создаем таблицы в базе данных
Base.metadata.create_all(bind=engine)

# Создаем папку для загрузок, если её нет
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Создаем приложение FastAPI
app = FastAPI(
    title=APP_NAME,
    description="API для управления меню ресторанов TastySkills",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене замените на конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем статические файлы
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем API роуты
app.include_router(auth.router, prefix="/api/v1")
app.include_router(restaurants.router, prefix="/api/v1")
app.include_router(sections.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")

# Подключаем веб-роуты
app.include_router(web_router)


@app.get("/")
def read_root() -> Dict[str, Any]:
    """Корневой эндпоинт"""
    return {
        "message": "Добро пожаловать в TastySkills.",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check() -> Dict[str, str]:
    """Проверка здоровья приложения"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 