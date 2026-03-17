output "instance_id" {
  value = google_sql_database_instance.postgres.name
}

output "service_account_email" {
  value = google_service_account.control_plane.email
}

output "backup_bucket" {
  value = google_storage_bucket.backups.name
}

output "scheduler_service_account_email"{
  value = google_service_account.scheduler.name
}

output "cloud_run_url" {
  value = google_cloud_run_service.control_plane.status[0].url
}

output "artifact_repo" {
  value = google_artifact_registry_repository.docker.repository_id
}

output "replica_instance_id" {
  value       = var.enable_replica ? google_sql_database_instance.replica[0].name : null
  description = "Read replica instance id (if enabled)"
}

output "wif_provider" {
  value       = "projects/${var.project_number}/locations/global/workloadIdentityPools/${google_iam_workload_identity_pool.github.workload_identity_pool_id}/providers/${google_iam_workload_identity_pool_provider.github.workload_identity_pool_provider_id}"
  description = "Workload Identity Provider for GitHub Actions (use as WIF_PROVIDER secret)"
}

output "wif_service_account" {
  value       = google_service_account.github_actions.email
  description = "Service account for GitHub Actions (use as WIF_SERVICE_ACCOUNT secret)"
}
