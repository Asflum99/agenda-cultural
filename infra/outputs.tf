output "distribution_domain" {
  value = aws_cloudfront_distribution.this.domain_name
}

output "distribution_id" {
  value = aws_cloudfront_distribution.this.id
}

output "web_function_url" {
  value = aws_lambda_function_url.web.function_url
}

output "frontend_bucket" {
  value = aws_s3_bucket.frontend.bucket
}

output "movies_table" {
  value = aws_dynamodb_table.movies.name
}
