# StudiNavi Terraform IaC

このディレクトリには、StudiNaviアプリケーションのAWSインフラストラクチャをコードとして管理するTerraformファイルが含まれています。

## 含まれるリソース

- ECRリポジトリ（フロントエンド・バックエンド用）
- RDSデータベース（PostgreSQL）
- ECSクラスター、タスク定義、サービス
- Application Load Balancer
- セキュリティグループ
- IAMロールとポリシー
- SSMパラメータストア

## 使用方法

### 前提条件

- Terraformがインストールされていること（バージョン1.0以上推奨）
- AWS CLIがインストールされ、適切な認証情報が設定されていること

### terraform.tfvarsファイルの作成

以下の内容で`terraform.tfvars`ファイルを作成してください：

```hcl
aws_region         = "ap-northeast-1"
vpc_id             = "vpc-xxxxxxxxxxxxxxxxx"
public_subnet_ids  = ["subnet-xxxxxxxxxxxxxxxxx", "subnet-yyyyyyyyyyyyyyyyy"]
private_subnet_ids = ["subnet-xxxxxxxxxxxxxxxxx", "subnet-yyyyyyyyyyyyyyyyy"]
db_password        = "your-secure-password"
```

### デプロイ手順

```bash
# 初期化
terraform init

# 実行計画の確認
terraform plan

# リソースの作成
terraform apply
```

### 削除手順

```bash
# リソースの削除
terraform destroy
```

## 注意事項

- `db_password`は機密情報のため、リポジトリにコミットしないでください。
- 本番環境では、状態ファイル（tfstate）をS3バケットに保存することを推奨します。
- 重要なリソースを誤って削除しないよう、`terraform destroy`コマンドは慎重に使用してください。

## 追加設定

必要に応じて以下の設定を追加・変更してください：

- HTTPS対応（ACMとRoute 53の設定）
- バックアップ戦略
- モニタリングとアラート設定
- オートスケーリング設定
