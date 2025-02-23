# AWS デプロイメントガイド

このドキュメントでは、StudiNaviアプリケーションのAWSへのデプロイ手順を説明します。

## 目次
1. [本番環境用Dockerfileの作成](#1-本番環境用dockerfileの作成)
2. [AWSアカウントのセットアップ](#2-awsアカウントのセットアップ)
3. [最小構成でのデプロイ](#3-最小構成でのデプロイ)
4. [データベースの移行](#4-データベースの移行)
5. [CI/CDパイプラインの構築](#5-cicdパイプラインの構築)
6. [本格的なインフラ構築](#6-本格的なインフラ構築)

## 1. 本番環境用Dockerfileの作成

### 1.1 開発環境と本番環境の違い
- 開発環境
  - ホットリロード有効
  - デバッグモード有効
  - 開発用ツール（pgAdmin等）
  - ボリュームマウント

- 本番環境
  - 最適化されたビルド
  - セキュアな設定
  - パフォーマンス重視
  - 不要なツール削除

### 1.2 本番用Docker Compose設定
```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      - DEBUG=False
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    command: nginx -g 'daemon off;'
```

## 2. AWSアカウントのセットアップ

### 2.1 初期設定
1. AWSアカウントの作成
2. 多要素認証（MFA）の設定
3. IAMユーザーの作成と権限設定
4. 請求アラートの設定

### 2.2 重要な設定項目
- 予算アラートの設定（月額上限）
- セキュリティグループの基本設定
- リージョンの選択（ap-northeast-1推奨）

## 3. 最小構成でのデプロイ

### 3.1 AWS App Runner
1. コンテナイメージのプッシュ
2. サービスの作成
3. 環境変数の設定
4. ヘルスチェックの設定

### 3.2 初期デプロイのチェックリスト
- [ ] HTTPSアクセスの確認
- [ ] ログの確認
- [ ] エラーハンドリングの確認
- [ ] パフォーマンスの確認

## 4. データベースの移行

### 4.1 RDSセットアップ
1. PostgreSQLインスタンスの作成
2. セキュリティグループの設定
3. バックアップ設定
4. 監視設定

### 4.2 データ移行手順
1. 現在のデータのバックアップ
2. RDSへの移行
3. 接続テスト
4. アプリケーション設定の更新

## 5. CI/CDパイプラインの構築

### 5.1 GitHub Actions設定
```yaml
name: Deploy to AWS
on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
      # 以下、デプロイ手順
```

### 5.2 自動化項目
- テスト実行
- セキュリティスキャン
- イメージビルド
- デプロイ

## 6. 本格的なインフラ構築

### 6.1 推奨構成
```
インターネット → Route 53 → CloudFront → ALB → ECS → RDS
```

### 6.2 追加コンポーネント
- VPC設定
- ECSクラスター
- ALB（ロードバランサー）
- Route 53（ドメイン管理）
- CloudFront（CDN）

## 参考リンク
- [AWS公式ドキュメント](https://docs.aws.amazon.com/ja_jp/)
- [AWS料金計算ツール](https://calculator.aws/)
- [AWSベストプラクティス](https://aws.amazon.com/jp/architecture/well-architected/)

## 注意事項
- 本番環境の変更は必ずステージング環境でテスト
- セキュリティグループは最小権限の原則に従う
- 定期的なバックアップと復元テストを実施
- コスト監視を徹底
