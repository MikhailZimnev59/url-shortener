import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db, get_db_connection
import os

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Очистка базы данных перед каждым тестом"""
    # Удаляем старую базу данных
    if os.path.exists("db.sqlite3"):
        os.remove("db.sqlite3")

    # Инициализируем новую
    init_db()


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


def test_redirect():
    """Тест редиректа по короткому коду"""
    # Создаем короткую ссылку
    response = client.post(
        "/shorten",
        json={"url": "https://www.example.com"}
    )
    short_code = response.json()["short_url"].split("/")[-1]

    # Тестируем редирект
    response = client.get(f"/{short_code}", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "https://www.example.com"


def test_invalid_code():
    """Тест несуществующего кода"""
    response = client.get("/nonexistent")
    assert response.status_code == 404


def test_invalid_url():
    """Тест невалидного URL"""
    response = client.post(
        "/shorten",
        json={"url": "not-a-url"}
    )
    assert response.status_code == 422  # Pydantic validation error


def test_health_check():
    """Тест эндпоинта здоровья"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_click_count():
    """Тест счетчика кликов"""
    # Создаем короткую ссылку
    response = client.post(
        "/shorten",
        json={"url": "https://www.example.com"}
    )
    short_code = response.json()["short_url"].split("/")[-1]

    # Получаем исходные данные
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT click_count FROM urls WHERE short_code = ?", (short_code,))
    initial_count = cursor.fetchone()["click_count"]
    conn.close()

    # Делаем несколько редиректов
    for _ in range(3):
        client.get(f"/{short_code}", follow_redirects=False)

    # Проверяем счетчик
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT click_count FROM urls WHERE short_code = ?", (short_code,))
    final_count = cursor.fetchone()["click_count"]
    conn.close()

    assert final_count == initial_count + 3