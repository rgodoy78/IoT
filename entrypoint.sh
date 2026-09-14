#!/bin/sh
set -e

echo "Esperando a la base de datos en $SQL_HOST:$SQL_PORT..."
while ! nc -z "$SQL_HOST" "$SQL_PORT"; do
  sleep 0.5
done
echo "Base de datos disponible."

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
