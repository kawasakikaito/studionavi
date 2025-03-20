# syntax=docker/dockerfile:1
FROM --platform=linux/amd64 python:3.11-slim

# 環境変数を設定
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings.production
ENV SECURE_SSL_REDIRECT=False
ENV CORS_ALLOW_ALL_ORIGINS=True

# 作業ディレクトリを設定
WORKDIR /app

# システム依存関係をインストール
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# backendのコードをコピー
COPY . /app

# HTTPSリダイレクトを無効化するためのスクリプトを作成
RUN echo '#!/bin/bash\n\
echo "Djangoの設定を上書きしています..."\n\
sed -i "s/SECURE_SSL_REDIRECT = True/SECURE_SSL_REDIRECT = False/g" /app/config/settings/production.py\n\
sed -i "s/SESSION_COOKIE_SECURE = True/SESSION_COOKIE_SECURE = False/g" /app/config/settings/production.py\n\
sed -i "s/CSRF_COOKIE_SECURE = True/CSRF_COOKIE_SECURE = False/g" /app/config/settings/production.py\n\
# SecurityMiddlewareを無効化\n\
echo "MIDDLEWARE = [m for m in MIDDLEWARE if m != \\"django.middleware.security.SecurityMiddleware\\"]" >> /app/config/settings/production.py\n\
echo "設定の上書きが完了しました"\n\
python manage.py runserver 0.0.0.0:8000\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# マイグレーションスクリプトを作成
RUN echo '#!/bin/bash\n\
echo "データベースマイグレーションを実行しています..."\n\
python manage.py migrate\n\
python manage.py collectstatic --noinput\n\
echo "スーパーユーザーが存在するか確認しています..."\n\
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username=\"\$DJANGO_SUPERUSER_USERNAME\").exists() or User.objects.create_superuser(\"\$DJANGO_SUPERUSER_USERNAME\", \"\$DJANGO_SUPERUSER_EMAIL\", \"\$DJANGO_SUPERUSER_PASSWORD\")"\n\
echo "マイグレーションが完了しました"\n\
' > /app/migrate.sh && chmod +x /app/migrate.sh

# SQLiteデータベース用のボリュームを作成
VOLUME /app/db

# アプリが実行されるポートを公開
EXPOSE 8000

# アプリケーションを実行するコマンド
CMD ["/app/entrypoint.sh"]
