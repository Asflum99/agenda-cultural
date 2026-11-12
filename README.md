# Agenda Cultural

Cartelera de cine cultural en Lima. Centraliza la programación de los principales centros culturales de la ciudad en un solo lugar.

## ¿Qué es?

Agenda Cultural recopila automáticamente la programación gratuita de cine de diversos centros culturales de Lima. Toda la información en un solo lugar, actualizada diariamente.

## Características

- **Actualización diaria** — Los datos se refrescan automáticamente cada mañana
- **Multi-centro** — Cartelera de varios centros culturales en un solo lugar
- **Pósters de TMDB** — Imágenes obtenidas automáticamente de The Movie Database
- **Open Source** — Código abierto bajo licencia MIT

## Desarrollo Local

### Requisitos

- Go 1.25+
- Docker
- Python 3.13+ con `uv`
- [mise](https://mise.jdx.dev) (task runner y toolchain)

### Configuración

```bash
# 1. Clonar el repositorio
git clone https://github.com/asflum99/agenda-cultural.git
cd agenda-cultural

# 2. Crear mise.local.toml con tus credenciales
cat > mise.local.toml << EOF
[env]
TMDB_API_KEY = "tu_api_key_aqui"
DYNAMODB_ENDPOINT = "http://localhost:4566"
AWS_REGION = "us-east-1"
EOF

# 3. Iniciar localstack y crear tablas de DynamoDB
mise run create_db

# 4. Ejecutar el servidor web
mise run run-web
```

El servidor estará disponible en `http://localhost:8080`.

`mise.local.toml` está en `.gitignore` y mise lo carga automáticamente junto a
`mise.toml`: no hay que declararlo ni exportar variables a mano.

### Ejecutar el Scraper Localmente

```bash
# 1. Construir y desplegar el Lambda en localstack
mise run create-function

# 2. Ejecutar el scraper
mise run invoke-lambda

# 3. Ver las películas guardadas
awslocal dynamodb scan --table-name Movies --output table
```

## Arquitectura

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────┐
│   EventBridge   │────▶│  Lambda Scraper  │────▶│  DynamoDB    │
│  (cron diario)  │     │  (Go + Colly)    │     │  (Movies)    │
└─────────────────┘     └──────────────────┘     └──────┬───────┘
                                                        │
┌─────────────────┐     ┌──────────────────┐     ┌──────▼───────┐
│   CloudFront    │────▶│  Lambda Web      │◀────│  DynamoDB    │
│  (CDN + Cache)  │     │  (Go + chi)      │     │  (Movies)    │
└────────┬────────┘     └──────────────────┘     └──────────────┘
         │
         ▼
┌─────────────────┐
│  S3 (Estáticos) │
│  CSS / JS       │
└─────────────────┘
```

### Estructura del Proyecto

```
cmd/
├── web/              # Servidor HTTP (Go + chi)
└── scraper/          # Lambda de scraping (Go + Colly)
internal/
├── models/           # Estructuras de datos
├── scraper/          # Implementaciones de scrapers
└── webapp/           # Lógica web (rutas, handlers)
ui/
├── html/             # Plantillas Go
└── static/           # CSS y JS
infra/                # Infraestructura en OpenTofu
mise-tasks/
├── create_db.py         # Crea las tablas de DynamoDB en localstack
└── create-function.sh   # Compila y despliega el Lambda en localstack
```

## Despliegue

### Infraestructura (OpenTofu)

La infraestructura se define con OpenTofu en `infra/`, y todo pasa por tareas
de mise:

```bash
# 1. (una vez) el bucket de state `agenda-cultural-tfstate` debe existir en S3
cd infra && tofu init

# 2. Compilar Lambdas y desplegar
mise run tf-plan   # review del plan
mise run deploy    # corre build-lambdas y `tofu apply` en infra/
```

Los valores por cuenta van en `mise.local.toml` (no commiteado):

```toml
[env]
TF_VAR_certificate_arn = "arn:aws:acm:us-east-1:...:certificate/..."
CLOUDFLARE_API_TOKEN = "<token con Zone:Read + DNS:Edit>"
```

Esto crea:
- Tabla DynamoDB `Movies` con TTL automático
- Lambda Scraper (triggered por EventBridge cron)
- Lambda Web (API Gateway + CloudFront)
- Bucket S3 para archivos estáticos
- Distribución CloudFront con cache behaviors
- CNAME de Cloudflare apuntando a la distribución

### Archivos Estáticos

```bash
# Subir CSS y JS a S3
mise run deploy-static
```

## Tecnologías

- **Backend**: Go 1.25, chi router, aws-lambda-go
- **Scraper**: Colly (web scraping), goquery
- **Base de datos**: DynamoDB (TTL automático)
- **Infraestructura**: OpenTofu, CloudFront, S3, EventBridge, API Gateway, Cloudflare DNS
- **Frontend**: Go templates, CSS custom properties, htmx, vanilla JS
- **Tipografía**: DM Serif Display, Source Sans 3 (Google Fonts)

## Licencia

MIT
