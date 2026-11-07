#!/bin/bash
#MISE dir="cmd/scraper/"
#MISE description="Create Lambda function"
set -e

CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
  go build -ldflags="-s -w" -tags lambda.norpc -o bootstrap main.go

chmod +x bootstrap
zip -j function.zip bootstrap

env_vars="Variables={"
env_vars+="DYNAMODB_ENDPOINT=$DYNAMODB_ENDPOINT,"
env_vars+="AWS_REGION=$AWS_REGION,"
env_vars+="MOVIES_TABLE_NAME=$MOVIES_TABLE_NAME,"
env_vars+="TMDB_API_KEY=$TMDB_API_KEY,"
env_vars+="}"

awslocal lambda create-function \
  --function-name scraper \
  --runtime provided.al2023 \
  --handler bootstrap \
  --zip-file fileb://function.zip \
  --role arn:aws:iam::000000000000:role/irrelevant \
  --environment "$env_vars" \
  --memory-size 512 \
  --timeout 30
