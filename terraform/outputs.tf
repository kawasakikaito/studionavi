output "ecr_backend_repository_url" {
  description = "The URL of the backend ECR repository"
  value       = aws_ecr_repository.studionavi_backend.repository_url
}

output "ecr_frontend_repository_url" {
  description = "The URL of the frontend ECR repository"
  value       = aws_ecr_repository.studionavi_frontend.repository_url
}

output "rds_endpoint" {
  description = "The endpoint of the RDS instance"
  value       = aws_db_instance.studionavi_db.endpoint
}

output "alb_dns_name" {
  description = "The DNS name of the ALB"
  value       = aws_lb.studionavi_alb.dns_name
}

output "ecs_cluster_name" {
  description = "The name of the ECS cluster"
  value       = aws_ecs_cluster.studionavi_cluster.name
}

output "ecs_service_name" {
  description = "The name of the ECS service"
  value       = aws_ecs_service.studionavi_service.name
}

output "task_definition_arn" {
  description = "The ARN of the task definition"
  value       = aws_ecs_task_definition.studionavi_task.arn
}
