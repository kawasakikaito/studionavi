#!/bin/bash
set -e

echo "Waiting for database to be ready..."
python << END
import sys
import time
import psycopg2
import os
from urllib.parse import urlparse

# DATABASE_URLから接続情報を取得
url = urlparse(os.environ['DATABASE_URL'])
dbname = url.path[1:]
user = url.username
password = url.password
host = url.hostname
port = url.port

# データベースへの接続を試行
for i in range(30):
    try:
        psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        print("Database is ready!")
        sys.exit(0)
    except psycopg2.OperationalError:
        print("Database is not ready. Waiting...")
        time.sleep(2)

print("Could not connect to database after 60 seconds")
sys.exit(1)
END

echo "Running migrations..."
python manage.py migrate --noinput

echo "Creating superuser if not exists..."
python manage.py createsuperuser --noinput || true

echo "Loading fixtures..."
python manage.py loaddata api/fixtures/studio_fixtures.json

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Migration completed successfully!"
