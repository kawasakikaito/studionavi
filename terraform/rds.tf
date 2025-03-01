resource "aws_db_instance" "studionavi_db" {
  identifier           = "studionavi-db"
  allocated_storage    = 20
  storage_type         = "gp2"
  engine               = "postgres"
  engine_version       = "14.10"
  instance_class       = "db.t3.micro"
  username             = "postgres"
  password             = var.db_password
  parameter_group_name = "default.postgres14"
  skip_final_snapshot  = true
  publicly_accessible  = false
  multi_az             = false
  
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.studionavi_db_subnet_group.name

  tags = {
    Name        = "studionavi-db"
    Environment = "production"
    Project     = "studionavi"
  }
}

resource "aws_security_group" "rds_sg" {
  name        = "studionavi-rds-sg"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = var.vpc_id

  # ECSからのアクセスを許可
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.ecs_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "studionavi-rds-sg"
    Environment = "production"
    Project     = "studionavi"
  }
}

resource "aws_db_subnet_group" "studionavi_db_subnet_group" {
  name       = "studionavi-db-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name        = "studionavi-db-subnet-group"
    Environment = "production"
    Project     = "studionavi"
  }
}
