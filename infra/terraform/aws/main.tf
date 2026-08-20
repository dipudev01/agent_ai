# Production AWS infrastructure for the BFSI AI Agent Platform.
# State is remote (S3 + DynamoDB lock). Multi-AZ by default.

terraform {
  required_version = ">= 1.6"
  backend "s3" {
    bucket         = "bfsi-tfstate"
    key            = "prod/aws/terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "bfsi-tfstate-lock"
    encrypt        = true
  }
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = {
      Environment = var.environment
      Platform    = "bfsi-ai-agent"
      CostCenter  = var.cost_center
    }
  }
}

variable "region"       { default = "ap-south-1" }
variable "environment"  { default = "prod" }
variable "cost_center"  { default = "fintech-ai" }
variable "cluster_name" { default = "bfsi-ai" }

# --- EKS ---
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "${var.cluster_name}-${var.environment}"
  cluster_version = "1.29"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  enable_irsa = true

  eks_managed_node_groups = {
    general = {
      desired_size = 3
      min_size     = 3
      max_size     = 10
      instance_types = ["m6i.large"]
      capacity_type = "ON_DEMAND"
    }
    inference = {
      desired_size = 2
      min_size     = 1
      max_size     = 6
      instance_types = ["g5.2xlarge"]  # GPU for self-hosted models
      capacity_type = "SPOT"
      labels = { node-role = "gpu-inference" }
    }
  }
}

# --- VPC with private subnets only ---
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.cluster_name}-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["${var.region}a", "${var.region}b", "${var.region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway   = true
  single_nat_gateway   = false
  enable_vpn_gateway   = true
  enable_dns_hostnames = true
}

# --- Managed services ---
resource "aws_db_instance" "postgres" {
  identifier     = "bfsi-ai-postgres"
  engine         = "postgres"
  engine_version = "16.3"
  instance_class = "db.r6g.large"
  multi_az       = true
  db_name        = "bfsi_ai"
  username       = var.db_user
  password       = var.db_password  # from secrets in CI
  storage_encrypted = true
  backup_retention_period = 35
  deletion_protection = true
  skip_final_snapshot   = false
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "bfsi-ai-redis"
  engine               = "redis"
  node_type            = "cache.r6g.large"
  num_cache_nodes      = 3
  parameter_group_name = "default.redis7"
  multi_az_enabled     = true
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
}

module "msk" {
  source  = "terraform-aws-modules/msk/aws"
  version = "~> 3.0"
  name    = "bfsi-ai-kafka"
  kafka_version = "3.6.0"
  number_of_broker_nodes = 3
  broker_node_instance_type = "kafka.m5.large"
  encryption_in_transit_client_broker = "TLS"
  encryption_at_rest_kms_key_arn = var.kms_key_arn
}

resource "aws_opensearch_domain" "search" {
  domain_name           = "bfsi-ai-search"
  engine_version        = "OpenSearch_2.13"
  cluster_config {
    instance_type  = "r6g.large.search"
    instance_count = 3
  }
  encrypt_at_rest { enabled = true }
  node_to_node_encryption { enabled = true }
  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "TLSSecurityPolicy-TLS-1-2-2019-07"
  }
}

resource "aws_s3_bucket" "documents" {
  bucket        = "bfsi-ai-documents-${var.environment}"
  force_destroy = false
}

resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_object_lock_configuration" "audit" {
  bucket = aws_s3_bucket.documents.id
  rule {
    default_retention {
      mode = "COMPLIANCE"
      days = var.audit_retention_days  # 7 years for audit evidence
    }
  }
}

resource "aws_kms_key" "bfsi" {
  description             = "BFSI AI platform master key"
  enable_key_rotation     = true
  deletion_window_in_days = 30
}

resource "aws_kms_alias" "bfsi" {
  name          = "alias/bfsi-master"
  target_key_id = aws_kms_key.bfsi.key_id
}

output "cluster_endpoint" { value = module.eks.cluster_endpoint }
output "postgres_endpoint" { value = aws_db_instance.postgres.endpoint }