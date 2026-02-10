import sqlite3
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "db.sqlite3"


def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_url TEXT NOT NULL,
            short_code TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            click_count INTEGER DEFAULT 0
        )
    """)

    # Создание индекса для ускорения поиска
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_short_code ON urls(short_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_original_url ON urls(original_url)")

    conn.commit()
    conn.close()
    logger.info("Database initialized")


def get_db_connection():
    """Получение соединения с базой данных"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_url(original_url: str, short_code: str) -> bool:
    """Создание новой записи о сокращенной ссылке"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO urls (original_url, short_code) VALUES (?, ?)",
            (original_url, short_code)
        )

        conn.commit()
        conn.close()
        logger.info(f"Created short URL: {short_code} -> {original_url}")
        return True
    except sqlite3.IntegrityError:
        logger.warning(f"Short code {short_code} already exists")
        return False


def get_url_by_code(short_code: str) -> Optional[dict]:
    """Получение оригинального URL по короткому коду"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM urls WHERE short_code = ?", (short_code,))
    row = cursor.fetchone()

    conn.close()

    if row:
        return dict(row)
    return None


def increment_click_count(short_code: str) -> bool:
    """Увеличение счетчика кликов"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE urls SET click_count = click_count + 1 WHERE short_code = ?",
            (short_code,)
        )

        conn.commit()
        conn.close()
        logger.info(f"Incremented click count for {short_code}")
        return True
    except Exception as e:
        logger.error(f"Error incrementing click count: {e}")
        return False


def get_url_by_original(original_url: str) -> Optional[dict]:
    """Получение записи по оригинальному URL (для проверки дубликатов)"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM urls WHERE original_url = ?", (original_url,))
    row = cursor.fetchone()

    conn.close()

    if row:
        return dict(row)
    return None