#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

# [ тут запуск миграций для admin_panel, в данном модуле deprecated ]
# python manage.py makemigrations movie_admin
# python manage.py migrate

# [ тут будет запуск etl ]
# python ETL/main.py &
exec "$@"
