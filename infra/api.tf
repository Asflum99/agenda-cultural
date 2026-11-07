resource "aws_cloudwatch_log_group" "api" {
  name              = "/aws/apigateway/agenda-cultural"
  retention_in_days = 7
}

resource "aws_apigatewayv2_api" "this" {
  name          = "agenda-cultural"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "web" {
  api_id           = aws_apigatewayv2_api.this.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.web.invoke_arn

  # El lambda Go espera el evento APIGatewayV2HTTPRequest (payload 2.0).
  payload_format_version = "2.0"
}

# Cada ruta nueva en internal/webapp/app.go necesita su aws_apigatewayv2_route.
# Sin ella, API Gateway responde 404 sin invocar la Lambda ni dejar rastro en sus logs.
resource "aws_apigatewayv2_route" "home" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "GET /"
  target    = "integrations/${aws_apigatewayv2_integration.web.id}"
}

resource "aws_apigatewayv2_route" "about" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "GET /acerca-de"
  target    = "integrations/${aws_apigatewayv2_integration.web.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.this.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
      userAgent      = "$context.identity.userAgent"
    })
  }
}

resource "aws_lambda_permission" "api" {
  statement_id  = "AllowHttpApi"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.web.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*"
}
