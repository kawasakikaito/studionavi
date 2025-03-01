# StudiNavi AWS CLI コマンド集

このドキュメントでは、StudiNaviプロジェクトで使用したAWS CLIコマンドを記録しています。
これらのコマンドは、IaC（Infrastructure as Code）として保存されており、環境の再構築や参照に利用できます。

## ECRリポジトリ関連

### ECRリポジトリの作成

```bash
# バックエンドリポジトリの作成
aws ecr create-repository \
    --repository-name studionavi-backend \
    --image-scanning-configuration scanOnPush=true \
    --region ap-northeast-1

# フロントエンドリポジトリの作成
aws ecr create-repository \
    --repository-name studionavi-frontend \
    --image-scanning-configuration scanOnPush=true \
    --region ap-northeast-1
```

### ECRリポジトリの認証とイメージのプッシュ

```bash
# ECRへのログイン
aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.ap-northeast-1.amazonaws.com

# イメージのビルドとタグ付け（バックエンド）
docker build -t studionavi-backend:latest -f backend/Dockerfile.prod backend/
docker tag studionavi-backend:latest $(aws sts get-caller-identity --query Account --output text).dkr.ecr.ap-northeast-1.amazonaws.com/studionavi-backend:latest

# イメージのプッシュ（バックエンド）
docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.ap-northeast-1.amazonaws.com/studionavi-backend:latest

# イメージのビルドとタグ付け（フロントエンド）
docker build -t studionavi-frontend:latest -f frontend/Dockerfile.prod frontend/
docker tag studionavi-frontend:latest $(aws sts get-caller-identity --query Account --output text).dkr.ecr.ap-northeast-1.amazonaws.com/studionavi-frontend:latest

# イメージのプッシュ（フロントエンド）
docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.ap-northeast-1.amazonaws.com/studionavi-frontend:latest
```

### ECRライフサイクルポリシーの設定

```bash
# バックエンドリポジトリのライフサイクルポリシー
aws ecr put-lifecycle-policy \
    --repository-name studionavi-backend \
    --lifecycle-policy-text '{"rules":[{"rulePriority":1,"description":"古いイメージを保持する数を制限する","selection":{"tagStatus":"any","countType":"imageCountMoreThan","countNumber":10},"action":{"type":"expire"}}]}' \
    --region ap-northeast-1

# フロントエンドリポジトリのライフサイクルポリシー
aws ecr put-lifecycle-policy \
    --repository-name studionavi-frontend \
    --lifecycle-policy-text '{"rules":[{"rulePriority":1,"description":"古いイメージを保持する数を制限する","selection":{"tagStatus":"any","countType":"imageCountMoreThan","countNumber":10},"action":{"type":"expire"}}]}' \
    --region ap-northeast-1
```

## RDS関連

### RDSインスタンスの作成

```bash
# DBサブネットグループの作成
aws rds create-db-subnet-group \
    --db-subnet-group-name studionavi-db-subnet-group \
    --db-subnet-group-description "Subnet group for StudiNavi DB" \
    --subnet-ids subnet-xxxxxxxxxxxx subnet-yyyyyyyyyyyy \
    --region ap-northeast-1

# セキュリティグループの作成
aws ec2 create-security-group \
    --group-name studionavi-rds-sg \
    --description "Security group for RDS PostgreSQL" \
    --vpc-id vpc-xxxxxxxxxxxx \
    --region ap-northeast-1

# セキュリティグループにインバウンドルールを追加
aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxxxxxxxxx \
    --protocol tcp \
    --port 5432 \
    --source-group sg-yyyyyyyyyyyy \
    --region ap-northeast-1

# RDSインスタンスの作成
aws rds create-db-instance \
    --db-instance-identifier studionavi-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 14.10 \
    --allocated-storage 20 \
    --master-username postgres \
    --master-user-password your-secure-password \
    --vpc-security-group-ids sg-xxxxxxxxxxxx \
    --db-subnet-group-name studionavi-db-subnet-group \
    --no-publicly-accessible \
    --no-multi-az \
    --backup-retention-period 7 \
    --preferred-backup-window 16:00-16:30 \
    --preferred-maintenance-window sun:17:00-sun:17:30 \
    --storage-type gp2 \
    --region ap-northeast-1
```

## ECS関連

### ECSクラスターの作成

```bash
# ECSクラスターの作成
aws ecs create-cluster \
    --cluster-name studionavi-cluster \
    --settings name=containerInsights,value=enabled \
    --region ap-northeast-1
```

### タスク定義の登録

```bash
# タスク定義の登録（task-definition.jsonファイルを使用）
aws ecs register-task-definition \
    --cli-input-json file://task-definition.json \
    --region ap-northeast-1
```

### ECSサービスの作成

```bash
# ECSサービスの作成
aws ecs create-service \
    --cluster studionavi-cluster \
    --service-name studionavi-service \
    --task-definition studionavi:1 \
    --desired-count 1 \
    --launch-type FARGATE \
    --platform-version LATEST \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxxxxxxxxx,subnet-yyyyyyyyyyyy],securityGroups=[sg-zzzzzzzzzzzz],assignPublicIp=ENABLED}" \
    --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:ap-northeast-1:xxxxxxxxxxxx:targetgroup/studionavi-frontend-tg/xxxxxxxxxxxxxxxx,containerName=frontend,containerPort=80" "targetGroupArn=arn:aws:elasticloadbalancing:ap-northeast-1:xxxxxxxxxxxx:targetgroup/studionavi-backend-tg/yyyyyyyyyyyyyyyy,containerName=backend,containerPort=8000" \
    --health-check-grace-period-seconds 120 \
    --region ap-northeast-1
```

## ALB関連

### ALBの作成

```bash
# セキュリティグループの作成
aws ec2 create-security-group \
    --group-name studionavi-alb-sg \
    --description "Security group for ALB" \
    --vpc-id vpc-xxxxxxxxxxxx \
    --region ap-northeast-1

# セキュリティグループにインバウンドルールを追加
aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxxxxxxxxx \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0 \
    --region ap-northeast-1

aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxxxxxxxxx \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0 \
    --region ap-northeast-1

# ALBの作成
aws elbv2 create-load-balancer \
    --name studionavi-alb \
    --subnets subnet-xxxxxxxxxxxx subnet-yyyyyyyyyyyy \
    --security-groups sg-xxxxxxxxxxxx \
    --region ap-northeast-1

# ターゲットグループの作成（フロントエンド）
aws elbv2 create-target-group \
    --name studionavi-frontend-tg \
    --protocol HTTP \
    --port 80 \
    --vpc-id vpc-xxxxxxxxxxxx \
    --target-type ip \
    --health-check-path /health \
    --health-check-interval-seconds 30 \
    --health-check-timeout-seconds 5 \
    --healthy-threshold-count 2 \
    --unhealthy-threshold-count 2 \
    --matcher "HttpCode=200" \
    --region ap-northeast-1

# ターゲットグループの作成（バックエンド）
aws elbv2 create-target-group \
    --name studionavi-backend-tg \
    --protocol HTTP \
    --port 8000 \
    --vpc-id vpc-xxxxxxxxxxxx \
    --target-type ip \
    --health-check-path /api/health/ \
    --health-check-interval-seconds 30 \
    --health-check-timeout-seconds 5 \
    --healthy-threshold-count 2 \
    --unhealthy-threshold-count 2 \
    --matcher "HttpCode=200,301" \
    --region ap-northeast-1

# リスナーの作成
aws elbv2 create-listener \
    --load-balancer-arn arn:aws:elasticloadbalancing:ap-northeast-1:xxxxxxxxxxxx:loadbalancer/app/studionavi-alb/xxxxxxxxxxxxxxxx \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:ap-northeast-1:xxxxxxxxxxxx:targetgroup/studionavi-frontend-tg/xxxxxxxxxxxxxxxx \
    --region ap-northeast-1

# リスナールールの作成（APIパス用）
aws elbv2 create-rule \
    --listener-arn arn:aws:elasticloadbalancing:ap-northeast-1:xxxxxxxxxxxx:listener/app/studionavi-alb/xxxxxxxxxxxxxxxx/xxxxxxxxxxxxxxxx \
    --priority 100 \
    --conditions Field=path-pattern,Values='/api/*' \
    --actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:ap-northeast-1:xxxxxxxxxxxx:targetgroup/studionavi-backend-tg/yyyyyyyyyyyyyyyy \
    --region ap-northeast-1
```

## IAM関連

### ECS実行ロールの作成

```bash
# ロールの作成
aws iam create-role \
    --role-name studionavi-ecs-execution-role \
    --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Action":"sts:AssumeRole"}]}' \
    --region ap-northeast-1

# ポリシーのアタッチ
aws iam attach-role-policy \
    --role-name studionavi-ecs-execution-role \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy \
    --region ap-northeast-1

# SSMアクセス用のインラインポリシーの追加
aws iam put-role-policy \
    --role-name studionavi-ecs-execution-role \
    --policy-name studionavi-ecs-ssm-policy \
    --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["ssm:GetParameters","secretsmanager:GetSecretValue","kms:Decrypt"],"Resource":"*"}]}' \
    --region ap-northeast-1
```

### ECSタスクロールの作成

```bash
# ロールの作成
aws iam create-role \
    --role-name studionavi-ecs-task-role \
    --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Action":"sts:AssumeRole"}]}' \
    --region ap-northeast-1

# インラインポリシーの追加
aws iam put-role-policy \
    --role-name studionavi-ecs-task-role \
    --policy-name studionavi-ecs-task-policy \
    --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["logs:CreateLogStream","logs:PutLogEvents"],"Resource":"*"}]}' \
    --region ap-northeast-1
```

## SSMパラメータストア関連

```bash
# データベースURLの保存
aws ssm put-parameter \
    --name "/studionavi/production/database_url" \
    --description "Database URL for StudiNavi" \
    --value "postgres://postgres:your-secure-password@studionavi-db.xxxxxxxxxxxx.ap-northeast-1.rds.amazonaws.com:5432/studionavi" \
    --type SecureString \
    --region ap-northeast-1
```

## 注意事項

- 上記コマンドの`subnet-xxxxxxxxxxxx`、`vpc-xxxxxxxxxxxx`、`sg-xxxxxxxxxxxx`などのIDは、実際の環境のIDに置き換えてください。
- パスワードなどの機密情報は、実際の値を使用する際に置き換えてください。
- 実行する前に、各コマンドの内容を確認し、必要に応じて調整してください。
