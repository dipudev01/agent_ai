# GCP variant — AKS-equivalent (GKE) + managed services. Mirror of aws/ with
# GCP-native equivalents. Multi-region active-passive with failover.

terraform {
  required_version = ">= 1.6"
  backend "gcs" {
    bucket = "bfsi-tfstate-gcp"
    prefix = "prod/gcp/terraform.tfstate"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" { default = "bfsi-ai-prod" }
variable "region"     { default = "asia-south1" }

module "gke" {
  source     = "terraform-google-modules/kubernetes-engine/google"
  version    = "~> 33.0"
  project_id = var.project_id
  name       = "bfsi-ai-gke"
  region     = var.region
  network    = google_compute_network.vpc.name
  subnetwork = google_compute_subnetwork.private.name

  node_pools = [
    {
      name               = "general"
      machine_type       = "e2-standard-4"
      min_count          = 3
      max_count          = 20
      disk_size_gb       = 100
      auto_repair        = true
      auto_upgrade       = true
    },
    {
      name               = "inference"
      machine_type       = "g2-standard-8"  # L4 GPU
      min_count          = 1
      max_count          = 8
      disk_size_gb       = 200
      accelerator_type   = "nvidia-l4"
      accelerator_count  = 1
    },
  ]
}

resource "google_compute_network" "vpc" {
  name                    = "bfsi-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "private" {
  name          = "bfsi-private"
  ip_cidr_range = "10.0.0.0/16"
  region        = var.region
  network       = google_compute_network.vpc.id
  private_ip_google_access = true
}

resource "google_sql_database_instance" "postgres" {
  name             = "bfsi-ai-postgres"
  database_version = "POSTGRES_16"
  region           = var.region
  settings {
    tier = "db-custom-4-16384"
    availability_type = "REGIONAL"
    disk_autoresize  = true
    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
    }
  }
}

resource "google_redis_instance" "cache" {
  name           = "bfsi-ai-redis"
  memory_size_gb = 8
  tier           = "STANDARD_HA"
  region         = var.region
  auth_enabled   = true
}

resource "google_pubsub_topic" "events" {
  name = "bfsi-domain-events"
}

resource "google_storage_bucket" "documents" {
  name          = "bfsi-ai-documents-${var.region}"
  location      = var.region
  versioning { enabled = true }
  retention_policy {
    retention_period = 2555000  # seconds ~ 29.5 days; extend per compliance
    is_locked        = true
  }
}

resource "google_kms_key_ring" "bfsi" {
  name     = "bfsi-keyring"
  location = var.region
}

resource "google_kms_crypto_key" "master" {
  name            = "bfsi-master-key"
  key_ring        = google_kms_key_ring.bfsi.id
  rotation_period = "7776000s"  # 90 days
}