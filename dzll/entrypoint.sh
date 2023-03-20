#!/bin/sh

if [ "$DATABASE" = "mariadb" ]
then
    echo "Waiting for mariadb..."

    while ! nc -z $DBHOST $DBPORT; do
      sleep 0.1
    done

    echo "MariaDB started"
fi

python manage.py collectstatic --no-input
exec "$@"
