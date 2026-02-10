from pydantic import BaseModel, HttpUrl, Field
from typing import Optional

class URLCreate(BaseModel):
    """Модель для создания короткой ссылки"""
    url: HttpUrl = Field(..., description="Оригинальный URL для сокращения")
    custom_code: Optional[str] = Field(
        None,
        min_length=4,
        max_length=10,
        pattern=r'^[a-zA-Z0-9]+$',
        description="Кастомный короткий код (опционально, 4-10 символов)"
    )

class URLResponse(BaseModel):
    """Модель ответа с короткой ссылкой"""
    short_url: str