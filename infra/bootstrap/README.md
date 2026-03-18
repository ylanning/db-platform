# Terraform bootstrap (state bucket + IAM + APIs)

Run this once to create the Terraform state bucket, enable required APIs, and grant GitHub Actions access.

```bash
cd infra/bootstrap
terraform init
terraform apply \
  -var project_id=YOUR_PROJECT_ID \
  -var region=europe-west2 \
  -var tf_state_bucket=tfstate-data-platform-490117-2025 \
  -var github_actions_sa=github-actions@data-platform-490117.iam.gserviceaccount.com \
  -var control_plane_sa=dbp-control-plane@data-platform-490117.iam.gserviceaccount.com \
  -var scheduler_sa=dbp-backup-scheduler@data-platform-490117.iam.gserviceaccount.com \
  -var cloud_run_url=https://dbp-control-plane-926377652927.europe-west2.run.app
```

Then use the bucket in the main Terraform backend config:

```bash
cd infra
terraform init -backend-config=backend.hcl
```
