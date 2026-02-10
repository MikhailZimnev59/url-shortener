# URL Shortener

Тестовое задание по сокращения ссылок на FastAPI.

## Запуск

### Установка зависимостей
pip install -e .

### Запуск приложения
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Приложение будет доступно по адресу: http://localhost:8000

###  Технологии
- Python 3.14
- Github https://github.com/MikhailZimnev59/url-shortener/
- sqlite3
- pytest
- Fastapi
- pyproject.toml

### Эндпойнты
- POST /shorten - сокращение ссылок с валидацией
- GET /{code} - редирект по короткому коду

### Запуск тестов
python -m pytest tests/ -v
