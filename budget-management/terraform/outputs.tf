# outputs.tf
output "db_instance_name" {
  value = google_sql_database_instance.budget_db.name
}

output "cloud_run_url" {
  value = google_cloud_run_service.budget_management.status[0].url
}