from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import uvicorn
from typing import Optional

from .database import init_db, create_url, get_url_by_code, increment_click_count, get_url_by_original
from .models import URLCreate, URLResponse
from .utils import generate_short_code, validate_url

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация при запуске и очистка при завершении"""
    # Инициализация базы данных
    init_db()
    logger.info("Application starting...")
    yield
    logger.info("Application shutting down...")


app = FastAPI(
    title="URL Shortener API",
    description="Простое приложение для сокращения ссылок",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/shorten", response_model=URLResponse, status_code=201)
async def shorten_url(url_data: URLCreate, request: Request):
    """
    Сокращает длинную ссылку и возвращает короткий URL

    - **url**: Оригинальный URL для сокращения
    - **custom_code**: Опциональный кастомный короткий код (4-10 символов)
    """
    original_url = str(url_data.url)

    # Валидация URL
    if not validate_url(original_url):
        logger.warning(f"Invalid URL submitted: {original_url}")
        raise HTTPException(status_code=400, detail="Invalid URL")

    # Проверка дубликатов
    existing = get_url_by_original(original_url)
    if existing:
        short_code = existing['short_code']
        logger.info(f"URL already exists: {short_code}")
        return URLResponse(
            short_url=f"{request.base_url}{short_code}"
        )

    # Генерация или использование кастомного кода
    short_code = url_data.custom_code
    if not short_code:
        # Генерация уникального кода
        max_attempts = 10
        for _ in range(max_attempts):
            short_code = generate_short_code()
            if not get_url_by_code(short_code):
                break
        else:
            logger.error("Failed to generate unique short code")
            raise HTTPException(status_code=500, detail="Failed to generate short code")

    # Создание записи в базе данных
    success = create_url(original_url, short_code)
    if not success:
        # Возможно, кастомный код уже существует
        existing = get_url_by_code(short_code)
        if existing and existing['original_url'] == original_url:
            logger.info(f"Custom code {short_code} already exists for this URL")
            return URLResponse(
                short_url=f"{request.base_url}{short_code}"
            )
        logger.warning(f"Custom code {short_code} already exists for different URL")
        raise HTTPException(status_code=409, detail="Custom code already in use")

    logger.info(f"Created short URL: {short_code}")
    return URLResponse(
        short_url=f"{request.base_url}{short_code}"
    )


@app.get("/{code}", response_class=RedirectResponse, status_code=307)
async def redirect_to_url(code: str):
    """
    Перенаправляет на оригинальную ссылку по короткому коду

    - **code**: Короткий код ссылки
    """
    # Валидация кода
    if not code or len(code) > 10 or not code.replace('_', '').isalnum():
        logger.warning(f"Invalid short code: {code}")
        raise HTTPException(status_code=400, detail="Invalid short code")

    # Поиск ссылки в базе данных
    url_data = get_url_by_code(code)
    if not url_data:
        logger.warning(f"Short code not found: {code}")
        raise HTTPException(status_code=404, detail="URL not found")

    # Увеличение счетчика кликов
    increment_click_count(code)

    logger.info(f"Redirecting {code} to {url_data['original_url']}")
    return url_data['original_url']



if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)