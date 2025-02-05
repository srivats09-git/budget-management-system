# main.tf
provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "cloudsql.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "firebase.googleapis.com"
  ])
  project = var.project_id
  service = each.key
}

# Create Cloud SQL instance
resource "google_sql_database_instance" "budget_db" {
  name             = "budget-db"
  database_version = "POSTGRES_13"
  region           = var.region

  settings {
    tier = "db-f1-micro"
    backup_configuration {
      enabled = true
      start_time = "04:00"
    }
  }

  deletion_protection = false  # Set to true in production
}

# Create database
resource "google_sql_database" "budget_management" {
  name     = "budget_management"
  instance = google_sql_database_instance.budget_db.name
}

# Create database user
resource "google_sql_user" "budget_app" {
  name     = "budget_app"
  instance = google_sql_database_instance.budget_db.name
  password = var.db_password
}

# Create service account
resource "google_service_account" "budget_app" {
  account_id   = "budget-app-sa"
  display_name = "Budget Management App Service Account"
}

# Grant permissions
resource "google_project_iam_member" "sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.budget_app.email}"
}

resource "google_project_iam_member" "secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.budget_app.email}"
}

# Deploy Cloud Run service
resource "google_cloud_run_service" "budget_management" {
  name     = "budget-management"
  location = var.region

  template {
    spec {
      service_account_name = google_service_account.budget_app.email
      containers {
        image = "gcr.io/${var.project_id}/budget-app:latest"
        
        env {
          name  = "INSTANCE_CONNECTION_NAME"
          value = google_sql_database_instance.budget_db.connection_name
        }
        
        env {
          name  = "DB_NAME"
          value = google_sql_database.budget_management.name
        }
        
        env {
          name  = "DB_USER"
          value = google_sql_user.budget_app.name
        }

        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

