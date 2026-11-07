data "cloudflare_zone" "this" {
  filter = {
    name = var.cloudflare_zone
  }
}

# Existe desde antes de OpenTofu: se importa con
#   tofu import cloudflare_dns_record.app <zone_id>/<record_id>
resource "cloudflare_dns_record" "app" {
  zone_id = data.cloudflare_zone.this.id
  name    = var.domain_name
  type    = "CNAME"
  content = aws_cloudfront_distribution.this.domain_name
  proxied = var.dns_proxied
  ttl     = 1 # 1 = automático; obligatorio con proxied
}
