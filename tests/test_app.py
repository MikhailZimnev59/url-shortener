import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db, get_db_connection, DB_PATH
import os
import time
import tempfile
import shutil
from pathlib import Path

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database(tmp_path):
    """
    Используем временную директорию для БД в каждом тесте.
    Это решает проблему блокировки файла в Windows.
    """
    # Сохраняем оригинальный путь к БД
    original_db_path = DB_PATH

    # Создаём временную БД в изолированной директории
    test_db_dir = tmp_path / "test_db"
    test_db_dir.mkdir()
    test_db_path = test_db_dir / "db.sqlite3"

    # Подменяем путь к БД для текущего теста
    from app import database
    database.DB_PATH = test_db_path

    # Инициализируем БД
    init_db()

    yield

    # Восстанавливаем оригинальный путь
    database.DB_PATH = original_db_path

    # Очищаем временные файлы (автоматически удалится при выходе из фикстуры)


def test_shorten_url():
    """Тест сокращения URL"""
    response = client.post(
        "/shorten",
        json={"url": "https://www.example.com"}
    )

    assert response.status_code == 201
    data = response.json()
    assert "short_url" in data
    assert data["short_url"].startswith("http://testserver/")

    # Проверяем, что короткий код существует
    short_code = data["short_url"].split("/")[-1]
    assert len(short_code) == 6  # По умолчанию 6 символов


def test_shorten_url_with_custom_code():
    """Тест сокращения URL с кастомным кодом"""
    response = client.post(
        "/shorten",
        json={
            "url": "https://www.example.com",
            "custom_code": "test123"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["short_url"] == "http://testserver/test123"


def test_duplicate_url():
    """Тест дублирования URL (должен вернуть существующий код)"""
    # Первый запрос
    response1 = client.post(
        "/shorten",
        json={"url": "https://www.example.com"}
    )
    code1 = response1.json()["short_url"].split("/")[-1]

    # Второй запрос с тем же URL
    response2 = client.post(
        "/shorten",
        json={"url": "https://www.example.com"}
    )
    code2 = response2.json()["short_url"].split("/")[-1]

    # Коды должны быть одинаковыми
    assert code1 == code2


def test_duplicate_custom_code():
    """Тест дублирования кастомного кода"""
    # Первый запрос с кастомным кодом
    response1 = client.post(
        "/shorten",
        json={
            "url": "https://www.example1.com",
            "custom_code": "custom"
        }
    )
    assert response1.status_code == 201

    # Второй запрос с тем же кастомным кодом
    response2 = client.post(
        "/shorten",
        json={
            "url": "https://www.example2.com",
            "custom_code": "custom"
        }
    )
    assert response2.status_code == 409  # Conflict


