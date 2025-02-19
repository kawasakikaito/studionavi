# 公式のNode.jsイメージを使用
FROM node:18-alpine

# 作業ディレクトリを設定
WORKDIR /app

# package.jsonとpackage-lock.jsonをコピー
COPY package*.json ./

# 依存関係をインストール
RUN npm install

# frontendのコードをコピー
COPY . /app

# アプリが実行されるポートを公開
EXPOSE 3000

# アプリケーションを開発モードで実行
CMD ["npm", "run", "dev", "--", "--host"]
