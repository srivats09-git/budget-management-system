# variables.tf
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-west2"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

