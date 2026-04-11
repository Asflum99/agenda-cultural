# Agenda Cultural - Developer Notes

## Commands

```bash
just run-web          # Run Go web server on :8080
just setup-db         # Start Docker Compose + create DynamoDB tables
just create-lambda   # Build Lambda zip and deploy to localstack
just invoke-lambda   # Test Lambda function
just list-movies     # Query Movies table from DynamoDB
```

## Environment

- **Go**: 1.25, modules
- **Python**: 3.13, uv for dependency management
- **Docker**: Uses `ministackorg/ministack` for localstack + redis
- **Local dev**: Requires `.env` file with `AWS_REGION`, `DYNAMODB_ENDPOINT`, `S3_BUCKET`, etc.

## Architecture

- **cmd/web**: Go HTTP server using chi router, serves HTML templates from `ui/html/`, reads from DynamoDB
- **cmd/scraper**: AWS Lambda function (compiled with `CGO_ENABLED=0` for linux), triggered by scheduler
- **internal/scraper**: Scraper implementations (Britanico, BNP, LUM)
- **scripts/create_db.py**: Python script to initialize DynamoDB tables

## Key Files

- `justfile` - All dev commands defined here
- `docker-compose.yml` - Localstack + Redis services
- `internal/models/models.go` - Shared data structures
- `.env` - Local environment variables (not committed)

## Notes

- Go templates use `prettier-plugin-go-template` for formatting
- Lambda function requires `bootstrap` binary + `function.zip` in `cmd/scraper/`
- DynamoDB tables: Movies, Schedules, SchedulerGroups (see `data/dynamodb-tables.json`)