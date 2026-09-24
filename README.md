## Фудграм
REST API + SPA для публикации рецептов. 

Доступен по ссылке: https://dimitry-foodgram.duckdns.org/

### Для ревьюера:

Ревьюеру — как прогнать Postman-коллекцию
Коллекция: postman_collection/foodgram.postman_collection.json
Ожидаемый результат: 222 passed / 0 failed.

Подготовка окружения:

```bash
git clone https://github.com/k-dimitry/foodgram.git
cd foodgram/backend

python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
```
В .env выставить:

```text
USE_SQLITE=True
DEBUG=True
```

Затем:

```bash
python manage.py migrate
python manage.py load_ingredients
python manage.py loaddata tags
python manage.py runserver
```


Сервер поднимется на http://127.0.0.1:8000 — это базовый URL коллекции.

### Прогон в Postman:

Postman → Import → postman_collection/foodgram.postman_collection.json
 → Run collection


Примечание: USE_SQLITE=True — специальный режим для локального прогона коллекции (SQLite, без PostgreSQL). В dev-режиме, в CI и в проде используется PostgreSQL (USE_SQLITE=False).

### Стек
Python 3.12, Django 5, Django REST Framework, PostgreSQL 16

Docker Compose, nginx, GitHub Actions (CI/CD)

React 17 SPA — папка frontend/

### Локальный запуск через Docker
```bash
cd infra
docker compose up --build
```

После старта:

Фронтенд: http://localhost/

OpenAPI: http://localhost/api/docs/

Админка: http://localhost/admin/


#### Deploy
Домен: https://dimitry-foodgram.duckdns.org/

Образы: ghcr.io/k-dimitry/foodgram-backend:latest, ghcr.io/k-dimitry/foodgram-frontend:latest

CI/CD: push в main → test → build&push → deploy (GitHub Actions)


### Структура
```text
backend/ Django + DRF
frontend/ React SPA
infra/ docker-compose, nginx.conf
data/ исходный список ингредиентов (JSON)
docs/ OpenAPI schema + redoc
postman_collection/
```
