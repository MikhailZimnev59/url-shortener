import requests

# Базовый запрос
response = requests.post(
    "http://localhost:8000/shorten",
    json={"url": "https://www.python.org/doc/versions/3.12/whatsnew/3.12.html"}
)

print(response.status_code)  # 201
print(response.json())
# {'short_url': 'http://localhost:8000/aB3x9Z'}

# С кастомным кодом
response = requests.post(
    "http://localhost:8000/shorten",
    json={
        "url": "https://www.python.org/doc/versions/3.12/whatsnew/3.12.html",
        "custom_code": "python312"
    }
)

print(response.json())
# {'short_url': 'http://localhost:8000/python312'}