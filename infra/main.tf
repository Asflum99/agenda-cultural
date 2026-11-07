provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = "agenda-cultural"
      ManagedBy = "opentofu"
    }
  }
}

provider "cloudflare" {}

data "aws_caller_identity" "this" {}

locals {
  account_id = data.aws_caller_identity.this.account_id
  tmdb_param = "/agenda-cultural/tmdb-api-key"
}

# ── DynamoDB ──────────────────────────────────────────────────────────────

resource "aws_dynamodb_table" "movies" {
  name           = var.movies_table_name
  billing_mode   = "PROVISIONED"
  read_capacity  = var.read_capacity
  write_capacity = var.write_capacity
  hash_key       = "CenterSlug"
  range_key      = "DateTitle"

  attribute {
    name = "CenterSlug"
    type = "S"
  }

  attribute {
    name = "DateTitle"
    type = "S"
  }

  ttl {
    attribute_name = "ExpiresAt"
    enabled        = true
  }
}

# ── IAM ───────────────────────────────────────────────────────────────────

data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "web" {
  name               = "agenda-cultural-web"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role_policy_attachment" "web_logs" {
  role       = aws_iam_role.web.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "web" {
  statement {
    actions = [
      "dynamodb:BatchGetItem",
      "dynamodb:GetItem",
      "dynamodb:Query",
      "dynamodb:Scan",
    ]
    resources = [
      aws_dynamodb_table.movies.arn,
      "${aws_dynamodb_table.movies.arn}/index/*",
    ]
  }
}

resource "aws_iam_role_policy" "web" {
  name   = "movies-read"
  role   = aws_iam_role.web.id
  policy = data.aws_iam_policy_document.web.json
}

resource "aws_iam_role" "scraper" {
  name               = "agenda-cultural-scraper"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role_policy_attachment" "scraper_logs" {
  role       = aws_iam_role.scraper.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "scraper" {
  statement {
    actions = [
      "dynamodb:BatchWriteItem",
      "dynamodb:DeleteItem",
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:Query",
      "dynamodb:Scan",
      "dynamodb:UpdateItem",
    ]
    resources = [
      aws_dynamodb_table.movies.arn,
      "${aws_dynamodb_table.movies.arn}/index/*",
    ]
  }

  statement {
    actions   = ["ssm:GetParameter"]
    resources = ["arn:aws:ssm:${var.aws_region}:${local.account_id}:parameter${local.tmdb_param}"]
  }

  statement {
    actions   = ["cloudfront:CreateInvalidation"]
    resources = ["arn:aws:cloudfront::${local.account_id}:distribution/${aws_cloudfront_distribution.this.id}"]
  }
}

resource "aws_iam_role_policy" "scraper" {
  name   = "scraper"
  role   = aws_iam_role.scraper.id
  policy = data.aws_iam_policy_document.scraper.json
}

# ── Lambdas ───────────────────────────────────────────────────────────────

# Creados antes que las funciones para evitar que Lambda los cree sin retención.
resource "aws_cloudwatch_log_group" "web" {
  name              = "/aws/lambda/AgendaCulturalWeb"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "scraper" {
  name              = "/aws/lambda/MoviesScraper"
  retention_in_days = 7
}

data "archive_file" "web" {
  type        = "zip"
  source_file = "build/web/bootstrap"
  output_path = "build/web.zip"
}

resource "aws_lambda_function" "web" {
  function_name    = "AgendaCulturalWeb"
  role             = aws_iam_role.web.arn
  runtime          = "provided.al2023"
  handler          = "bootstrap"
  architectures    = ["x86_64"]
  memory_size      = 256
  timeout          = 5
  filename         = data.archive_file.web.output_path
  source_code_hash = data.archive_file.web.output_base64sha256

  environment {
    variables = {
      MOVIES_TABLE_NAME    = aws_dynamodb_table.movies.name
      ORIGIN_VERIFY_SECRET = var.origin_verify_secret
    }
  }

  depends_on = [aws_cloudwatch_log_group.web]
}

data "archive_file" "scraper" {
  type        = "zip"
  source_file = "build/scraper/bootstrap"
  output_path = "build/scraper.zip"
}

resource "aws_lambda_function" "scraper" {
  function_name    = "MoviesScraper"
  role             = aws_iam_role.scraper.arn
  runtime          = "provided.al2023"
  handler          = "bootstrap"
  architectures    = ["x86_64"]
  memory_size      = 128
  timeout          = 30
  filename         = data.archive_file.scraper.output_path
  source_code_hash = data.archive_file.scraper.output_base64sha256

  environment {
    variables = {
      CLOUDFRONT_DISTRIBUTION_ID = aws_cloudfront_distribution.this.id
    }
  }

  depends_on = [aws_cloudwatch_log_group.scraper]
}

# ── EventBridge (scraper diario) ──────────────────────────────────────────

resource "aws_cloudwatch_event_rule" "daily" {
  name                = "agenda-cultural-daily"
  schedule_expression = "cron(0 6 * * ? *)"
}

resource "aws_cloudwatch_event_target" "scraper" {
  rule = aws_cloudwatch_event_rule.daily.name
  arn  = aws_lambda_function.scraper.arn

  depends_on = [aws_lambda_permission.events]
}

resource "aws_lambda_permission" "events" {
  statement_id  = "AllowEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.scraper.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily.arn
}
