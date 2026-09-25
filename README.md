## Фудграм
REST API + SPA для публикации рецептов. 

Доступен по ссылке: https://dimitry-foodgram.duckdns.org/

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
