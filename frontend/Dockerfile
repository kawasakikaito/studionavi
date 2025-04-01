# ビルドステージ
FROM node:18-alpine AS build

# 作業ディレクトリを設定
WORKDIR /app

# package.jsonとpackage-lock.jsonをコピー
COPY package*.json ./

# 依存関係をインストール
RUN npm install

# frontendのコードをコピー
COPY . /app

# アプリケーションをビルド
RUN npm run build

# 実行ステージ
FROM nginx:alpine

# Nginxの設定ファイルをコピー
COPY nginx.conf /etc/nginx/conf.d/default.conf

# ビルドステージからビルド済みのファイルをコピー
COPY --from=build /app/dist /usr/share/nginx/html

# ポート80を公開
EXPOSE 80

# Nginxを起動
CMD ["nginx", "-g", "daemon off;"]
