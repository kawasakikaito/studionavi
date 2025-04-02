#!/bin/bash
set -e

# 環境変数を設定
export DJANGO_SETTINGS_MODULE=config.settings.production
export DJANGO_ENVIRONMENT=production
export SECURE_SSL_REDIRECT=False
export SECURE_HSTS_SECONDS=0
export PYTHONPATH=/app

# デバッグ情報を出力
echo "Starting Django application with HTTPS redirect disabled"
echo "DJANGO_SETTINGS_MODULE: $DJANGO_SETTINGS_MODULE"
echo "SECURE_SSL_REDIRECT: $SECURE_SSL_REDIRECT"

# Gunicornを実行
exec gunicorn --bind 0.0.0.0:8000 --workers 3 --forwarded-allow-ips=* --access-logfile - --error-logfile - config.wsgi:application
