output "distribution_domain" {
  value = aws_cloudfront_distribution.this.domain_name
}

output "distribution_id" {
  value = aws_cloudfront_distribution.this.id
}

output "api_endpoint" {
  value = aws_apigatewayv2_api.this.api_endpoint
}

output "frontend_bucket" {
  value = aws_s3_bucket.frontend.bucket
}

output "movies_table" {
  value = aws_dynamodb_table.movies.name
}
