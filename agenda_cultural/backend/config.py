import os
from dotenv import load_dotenv

load_dotenv()

# Configuración TMDB
TMDB_TOKEN = os.getenv("TMDB_TOKEN")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w342"

if not TMDB_TOKEN:
    print("⚠️ ADVERTENCIA: TMDB_TOKEN no está configurado.")
