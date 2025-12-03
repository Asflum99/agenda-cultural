# 1. Base: Actualizar repositorio y librerías
update:
	@echo "--- ⬇️ Bajando cambios de GitHub ---"
	git pull origin main
	@echo "--- 📦 Sincronizando entorno virtual ---"
	uv sync

# 2. Tarea Interna: Reiniciar el cerebro (Backend)
_restart_backend:
	@echo "--- 🐍 Reiniciando Servicio Backend ---"
	sudo systemctl restart agendacultural
	sudo systemctl status agendacultural --no-pager

# =================================================================
# COMANDOS PÚBLICOS
# =================================================================

# OPCIÓN A: Solo lógica interna
deploy-back: update _restart_backend
	@echo "--- ✅ Mantenimiento de Backend completado ---"

# OPCIÓN B: La opción segura para la Web (Frontend + Backend)
deploy-full: update
	@echo "--- 🏗️ Construyendo Frontend (Reflex Export) ---"
	rm -rf frontend.zip .web
	uv run reflex export --frontend-only
	@echo "--- 🌐 Actualizando Nginx ---"
	rm -rf public_web/*
	unzip -q frontend.zip -d public_web
	sudo systemctl restart nginx
	# Es vital reiniciar el backend también para que coincida con el frontend nuevo
	@make _restart_backend
	@echo "--- 🎉 Despliegue COMPLETO finalizado ---"
