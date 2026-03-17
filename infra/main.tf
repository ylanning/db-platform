terraform {
  backend "gcs" {}

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "6.13.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "6.13.0"
    }
  }
}
provider "google" {
  project = var.project_id
  region  = var.region
}


resource "google_sql_database_instance" "postgres" {
  name             = var.instance_id
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier              = var.db_tier
    availability_type = "REGIONAL"
    backup_configuration {
      enabled                        = true
      start_time                     = var.backup_start_time
      point_in_time_recovery_enabled = true
    }
  }
}

resource "google_sql_database_instance" "replica" {
  count                = var.enable_replica ? 1 : 0
  name                 = var.replica_instance_id
  database_version     = "POSTGRES_15"
  region               = var.region
  master_instance_name = google_sql_database_instance.postgres.name

  replica_configuration {
    failover_target = false
  }
  settings {
    tier = var.db_tier
  }
}

resource "google_storage_bucket" "backups" {
  location                    = var.region
  name                        = var.backup_bucket
  uniform_bucket_level_access = true
}






resource "google_service_account" "control_plane" {
  account_id   = "dbp-control-plane"
  display_name = "DBP Control Plane"
}

resource "google_project_iam_member" "sql_admin" {
  project = var.project_id
  role    = "roles/cloudsql.admin"
  member  = "serviceAccount:${google_service_account.control_plane.email}"
}

resource "google_project_iam_member" "secret_manager" {
  project = var.project_id
  role    = "roles/secretmanager.admin"
  member  = "serviceAccount:${google_service_account.control_plane.email}"
}

resource "google_project_iam_member" "storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.control_plane.email}"
}

resource "google_artifact_registry_repository" "docker" {
  format        = "DOCKER"
  repository_id = var.artifact_repo
  location      = var.region
}

resource "google_cloud_run_service" "control_plane" {
  location = var.region
  name     = var.cloud_run_service_name

  template {
    spec {
      service_account_name = google_service_account.control_plane.email
      containers {
        image = var.cloud_run_image
        env {
          name  = "DBP_PROJECT_ID"
          value = var.project_id
        }
        env {
          name  = "DBP_REGION"
          value = var.region
        }
        env {
          name  = "DBP_INSTANCE_ID"
          value = var.instance_id
        }
        env {
          name  = "DBP_BACKUP_BUCKET"
          value = var.backup_bucket
        }
        env {
          name  = "DBP_SECRET_PREFIX"
          value = var.secret_prefix
        }
      }
    }
  }
}

resource "google_cloud_run_service_iam_member" "scheduler_invoker" {
  location = google_cloud_run_service.control_plane.location
  role     = "roles/run.invoker"
  service  = google_cloud_run_service.control_plane.name
  member   = "serviceAccount:${google_service_account.scheduler.email}"
}

resource "google_service_account" "scheduler" {
  account_id   = "dbp-backup-scheduler"
  display_name = "DBP Backup Scheduler"
}

resource "google_cloud_scheduler_job" "daily_backup" {
  name        = "dbp-daily-backup"
  description = "Trigger on-demand Cloud SQL backup via control plane"
  schedule    = "0 6 * * *"
  time_zone   = "Europe/London"

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_service.control_plane.status[0].url}/backup"

    oidc_token {
      service_account_email = google_service_account.scheduler.email
    }
  }
}

# -----------------------------------------------------------------------------
# GitHub Actions - Workload Identity Federation
# -----------------------------------------------------------------------------

resource "google_service_account" "github_actions" {
  account_id   = "github-actions"
  display_name = "GitHub Actions"
}

resource "google_project_iam_member" "github_actions_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

resource "google_project_iam_member" "github_actions_artifact_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

resource "google_project_iam_member" "github_actions_sa_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github"
  display_name              = "GitHub Actions"
  description               = "Identity pool for GitHub Actions"
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub Provider"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }

  attribute_condition = "assertion.repository == \"${var.github_repo}\""

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account_iam_member" "github_actions_wif" {
  service_account_id = google_service_account.github_actions.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repo}"
}
