terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "6.13.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_storage_bucket" "tf_state" {
  name                        = var.tf_state_bucket
  location                    = var.region
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }
}

resource "google_storage_bucket_iam_member" "github_actions" {
  bucket = google_storage_bucket.tf_state.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.github_actions_sa}"
}
