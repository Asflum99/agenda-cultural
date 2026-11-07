# Agenda Cultural - Developer Notes

## Commands

```bash
mise run run-web          # Run Go web server on :8080
mise run create_db        # Start Docker Compose + create DynamoDB tables
mise run create-function  # Build Lambda binary and deploy to localstack
mise run invoke-lambda    # Test Lambda function (output in out.json)
mise run deploy-static    # Sync CSS/JS to S3 bucket
mise run build-lambdas    # Build Go Lambda binaries (infra/build/)
mise run tf-plan          # Ver el plan de infraestructura
mise run deploy           # Build Lambdas y aplicar la infraestructura con OpenTofu
```

## Environment

- **Go**: 1.25, modules
- **Python**: 3.13, uv for dependency management
- **Docker**: Uses `ministackorg/ministack` for localstack + redis
- **Local dev**: Uses `mise.local.toml` for env vars (`TMDB_API_KEY`, `AWS_REGION`, `DYNAMODB_ENDPOINT`)

## Architecture

- **cmd/web**: Go HTTP server using chi router, serves Go templates from `ui/html/`, reads from DynamoDB
- **cmd/scraper**: AWS Lambda function (compiled with `CGO_ENABLED=0` for linux), triggered by EventBridge scheduler
- **internal/scraper**: Scraper implementations (BNP, Britanico, LUM) using colly
- **internal/webapp**: Web application logic (routes, handlers, template rendering)
- **internal/models**: Shared data structures (Movie)
- **ui/html/**: Go templates with `components/` (navbar, footer, movie_card, cinema_row) and `pages/` (home, about)
- **ui/static/**: CSS (`css/style.css`), JS (`js/htmx.min.js`, `js/carousel.js`)

## Key Files

- `mise.toml` - Task runner config (dev + deploy commands)
- `mise.local.toml` - Local environment variables (not committed)
- `mise-tasks/` - Task scripts (create_db.py, create-function.sh)
- `docker-compose.yml` - Localstack + Redis services
- `infra/` - infraestructura en OpenTofu (DynamoDB, Lambdas, API Gateway, CloudFront, S3, CNAME de Cloudflare)

## Frontend

- **Theme**: Dark mode only (warm brown cinema aesthetic)
- **Fonts**: DM Serif Display (headings), Source Sans 3 (body) — loaded from Google Fonts
- **CSS**: `ui/static/css/style.css` — arthouse/cinema theme with CSS custom properties
- **JS**: htmx (loaded but not actively used), carousel.js (horizontal scroll navigation)
- **Static serving**: Local dev serves `/css/*` and `/js/*` from `ui/static/css` and `ui/static/js`
- **Production**: Static files synced to S3, served via CloudFront with cache behaviors for `/css/*` and `/js/*`

## Deployment

```bash
# (una vez) el bucket de state `agenda-cultural-tfstate` debe existir en S3
cd infra && tofu init

# Build Lambdas + plan/apply de infraestructura (recursos en infra/*.tf)
mise run tf-plan
mise run deploy

# Deploy static assets to S3
mise run deploy-static
```

Valores sensibles en `mise.local.toml` (`[env]`): `TF_VAR_certificate_arn`,
`TF_VAR_origin_verify_secret`, `CLOUDFLARE_API_TOKEN`.

## Notes

- Go templates use `prettier-plugin-go-template` for formatting
- Lambda functions use `provided.al2023` runtime (custom Go binary)
- DynamoDB table `Movies` uses TTL on `ExpiresAt` for automatic cleanup
- TMDB API key stored in SSM Parameter Store for production, `mise.local.toml` for local
- CloudFront caches HTML for 24h; static assets use AWS managed cache policy
