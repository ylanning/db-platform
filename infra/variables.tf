variable "project_id" {
  type        = string
  description = "GCP project id"
}

variable "project_number" {
  type        = string
  description = "GCP project number (run: gcloud projects describe PROJECT_ID --format='value(projectNumber)')"
}

variable "region" {
  type    = string
  default = "europe-west2"
}

variable "instance_id" {
  type        = string
  description = "Cloud SQL instance id"
}

variable "db_tier" {
  type    = string
  default = "db-custom-1-3840"
}

variable "backup_bucket" {
  type        = string
  description = "GCS bucket for backups"
}

variable "backup_start_time" {
  type        = string
  default     = "06:00"
  description = "Daily automated backup start time (UTC, HH:MM)"
}

variable "cloud_run_image" {
  type        = string
  description = "Container image for the control plane API"
}

variable "cloud_run_service_name" {
  type        = string
  default     = "dbp-control-plane"
  description = "Cloud Run service name"
}

variable "cloud_run_url" {
  type        = string
  default     = ""
  description = "Full Cloud Run URL (e.g., https://...run.app). Required for scheduler job if service URL isn't available from the provider."
}

variable "secret_prefix" {
  type        = string
  default     = "dbp"
  description = "Secret name prefix"
}

variable "artifact_repo" {
  type        = string
  default     = "dbp-control-plane"
  description = "Artifact Registry repository id"
}

variable "enable_replica" {
  type        = bool
  default     = false
  description = "Whether to create a read replica"
}

variable "replica_instance_id" {
  type        = string
  default     = "dbp-replica"
  description = "Read replica instance id"
}

variable "github_repo" {
  type        = string
  description = "GitHub repository in format 'owner/repo'"
}
