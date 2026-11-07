variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "certificate_arn" {
  description = "ARN del certificado ACM del dominio (tiene que estar en us-east-1)"
  type        = string
}

variable "origin_verify_secret" {
  description = "Header que CloudFront manda a API Gateway para validar el origen"
  type        = string
  sensitive   = true
}

variable "domain_name" {
  type    = string
  default = "agendacultural.qzz.io"
}

variable "cloudflare_zone" {
  description = "Zona de Cloudflare que contiene el CNAME (qzz.io da subdominios como zonas propias)"
  type        = string
  default     = "agendacultural.qzz.io"
}

variable "dns_proxied" {
  description = "Nube naranja de Cloudflare sobre el CNAME"
  type        = bool
  default     = true
}

variable "movies_table_name" {
  type    = string
  default = "Movies"
}

variable "read_capacity" {
  type    = number
  default = 5
}

variable "write_capacity" {
  type    = number
  default = 5
}

variable "frontend_bucket" {
  type    = string
  default = "agenda-cultural-prod-frontend-bucket"
}
