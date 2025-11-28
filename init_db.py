import asyncio
from agenda_cultural.backend.app_initializer import initialize_app
# from agenda_cultural.backend.models import Movies

async def main():
    print("--- Iniciando proceso manual de carga ---")
    await initialize_app()
    print("--- Proceso finalizado ---")

if __name__ == "__main__":
    asyncio.run(main())
