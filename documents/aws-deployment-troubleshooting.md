# AWS ECSデプロイのトラブルシューティングと操作ガイド

このドキュメントでは、StudiNaviアプリケーションのAWS ECSデプロイに関する操作とトラブルシューティングの手順をまとめています。

## 目次

1. [デプロイの概要](#1-デプロイの概要)
2. [実行したコマンドと説明](#2-実行したコマンドと説明)
3. [発生した問題と解決策](#3-発生した問題と解決策)
4. [用語集](#4-用語集)
5. [今後の改善点](#5-今後の改善点)
6. [現在の問題点と必要事項](#6-現在の問題点と必要事項)

## 1. デプロイの概要

StudiNaviアプリケーションは以下のAWSサービスを利用してデプロイされています：

- **Amazon ECS (Elastic Container Service)**: コンテナオーケストレーションサービス
- **Amazon ECR (Elastic Container Registry)**: Dockerイメージのレジストリ
- **Application Load Balancer (ALB)**: HTTPトラフィックのロードバランサー
- **Amazon RDS**: PostgreSQLデータベース

デプロイプロセスは以下の流れで行われます：

1. GitHubのmainブランチにコードがプッシュされる
2. GitHub Actionsワークフローが起動
3. Dockerイメージがビルドされ、ECRにプッシュされる
4. データベースマイグレーションが実行される
5. ECSサービスが更新され、新しいタスクがデプロイされる

## 2. 実行したコマンドと説明

### アプリケーションのURLを確認

```bash
# ALB（Application Load Balancer）のDNS名を取得
aws elbv2 describe-load-balancers --names studionavi-alb --query 'LoadBalancers[0].DNSName' --output text
```

このコマンドは、アプリケーションのロードバランサーのDNS名を取得します。これがアプリケーションにアクセスするためのURLです。

### CloudFrontディストリビューションの確認

```bash
# CloudFrontディストリビューションのリストを取得
aws cloudfront list-distributions --query 'DistributionList.Items[*].{DomainName:DomainName,Origins:Origins.Items[0].DomainName}' --output json
```

このコマンドは、CloudFrontディストリビューション（CDN）の設定を確認します。現在は設定されていません。

### Route 53ホストゾーンの確認

```bash
# Route 53ホストゾーンのリストを取得
aws route53 list-hosted-zones --query 'HostedZones[*].{Name:Name,Id:Id}' --output json
```

このコマンドは、Route 53（DNSサービス）のホストゾーンを確認します。現在は設定されていません。

### ECSサービスの設定確認

```bash
# ECSサービスのロードバランサー設定を確認
aws ecs describe-services --cluster studionavi-cluster --services studionavi-service --query 'services[0].loadBalancers' --output json
```

このコマンドは、ECSサービスとロードバランサーの接続設定を確認します。フロントエンドとバックエンドのターゲットグループが設定されています。

### アプリケーションの応答確認

```bash
# URLにアクセスしてHTTPステータスコードを確認
curl -s -o /dev/null -w "%{http_code}" http://studionavi-alb-837030228.ap-northeast-1.elb.amazonaws.com/
```

このコマンドは、アプリケーションのURLにアクセスして、HTTPステータスコードを確認します。

### Nginxの設定変更

フロントエンドのNginx設定を変更して、ルートパス（/）でSPAアプリケーションを表示し、ヘルスチェックを別のパスに移動しました。

```nginx
# 変更前
location = / {
    access_log off;
    add_header Content-Type text/plain;
    return 200 'ok';
}

# 変更後
location = /health {
    access_log off;
    add_header Content-Type text/plain;
    return 200 'ok';
}
```

### 変更のコミットとプッシュ

```bash
# 変更をコミット
git add frontend/nginx.conf
git commit -m "フロントエンドのNginx設定を修正：ヘルスチェックエンドポイントを/healthに移動"

# mainブランチにプッシュしてデプロイを開始
git push origin feature/production-docker:main
```

これらのコマンドは、変更をコミットし、mainブランチにプッシュしてデプロイを開始します。

### デプロイ状態の確認

```bash
# ECSサービスのデプロイ状態を確認
aws ecs describe-services --cluster studionavi-cluster --services studionavi-service --query 'services[0].{status:status,desiredCount:desiredCount,runningCount:runningCount,pendingCount:pendingCount,deployments:deployments[*].{status:status,rolloutState:rolloutState,updatedAt:updatedAt}}' --output json
```

このコマンドは、ECSサービスのデプロイ状態を確認します。`rolloutState`が`COMPLETED`になれば、デプロイが完了しています。

### ECSタスクの確認

```bash
# 実行中のタスクを確認
aws ecs list-tasks --cluster studionavi-cluster

# タスクの詳細を確認
aws ecs describe-tasks --cluster studionavi-cluster --tasks [タスクARN] --query 'tasks[0].{lastStatus:lastStatus,createdAt:createdAt,version:version,taskDefinitionArn:taskDefinitionArn}' --output json
```

これらのコマンドは、実行中のECSタスクとその詳細を確認します。

### ターゲットグループのヘルスチェック設定変更

```bash
# ターゲットグループのヘルスチェックパスを確認
aws elbv2 describe-target-groups --names studionavi-frontend-tg --query 'TargetGroups[0].{HealthCheckPath:HealthCheckPath}' --output json

# ターゲットグループのヘルスチェックパスを変更
aws elbv2 modify-target-group --target-group-arn arn:aws:elasticloadbalancing:ap-northeast-1:717279708380:targetgroup/studionavi-frontend-tg/c42a7751e9debed4 --health-check-path /health
```

これらのコマンドは、ALBターゲットグループのヘルスチェック設定を確認し、変更します。

## 3. 発生した問題と解決策

### 問題1: フロントエンドアプリケーションが表示されない

**症状**: URLにアクセスすると「ok」というテキストのみが表示される

**原因**: Nginxの設定で、ルートパス（/）へのアクセスに対して「ok」というテキストを返すように設定されていた

**解決策**: 
1. Nginxの設定を変更して、ヘルスチェックエンドポイントを`/health`に移動
2. ルートパスでSPAアプリケーションが表示されるようにする

### 問題2: デプロイに時間がかかる

**症状**: デプロイが完了するまでに長時間かかる

**原因**: 
- ECSのローリングデプロイメカニズム
- ヘルスチェックの待機時間
- コネクションドレイニング

**解決策**:
- ターゲットグループのヘルスチェック設定を更新
- デプロイの進行状況を定期的に確認

### 問題3: バックエンドヘルスチェックの301リダイレクト問題

**症状**: バックエンドのヘルスチェックが301リダイレクトレスポンスで失敗し、タスクが継続的に再起動される

**原因**: 
- Djangoのヘルスチェックエンドポイントがリダイレクトを返す（301レスポンス）
- ALBのターゲットグループが200レスポンスのみを「healthy」とみなす設定
- Dockerイメージがlinux/amd64プラットフォームと互換性がない問題も発生

**解決策**:
1. プラットフォーム互換性の問題の解決:
   - Dockerイメージを`--platform=linux/amd64`オプションで明示的にビルド
   ```bash
   docker build --platform=linux/amd64 -t 717279708380.dkr.ecr.ap-northeast-1.amazonaws.com/studionavi-backend:latest ./backend
   ```

2. ALBターゲットグループの設定変更:
   - ヘルスチェックパスを `/health/` に変更（末尾のスラッシュを追加）
   - HTTPレスポンスコードマッチャーを変更し、301レスポンスも「healthy」とみなす設定に
   ```bash
   # ヘルスチェックパスの変更
   aws elbv2 modify-target-group --target-group-arn arn:aws:elasticloadbalancing:ap-northeast-1:717279708380:targetgroup/studionavi-backend-tg/1c6d47941fe4d6f6 --health-check-path "/health/" --region ap-northeast-1
   
   # レスポンスコードマッチャーの変更（200と301を許可）
   aws elbv2 modify-target-group --target-group-arn arn:aws:elasticloadbalancing:ap-northeast-1:717279708380:targetgroup/studionavi-backend-tg/1c6d47941fe4d6f6 --matcher '{"HttpCode": "200,301"}' --region ap-northeast-1
   ```

この解決策は、301リダイレクトを完全に解消するのではなく、ALBのヘルスチェック設定側で301レスポンスを健全とみなすように設定を変更することでプラグマティックに問題を解決しました。これにより、アプリケーションコードの複雑な変更を避け、インフラストラクチャ側での調整で対応することができました。

## 4. 用語集

- **AWS ECS (Elastic Container Service)**: Dockerコンテナを実行するためのフルマネージドコンテナオーケストレーションサービス
- **AWS ECR (Elastic Container Registry)**: Dockerイメージを保存、管理するためのレジストリサービス
- **ALB (Application Load Balancer)**: HTTPトラフィックを複数のターゲットに分散するロードバランサー
- **ターゲットグループ**: ALBがトラフィックを転送する先のインスタンスやコンテナのグループ
- **ECSタスク**: ECS上で実行される最小単位のコンテナセット
- **ECSサービス**: 指定された数のタスクを維持し、タスクが失敗した場合に自動的に再起動するサービス
- **ヘルスチェック**: アプリケーションが正常に動作しているかを確認するための仕組み
- **ドレイニング**: 既存の接続を適切に終了させるプロセス
- **ローリングデプロイ**: サービスを停止せずに、新しいバージョンを徐々にデプロイする方法

## 5. 今後の改善点

1. **デプロイ時間の短縮**:
   - ヘルスチェックのインターバルとタイムアウトの最適化
   - 最小ヘルシーパーセントと最大パーセントの調整

2. **モニタリングの強化**:
   - CloudWatchアラームの設定
   - デプロイイベントの通知設定

3. **セキュリティの強化**:
   - HTTPS対応
   - WAF（Web Application Firewall）の導入

4. **カスタムドメインの設定**:
   - Route 53でのドメイン設定
   - ACM（AWS Certificate Manager）での証明書発行

5. **CI/CDパイプラインの改善**:
   - テスト自動化の追加
   - ステージング環境の導入

## 6. 現在の問題点と必要事項

### 1. デプロイ状況
- ECSサービスのデプロイは正常に完了（rolloutState: COMPLETED）。
- バックエンドおよびフロントエンドのターゲットグループは、現時点でhealthy（古いタスクはdraining中）。

### 2. 発生していた問題点
- **バックエンドのヘルスチェック**: 初期はHTTPSへのリダイレクト（301）が原因でヘルスチェックに失敗していた。
   - 対策として、ALBバックエンドターゲットグループのヘルスチェック設定にて、レスポンスコード200および301を健全とみなすよう修正済み。

- **フロントエンドのNginx設定**: ルートパス（/）のレスポンスでContent-Typeがtext/plainになっていたため、正しくHTMLとして表示されない問題があった。
   - 対策として、Nginx設定にてContent-Typeをtext/htmlに修正し、コミット・プッシュ済み。

### 3. 残る課題と今後の必要事項
- **HTTPS対応の強化**:
   - 現在、バックエンドの/api/health/エンドポイントはHTTPSへのリダイレクトを引き起こしていて、ALBでのHTTPS設定、ACMによる証明書発行、Route53でのカスタムドメイン設定を検討する。

- **モニタリングとログ管理**:
   - CloudWatchアラームの設定やログ解析ツールの導入により、今後のデプロイや運用時の障害発生を迅速に検知・対処できる環境の整備。

- **デプロイプロセスの最適化**:
   - 現状のヘルスチェックやデプロイ時間を更に短縮するため、ヘルスチェックのパラメータの調整やブルー/グリーンデプロイの導入など、運用面での改善策を検討する。

以上の内容をもとに、他のメンバーも作業を継続できるように情報共有をお願いいたします。
