default:
    @just --list

run-web:
    go run ./cmd/web/

create-function:
    cd cmd/scraper && \
    CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" -tags lambda.norpc -o bootstrap main.go && \
    chmod +x bootstrap && \
    zip -j function.zip bootstrap && \
    awslocal lambda create-function \
    --function-name scraper \
    --runtime provided.al2 \
    --handler bootstrap \
    --zip-file fileb://function.zip \
    --role arn:aws:iam::000000000000:role/irrelevant \
    --environment file://environment.json \
    --memory-size 512 \
    --timeout 30

delete-function:
    awslocal lambda delete-function --function-name scraper

invoke-lambda:
    awslocal lambda invoke --function-name scraper out.json

list-movies:
    awslocal dynamodb scan \
      --table-name Movies \
      --query "Items[].{DateTitle: DateTitle.S, Fecha: Date.S, Titulo: Title.S, Centro: CenterSlug.S, TTL: ExpiresAt.N}" \
      --output table

setup-db:
    docker compose down -v
    docker compose up -d
    @sleep 2
    uv run scripts/create_db.py --env local

htmx_version := "2.0.8"
setup-ui:
    curl -L https://cdn.jsdelivr.net/npm/htmx.org@{{htmx_version}}/dist/htmx.min.js -o ui/static/js/htmx.min.js

CLOUDFRONT_DIST_ID ?= ""

deploy-static:
    aws s3 sync ui/static/css/ s3://agenda-cultural-prod-frontend-bucket/css/ --delete
    aws s3 sync ui/static/js/ s3://agenda-cultural-prod-frontend-bucket/js/ --delete

invalidate-cache:
    aws cloudfront create-invalidation --distribution-id {{CLOUDFRONT_DIST_ID}} --paths "/*"
