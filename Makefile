# =================================================================
# 1. TAREAS BASE (Sistema y Dependencias)
# =================================================================

# Descargar código y sincronizar librerías
update:
	@echo "--- ⬇️ Bajando cambios de GitHub ---"
	git pull origin main
	@echo "--- 📦 Sincronizando entorno virtual ---"
	uv sync

# Aplicar cambios en la estructura de la Base de Datos
migrate:
	@echo "--- 🗄️ Aplicando migraciones pendientes ---"
	uv run reflex db migrate

# Reiniciar el servicio de Python (Backend)
_restart_backend:
	@echo "--- 🐍 Reiniciando Servicio Backend ---"
	sudo systemctl restart agendacultural
	sudo systemctl status agendacultural --no-pager

# Construir y mover los archivos estáticos (Frontend)
_build_frontend:
	@echo "--- 🏗️ Construyendo Frontend (Reflex Export) ---"
	# 1. Limpieza previa
	rm -rf frontend.zip .web
	
	# 2. Generación
	uv run reflex export --frontend-only --env prod
	
	@echo "--- 🌐 Actualizando Nginx ---"
	# 3. Limpieza del directorio público
	rm -rf public_web/*
	
	# 4. Descomprimir
	unzip -q frontend.zip -d public_web
	
	# 5. Borramos el zip y también la carpeta .web que genera Reflex al compilar
	rm -f frontend.zip
	rm -rf .web
	
	# 6. Reiniciar servidor web
	sudo systemctl restart nginx

# =================================================================
# 2. COMANDOS DE DESPLIEGUE (Los que tú ejecutas)
# =================================================================

# OPCIÓN A: Solo Backend (Código Python + Base de Datos)
# Útil si solo cambiaste scrapers, modelos o lógica interna.
deploy-back: update migrate _restart_backend
	@echo "--- ✅ Despliegue de Backend completado ---"

# OPCIÓN B: Despliegue Completo (Frontend + Backend + DB)
# Útil cuando cambiaste UI (home.py, etc) o todo a la vez.
deploy-full: update migrate _build_frontend _restart_backend
	@echo "--- 🎉 Despliegue FULL finalizado ---"
