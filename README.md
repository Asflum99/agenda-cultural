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
- [Just](https://github.com/casey/just) (task runner)

### Configuración

```bash
# 1. Clonar el repositorio
git clone https://github.com/asflum99/agenda-cultural.git
cd agenda-cultural

# 2. Crear archivo .env con tus credenciales
cat > .env << EOF
TMDB_API_KEY=tu_api_key_aqui
DYNAMODB_ENDPOINT=http://localhost:4566
AWS_REGION=us-east-1
EOF

# 3. Iniciar localstack y crear tablas de DynamoDB
just setup-db

# 4. Ejecutar el servidor web
just run-web
```

El servidor estará disponible en `http://localhost:8080`.

### Ejecutar el Scraper Localmente

```bash
# 1. Crear environment.json para el Lambda
cat > environment.json << EOF
{
  "Variables": {
    "DYNAMODB_ENDPOINT": "http://ministack:4566",
    "AWS_REGION": "us-east-1",
    "MOVIES_TABLE_NAME": "Movies",
    "CLOUDFRONT_DISTRIBUTION_ID": "",
    "TMDB_API_KEY": "tu_api_key_aqui"
  }
}
EOF

# 2. Construir y desplegar el Lambda en localstack
just create-function

# 3. Ejecutar el scraper
just invoke-lambda

# 4. Ver las películas guardadas
just list-movies
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
├── storage/          # Repositorio S3
└── webapp/           # Lógica web (rutas, handlers)
ui/
├── html/             # Plantillas Go
└── static/           # CSS y JS
scripts/
└── create_db.py      # Script para crear tablas DynamoDB
```

## Despliegue

### Infraestructura (SAM)

```bash
sam build
sam deploy --guided
```

Esto crea:
- Tabla DynamoDB `Movies` con TTL automático
- Lambda Scraper (triggered por EventBridge cron)
- Lambda Web (API Gateway + CloudFront)
- Bucket S3 para archivos estáticos
- Distribución CloudFront con cache behaviors

### Archivos Estáticos

```bash
# Subir CSS y JS a S3
just deploy-static

# Invalidar cache de CloudFront
just invalidate-cache
```

## Tecnologías

- **Backend**: Go 1.25, chi router, aws-lambda-go
- **Scraper**: Colly (web scraping), goquery
- **Base de datos**: DynamoDB (TTL automático)
- **Infraestructura**: AWS SAM, CloudFront, S3, EventBridge
- **Frontend**: Go templates, CSS custom properties, htmx, vanilla JS
- **Tipografía**: DM Serif Display, Source Sans 3 (Google Fonts)

## Licencia

MIT
