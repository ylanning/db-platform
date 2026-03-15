# DB Platform Control Plane (Cloud SQL)

A mini DBaaS control plane to provision Cloud SQL Postgres databases, manage credentials via Secret Manager, and trigger backups.

## Endpoints
- `POST /provision`
- `POST /deprovision`
- `GET /status/{db_id}`
- `POST /backup`
- `POST /rotate-credentials`

## Config
Set environment variables (prefix `DBP_`):
- `DBP_PROJECT_ID`
- `DBP_REGION` (default `europe-west2`)
- `DBP_INSTANCE_ID`
- `DBP_BACKUP_BUCKET`
- `DBP_SECRET_PREFIX` (default `dbp`)

## Local run
```bash
poetry install
poetry run uvicorn app.main:app --reload
```

## Terraform
```bash
cd infra
terraform init
terraform apply \
  -var project_id=YOUR_PROJECT \
  -var instance_id=YOUR_INSTANCE \
  -var backup_bucket=YOUR_BUCKET \
  -var backup_start_time=06:00 \
  -var cloud_run_image=YOUR_IMAGE
```

## Local-time backup scheduling
Terraform deploys the API to Cloud Run and creates a Cloud Scheduler job that calls `/backup` daily at 06:00 Europe/London time. The scheduler service account is granted `roles/run.invoker` on the Cloud Run service.

## Design decision: Terraform vs Python
Use Terraform for long-lived, shared infrastructure (Cloud SQL instance, networking, IAM, automated backup policy).
Use the Python control plane for runtime tenant actions (create/drop databases, create/rotate users, on-demand backups).

## CI/CD: build + deploy
The workflow `/db-platform/Documents/New project/.github/workflows/build-and-deploy.yml` builds the Docker image, pushes to Artifact Registry, then runs Terraform apply.
Required GitHub secrets:
- `GCP_PROJECT_ID`
- `GCP_REGION` (e.g., `europe-west2`)
- `GCP_WIF_PROVIDER`
- `GCP_WIF_SERVICE_ACCOUNT`
- `CLOUDSQL_INSTANCE_ID`
- `BACKUP_BUCKET`

## Diagrams
See `/db-platform/docs/diagrams.md` for architecture, CI/CD, runtime flows, and error paths.

## HA and failover
Cloud SQL is configured with `availability_type = REGIONAL` (synchronous standby in another zone) for automatic failover. This provides low RTO without changing connection strings; backups remain for disaster recovery and PITR.

## Read replica (optional)
You can enable a read replica for manual promotion during incidents:
```bash
terraform apply \
  -var enable_replica=true \
  -var replica_instance_id=dbp-replica
```

## Replica promotion runbook (manual)
1. Identify primary outage via monitoring/alerts.
2. Promote the replica to a standalone instance:
   - `gcloud sql instances promote-replica REPLICA_INSTANCE_ID`
   - Or Cloud Console → Cloud SQL → select replica → Promote replica
3. Update application connection strings to the promoted instance (or swap DNS).
4. Verify read/write health and resume traffic.
5. Recreate a new replica for redundancy.

## RPO/RTO comparison (high level)
| Option | RPO | RTO | Failover | Cost |
| --- | --- | --- | --- | --- |
| HA (regional) | Low | Low | Automatic | Higher |
| Read replica | Moderate | Moderate | Manual promotion | Moderate |
| Backups/PITR | Higher | Higher | Manual restore | Lowest |

Selection guidance: use HA for user-facing critical services, read replicas for cost-conscious resilience with manual failover, and backups/PITR for disaster recovery and data correction.
