provider "aws" {
  region = "ap-northeast-1"
}

# ECRリポジトリの定義
resource "aws_ecr_repository" "studionavi_backend" {
  name                 = "studionavi-backend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "studionavi-backend"
    Environment = "production"
    Project     = "studionavi"
  }
}

resource "aws_ecr_repository" "studionavi_frontend" {
  name                 = "studionavi-frontend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "studionavi-frontend"
    Environment = "production"
    Project     = "studionavi"
  }
}

# ECRライフサイクルポリシー
resource "aws_ecr_lifecycle_policy" "backend_policy" {
  repository = aws_ecr_repository.studionavi_backend.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1,
        description  = "古いイメージを保持する数を制限する",
        selection = {
          tagStatus     = "any",
          countType     = "imageCountMoreThan",
          countNumber   = 10
        },
        action = {
          type = "expire"
        }
      }
    ]
  })
}

resource "aws_ecr_lifecycle_policy" "frontend_policy" {
  repository = aws_ecr_repository.studionavi_frontend.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1,
        description  = "古いイメージを保持する数を制限する",
        selection = {
          tagStatus     = "any",
          countType     = "imageCountMoreThan",
          countNumber   = 10
        },
        action = {
          type = "expire"
        }
      }
    ]
  })
}
