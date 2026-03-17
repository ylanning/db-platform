# Terraform bootstrap (state bucket + IAM)

Run this once to create the Terraform state bucket and grant GitHub Actions access.

```bash
cd infra/bootstrap
terraform init
terraform apply \
  -var project_id=YOUR_PROJECT_ID \
  -var region=europe-west2 \
  -var tf_state_bucket=tf-state-data-platform \
  -var github_actions_sa=github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

Then use the bucket in the main Terraform backend config:

```bash
cd infra
terraform init -backend-config=backend.hcl
```
