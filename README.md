# Agenda Cultural

Aplicación web que recopila y presenta la cartelera de películas en centros culturales de Lima, Perú.

## Características

- **Scraping automático**: Recolecta información de películas desde LUM, BNP, CCPUCP y Alianza Francesa
- **Actualización diaria**: Ejecución programada cada medianoche usando APScheduler
- **Interfaz web**: Aplicación construida con Reflex (framework Python full-stack)
- **Base de datos**: PostgreSQL para almacenamiento persistente
- **Despliegue fácil**: Configuración Docker para desarrollo y producción

## Tecnologías

- **Backend**: Python 3.13+, SQLAlchemy, SQLModel
- **Frontend**: Reflex (Pynecone)
- **Scraping**: Playwright, httpx
- **Base de datos**: PostgreSQL 15
- **Scheduler**: APScheduler
- **Despliegue**: Docker Compose, Systemd

## Estructura del proyecto

```
agenda_cultural/
├── agenda_cultural/          # Aplicación principal
│   ├── backend/              # Scraping y lógica de negocio
│   │   ├── scrapers/         # Extractores por centro cultural
│   │   ├── models.py         # Modelos de base de datos
│   │   └── services/         # Servicios de aplicación
│   └── frontend/             # Páginas y componentes UI
│       ├── pages/            # Páginas de la aplicación
│       └── components/       # Componentes reutilizables
├── tests/                    # Tests unitarios y de integración
├── alembic/                  # Migraciones de base de datos
└── docker-compose.yml        # Configuración Docker
```

## 💻 Configuración y Ejecución Local

Sigue estos pasos para levantar el entorno de desarrollo en tu máquina utilizando **uv** para una gestión de dependencias ultrarrápida.

### Prerrequisitos
Asegúrate de tener instalado:
* [Python 3.10+](https://www.python.org/downloads/)
* [uv](https://github.com/astral-sh/uv) (Gestor de paquetes moderno)
* [Docker](https://docs.docker.com/get-docker/) (Engine y CLI con Docker Compose)
* [Git](https://git-scm.com/)

### 1. Clonar el repositorio
Descarga el código fuente y entra en la carpeta del proyecto:
```bash
git clone [https://github.com/Asflum99/agenda-cultural.git](https://github.com/Asflum99/agenda-cultural.git)
cd agenda-cultural
```

### 2. Configurar variables de entorno
El proyecto necesita ciertas claves para funcionar. Crea un archivo .env en la raíz del proyecto y configura los siguientes valores:
```bash
# Variables para Docker
POSTGRES_USER=my_user
POSTGRES_PASSWORD=my_password

# URL de conexión a la base de datos (usa los valores configurados arriba)
DATABASE_URL="postgresql://my_user:my_password@localhost:5432/movies_db"

# API Keys y Entorno
TMDB_TOKEN="TU_TOKEN"
```

### 4. Iniciar la Base de datos
Uso de Docker para levantar PostgreSQL rápidamente.
```bash
docker compose up -d
```

### 5. Instalación y preparación del entorno
```bash
uv sync
uv run playwright install
```

### 6. Configurar la Base de Datos
Usamos uv para sincronizar el entorno virtual y las dependencias.
```bash
uv run reflex db migrate
```

### 7. Lanzar aplicación
Una vez hecha toda la configuración previa, ya se puede ejecutar la página web con el siguiente comando:
```bash
# Obtener cartelera actual
uv run run_scraper.py

# Iniciar servidor de desarrollo
uv run reflex run
```

## Despliegue

La aplicación está configurada para despliegue en producción con:
- Variables de entorno para entorno de producción
- Servicio Systemd para el scheduler
- Análisis de tráfico con Umami (solo en producción)

## Centros culturales

- **LUM**: Lugar de la Memoria
- **BNP**: Biblioteca Nacional del Perú
- **CCPUCP**: Centro Cultural de la Pontificia Universidad Católica del Perú
- **Alianza Francesa**: Alianza Francesa de Lima
