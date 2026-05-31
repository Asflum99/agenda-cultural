# Agenda Cultural - Developer Notes

## Commands

```bash
just run-web          # Run Go web server on :8080
just setup-db         # Start Docker Compose + create DynamoDB tables
just create-function  # Build Lambda binary and deploy to localstack
just delete-function  # Remove Lambda from localstack
just invoke-lambda    # Test Lambda function (output in out.json)
just list-movies      # Query Movies table from DynamoDB
just setup-ui         # Download htmx.min.js
just deploy-static    # Sync CSS/JS to S3 bucket
just invalidate-cache # Invalidate CloudFront cache
```

## Environment

- **Go**: 1.25, modules
- **Python**: 3.13, uv for dependency management
- **Docker**: Uses `ministackorg/ministack` for localstack + redis
- **Local dev**: Requires `.env` file with `TMDB_API_KEY`, `AWS_REGION`, `DYNAMODB_ENDPOINT`
- **Local Lambda**: Requires `environment.json` with `DYNAMODB_ENDPOINT: "http://ministack:4566"` and `TMDB_API_KEY`

## Architecture

- **cmd/web**: Go HTTP server using chi router, serves Go templates from `ui/html/`, reads from DynamoDB
- **cmd/scraper**: AWS Lambda function (compiled with `CGO_ENABLED=0` for linux), triggered by EventBridge scheduler
- **internal/scraper**: Scraper implementations (BNP, Britanico, LUM) using colly
- **internal/webapp**: Web application logic (routes, handlers, template rendering)
- **internal/models**: Shared data structures (Movie)
- **internal/storage**: S3 repository for JSON storage
- **ui/html/**: Go templates (base, navbar, footer, movie_card, cinema_row, pages)
- **ui/static/**: CSS (style.css), JS (htmx.min.js, carousel.js)

## Key Files

- `justfile` - All dev commands
- `docker-compose.yml` - Localstack + Redis services
- `template.yaml` - SAM/CloudFormation infrastructure (DynamoDB, Lambdas, CloudFront, S3)
- `environment.json` - Local Lambda environment variables (not committed)
- `.env` - Local environment variables (not committed)

## Frontend

- **Theme**: Dark mode only (warm brown cinema aesthetic)
- **Fonts**: DM Serif Display (headings), Source Sans 3 (body) — loaded from Google Fonts
- **CSS**: `ui/static/css/style.css` — arthouse/cinema theme with CSS custom properties
- **JS**: htmx (loaded but not actively used), carousel.js (horizontal scroll navigation)
- **Static serving**: Local dev serves `/css/*` and `/js/*` from `ui/static/css` and `ui/static/js`
- **Production**: Static files synced to S3, served via CloudFront with cache behaviors for `/css/*` and `/js/*`

## Deployment

```bash
# Build and deploy all infrastructure
sam build --clean
sam deploy --guided

# Deploy static assets to S3
just deploy-static

# Invalidate CloudFront cache
just invalidate-cache
```

## Notes

- Go templates use `prettier-plugin-go-template` for formatting
- Lambda functions use `provided.al2023` runtime (custom Go binary)
- DynamoDB table `Movies` uses TTL on `ExpiresAt` for automatic cleanup
- TMDB API key stored in SSM Parameter Store for production, `.env` for local
- CloudFront caches HTML for 24h; static assets use AWS managed cache policy
