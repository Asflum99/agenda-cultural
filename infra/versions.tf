terraform {
  required_version = ">= 1.10"

  backend "s3" {
    bucket       = "agenda-cultural-tfstate"
    key          = "prod/terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.70"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.28"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.8"
    }
  }
}
