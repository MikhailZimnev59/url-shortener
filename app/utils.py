import secrets
import string
import logging

logger = logging.getLogger(__name__)


def generate_short_code(length: int = 6) -> str:
    """
    Генерация случайного короткого кода

    Args:
        length: Длина кода (по умолчанию 6)

    Returns:
        Случайная строка из букв и цифр
    """
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


def validate_url(url: str) -> bool:
    """
    Валидация URL

    Args:
        url: URL для проверки

    Returns:
        True если валиден, иначе False
    """
    try:
        # Pydantic уже валидирует через модели, но добавим дополнительную проверку
        if not url or len(url) > 2048:
            return False

        # Простая проверка на наличие схемы
        if '://' not in url:
            return False

        return True
    except Exception as e:
        logger.error(f"URL validation error: {e}")
        return False