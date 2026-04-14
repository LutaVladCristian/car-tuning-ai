locals {
  app_name        = "car-tuning-ai"
  env             = "dev"
  name_prefix     = "${local.app_name}-${local.env}"
}

resource "google_project_service" "apis" {
  for_each = toset([
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "compute.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "serviceusage.googleapis.com",
    "sqladmin.googleapis.com",
    "storage.googleapis.com",
  ])

  project = var.project_id
  service = each.key

  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "app" {
  location      = var.region
  repository_id = "${local.name_prefix}-containers"
  description   = "Dev containers for Car Tuning AI"
  format        = "DOCKER"

  depends_on = [google_project_service.apis]
}

resource "google_storage_bucket" "photos" {
  name                        = "${var.project_id}-${local.name_prefix}-photos"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false

  depends_on = [google_project_service.apis]
}

resource "google_storage_bucket" "models" {
  name                        = "${var.project_id}-${local.name_prefix}-models"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false

  depends_on = [google_project_service.apis]
}

resource "random_password" "database_password" {
  length  = 32
  special = true
}

resource "google_sql_database_instance" "postgres" {
  name             = "${local.name_prefix}-postgres"
  database_version = "POSTGRES_16"
  region           = var.region

  settings {
    tier              = "db-f1-micro"
    availability_type = "ZONAL"
    disk_type         = "PD_SSD"
    disk_size         = 10

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
    }

    ip_configuration {
      ipv4_enabled = true
    }
  }

  deletion_protection = true

  depends_on = [google_project_service.apis]
}

resource "google_sql_database" "app" {
  name     = var.database_name
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "app" {
  name     = var.database_user
  instance = google_sql_database_instance.postgres.name
  password = random_password.database_password.result
}

resource "google_secret_manager_secret" "database_url" {
  secret_id = "${local.name_prefix}-database-url"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "database_url" {
  secret = google_secret_manager_secret.database_url.id

  secret_data = "postgresql://${var.database_user}:${urlencode(random_password.database_password.result)}@/${var.database_name}?host=/cloudsql/${google_sql_database_instance.postgres.connection_name}"
}

resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "${local.name_prefix}-openai-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret" "firebase_project_id" {
  secret_id = "${local.name_prefix}-firebase-project-id"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_service_account" "backend" {
  account_id   = "${local.name_prefix}-backend"
  display_name = "Car Tuning AI dev backend"
}

resource "google_service_account" "frontend" {
  account_id   = "${local.name_prefix}-frontend"
  display_name = "Car Tuning AI dev frontend"
}

resource "google_service_account" "segmentation" {
  account_id   = "${local.name_prefix}-segmentation"
  display_name = "Car Tuning AI dev segmentation VM"
}

resource "google_service_account" "github_deployer" {
  account_id   = "ctai-dev-gh-deploy"
  display_name = "GitHub Actions dev deployer"
}

resource "google_project_iam_member" "github_deployer_roles" {
  for_each = toset([
    "roles/artifactregistry.writer",
    "roles/cloudsql.client",
    "roles/compute.admin",
    "roles/iam.serviceAccountUser",
    "roles/run.admin",
    "roles/secretmanager.secretAccessor",
    "roles/storage.admin",
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.github_deployer.email}"
}

resource "google_project_iam_member" "backend_roles" {
  for_each = toset([
    "roles/cloudsql.client",
    "roles/secretmanager.secretAccessor",
    "roles/storage.objectAdmin",
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "segmentation_roles" {
  for_each = toset([
    "roles/artifactregistry.reader",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/secretmanager.secretAccessor",
    "roles/storage.objectViewer",
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.segmentation.email}"
}

resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "${local.name_prefix}-github"
  display_name              = "GitHub Actions dev"
  description               = "Trust pool for GitHub Actions deploying dev."

  depends_on = [google_project_service.apis]
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github"
  display_name                       = "GitHub OIDC"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
    "attribute.ref"        = "assertion.ref"
  }

  attribute_condition = "assertion.repository == '${var.github_owner}/${var.github_repo}'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account_iam_member" "github_workload_identity_user" {
  service_account_id = google_service_account.github_deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/projects/${var.project_number}/locations/global/workloadIdentityPools/${google_iam_workload_identity_pool.github.workload_identity_pool_id}/attribute.repository/${var.github_owner}/${var.github_repo}"
}

resource "google_cloud_run_v2_service" "backend" {
  name     = "${local.name_prefix}-backend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.backend.email

    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }

    vpc_access {
      network_interfaces {
        network = "default"
      }

      egress = "PRIVATE_RANGES_ONLY"
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.postgres.connection_name]
      }
    }

    containers {
      image = var.backend_image

      env {
        name = "APP_ENV"
        value = local.env
      }

      env {
        name = "GCS_PHOTOS_BUCKET"
        value = google_storage_bucket.photos.name
      }

      env {
        name = "SEGMENTATION_MS_URL"
        value = "http://${google_compute_instance.segmentation.network_interface[0].network_ip}:8000"
      }

      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.database_url.secret_id
            version = "latest"
          }
        }
      }

      ports {
        container_port = 8001
      }

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }
    }
  }

  depends_on = [google_project_iam_member.backend_roles]
}

resource "google_cloud_run_v2_service" "frontend" {
  name     = "${local.name_prefix}-frontend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.frontend.email

    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }

    containers {
      image = var.frontend_image

      ports {
        container_port = 80
      }
    }
  }
}

resource "google_cloud_run_service_iam_member" "backend_public" {
  location = google_cloud_run_v2_service.backend.location
  project  = var.project_id
  service  = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_service_iam_member" "frontend_public" {
  location = google_cloud_run_v2_service.frontend.location
  project  = var.project_id
  service  = google_cloud_run_v2_service.frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_compute_firewall" "allow_backend_to_segmentation" {
  name    = "${local.name_prefix}-allow-segmentation"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["8000"]
  }

  source_ranges = ["10.0.0.0/8"]
  target_tags   = ["${local.name_prefix}-segmentation"]
}

resource "google_compute_instance" "segmentation" {
  name         = "${local.name_prefix}-segmentation"
  machine_type = var.segmentation_machine_type
  zone         = var.zone
  tags         = ["${local.name_prefix}-segmentation"]

  boot_disk {
    initialize_params {
      image = "cos-cloud/cos-stable"
      size  = 100
      type  = "pd-ssd"
    }
  }

  network_interface {
    network = "default"

    access_config {
      // Ephemeral public IP for outbound pulls during dev. Remove for a private NAT setup.
    }
  }

  guest_accelerator {
    type  = var.segmentation_accelerator_type
    count = var.segmentation_accelerator_count
  }

  scheduling {
    on_host_maintenance = "TERMINATE"
    automatic_restart   = true
  }

  service_account {
    email  = google_service_account.segmentation.email
    scopes = ["cloud-platform"]
  }

  metadata = {
    gce-container-declaration = yamlencode({
      spec = {
        containers = [{
          name  = "car-segmentation-ms"
          image = var.segmentation_image
          env = [
            {
              name  = "MODEL_BUCKET"
              value = google_storage_bucket.models.name
            },
            {
              name  = "WORKING_DIR"
              value = "/app"
            },
          ]
          ports = [{
            containerPort = 8000
            hostPort      = 8000
          }]
        }]
        restartPolicy = "Always"
      }
    })
    google-logging-enabled    = "true"
    google-monitoring-enabled = "true"
  }

  depends_on = [
    google_project_iam_member.segmentation_roles,
    google_project_service.apis,
  ]
}
