#!/bin/bash
set -e

if [ -n "$POSTGRES_HOST" ]; then
    echo "Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT:-5432}..."
    while ! nc -z "${POSTGRES_HOST}" "${POSTGRES_PORT:-5432}"; do
        sleep 1
    done
    echo "PostgreSQL is up"
fi

mkdir -p /app/media/users/avatars
if [ ! -f /app/media/users/avatars/default.png ]; then
    cp /app/media_seed/users/avatars/default.png /app/media/users/avatars/default.png
    echo "Default avatar seeded"
fi

echo "Running migrations..."
python manage.py migrate --noinput

echo "Loading ingredients..."
python manage.py load_ingredients || echo "load_ingredients skipped/failed — continuing"

echo "Collecting static..."
python manage.py collectstatic --noinput

echo "Starting gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --access-logfile - \
    --error-logfile -