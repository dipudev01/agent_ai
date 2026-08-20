# On-premises / private cloud variant using K8s-native operators and
# HashiCorp Vault for secrets. No cloud vendor dependencies.

terraform {
  required_version = ">= 1.6"
  backend "local" { path = "terraform.tfstate" }
}

variable "cluster_endpoint" { default = "https://k8s.bfsi.internal:6443" }
variable "vault_addr"       { default = "https://vault.bfsi.internal:8200" }

# Use the kubernetes provider directly for on-prem clusters.
provider "kubernetes" {
  host = var.cluster_endpoint
  cluster_ca_certificate = file("${path.module}/ca.crt")
  client_certificate     = file("${path.module}/client.crt")
  client_key             = file("${path.module}/client.key")
}

# Stateful PostgreSQL via operator (CloudNativePG) with backups to NFS/object store.
resource "kubernetes_manifest" "cnpg_cluster" {
  manifest = {
    apiVersion = "postgresql.cnpg.io/v1"
    kind       = "Cluster"
    metadata = { name = "bfsi-postgres", namespace = "bfsi" }
    spec = {
      instances = 3
      storage = {
        size = "100Gi"
        storageClass = "gp3-ssd"
      }
      backup = {
        barmanObjectStore = {
          destinationPath = "s3://bfsi-backups"
          retentionPolicy = "30d"
        }
      }
      monitoring = { enablePodMonitor = true }
    }
  }
}

resource "kubernetes_manifest" "redis_ha" {
  manifest = {
    apiVersion = "redis.redis.opstreelabs.in/v1beta1"
    kind       = "Redis"
    metadata = { name = "bfsi-redis", namespace = "bfsi" }
    spec = {
      size          = 3
      kubernetesConfig = { image = "redis:7.2" }
      storage = { size = "20Gi" }
    }
  }
}

resource "kubernetes_manifest" "kafka_cr" {
  manifest = {
    apiVersion = "kafka.strimzi.io/v1beta2"
    kind       = "Kafka"
    metadata = { name = "bfsi-kafka", namespace = "bfsi" }
    spec = {
      kafka = {
        replicas = 3
        storage = { type = "jbod", volumes = [{ type = "persistent-claim", size = "50Gi" }] }
        listeners = [{ name = "plain", port = 9092, type = "internal", tls = false }]
      }
      zookeeper = { replicas = 3, storage = { type = "persistent-claim", size = "20Gi" } }
    }
  }
}

resource "vault_mount" "bfsi" {
  path = "bfsi"
  type = "kv-v2"
}

resource "vault_kv_secret_v2" "jwt_secret" {
  mount = vault_mount.bfsi.path
  name  = "app/jwt"
  data_json = jsonencode({ value = var.jwt_secret })
}