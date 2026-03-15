# Diagrams

## Architecture (Infrastructure + Runtime)
```mermaid
flowchart LR
  subgraph "IaC (Terraform)"
    VPC["VPC + Subnet"]
    SQL["Cloud SQL Postgres Instance (HA Regional)"]
    REPLICA["Read Replica (Optional)"]
    SA["Control Plane Service Account"]
    SM["Secret Manager"]
    GCS["GCS Backup Bucket"]
    SCH["Cloud Scheduler (06:00 Europe/London)"]
    SCHED_SA["Scheduler Service Account"]
  end

  subgraph "Runtime"
    CR["Cloud Run: Control Plane API"]
  end

  SCH -->|OIDC token| CR
  SCHED_SA -.->|roles/run.invoker| CR

  CR -->|Cloud SQL Admin API| SQL
  CR -->|Create/Update Secret| SM
  CR -->|Trigger Backup| SQL
  SQL -->|Automated Backups| GCS
  SQL -->|Streaming Replication| REPLICA

  VPC --> SQL
  SA --> CR
```

## CI/CD Workflow
```mermaid
flowchart LR
  subgraph "GitHub Actions (on push to main)"
    GIT["Checkout code"]
    TFINIT["Terraform init"]
    TFREPO["Terraform apply (target repo)"]
    TFOUT["terraform output artifact_repo"]
    DOCKER["Build + push Docker image"]
    TFAPPLY["Terraform apply (full infra)"]
  end

  subgraph "GCP"
    AR["Artifact Registry (Docker repo)"]
    CR["Cloud Run (Control Plane API)"]
    SQL["Cloud SQL Postgres"]
    SCH["Cloud Scheduler (06:00 Europe/London)"]
  end

  GIT --> TFINIT --> TFREPO --> AR
  TFREPO --> TFOUT
  TFOUT --> DOCKER --> AR
  DOCKER --> TFAPPLY --> CR
  TFAPPLY --> SQL
  SCH -->|POST /backup| CR
```

## Provisioning Flow
```mermaid
sequenceDiagram
  participant Client
  participant API as Control Plane API
  participant SQL as Cloud SQL Admin API
  participant SM as Secret Manager

  Client->>API: POST /provision {db_id, owner}
  API->>SQL: create database
  API->>SQL: create user + password
  API->>SM: store connection string
  API-->>Client: 200 provisioned + secret name
```

## Backup Flow (Scheduled + On-demand)
```mermaid
sequenceDiagram
  participant Scheduler as Cloud Scheduler (06:00 Europe/London)
  participant Client
  participant API as Control Plane API
  participant SQL as Cloud SQL Admin API

  Scheduler->>API: POST /backup (OIDC)
  API->>SQL: trigger backup
  API-->>Scheduler: 200 started + backup_id

  Client->>API: POST /backup
  API->>SQL: trigger backup
  API-->>Client: 200 started + backup_id
```

## Deprovision Flow
```mermaid
sequenceDiagram
  participant Client
  participant API as Control Plane API
  participant SQL as Cloud SQL Admin API
  participant SM as Secret Manager

  Client->>API: POST /deprovision {db_id, owner}
  API->>SQL: delete database (ignore if missing)
  API->>SQL: delete user (ignore if missing)
  API->>SM: delete secret (ignore errors)
  API-->>Client: 200 deprovisioned
```

## Rotate Credentials Flow
```mermaid
sequenceDiagram
  participant Client
  participant API as Control Plane API
  participant SQL as Cloud SQL Admin API
  participant SM as Secret Manager

  Client->>API: POST /rotate-credentials {db_id}
  API->>SQL: update user password
  API->>SM: store new connection string
  API-->>Client: 200 rotated + secret name
```

## Error: Provision Conflict
```mermaid
sequenceDiagram
  participant Client
  participant API as Control Plane API
  participant SQL as Cloud SQL Admin API

  Client->>API: POST /provision {db_id}
  API->>SQL: create database
  SQL-->>API: 409 Already Exists
  API-->>Client: 409 Conflict (db_id already exists)
```

## Error: Backup Upstream Failure
```mermaid
sequenceDiagram
  participant Client
  participant API as Control Plane API
  participant SQL as Cloud SQL Admin API

  Client->>API: POST /backup
  API->>SQL: trigger backup
  SQL-->>API: 500/503 error
  API-->>Client: 502 Bad Gateway (upstream failure)
```
