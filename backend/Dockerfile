# 公式のPythonイメージを使用
FROM python:3.12-slim

# 環境変数を設定
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

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

# SQLiteデータベース用のボリュームを作成
VOLUME /app/db

# アプリが実行されるポートを公開
EXPOSE 8000

# アプリケーションを実行するコマンド
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
