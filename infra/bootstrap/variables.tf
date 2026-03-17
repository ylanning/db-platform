variable "project_id" {
  type        = string
  description = "GCP project id"
}

variable "region" {
  type        = string
  default     = "europe-west2"
}

variable "tf_state_bucket" {
  type        = string
  description = "GCS bucket for Terraform state"
}

variable "github_actions_sa" {
  type        = string
  description = "GitHub Actions service account email"
}

variable "control_plane_sa" {
  type        = string
  description = "Control plane service account email"
}
