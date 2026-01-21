# 🐍 Debugging de Scrapers con nvim-dap

Esta guía explica cómo usar el script de debugging para debuggear los scrapers de centros culturales usando nvim-dap.

## 📋 Script Disponible

**`scripts/debug_runner.py`** - Script de debugging inteligente que:
- Detecta automáticamente el scraper donde estás ubicado y lo ejecuta.
- Fuerza el modo **visible** (no-headless) del navegador para inspección visual.
- Si no detecta un scraper, muestra un menú interactivo para seleccionar uno.

## 🚀 Configuración (.vscode/launch.json)

Asegúrate de tener esta configuración en tu archivo `.vscode/launch.json`. La variable `NVIM_CURRENT_FILE` es crítica para la auto-detección.

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "🐍 Debug: Scraper (Smart)",
      "type": "debugpy",
      "request": "launch",
      "module": "scripts.debug_runner",
      "env": {
        "NVIM_CURRENT_FILE": "${file}"
      },
      "console": "integratedTerminal",
      "justMyCode": true
    }
  ]
}
```

## 📖 Uso con nvim-dap

1. Abre cualquier archivo del scraper que quieres debuggear
2. Coloca breakpoints en el código
3. Presiona `F5` (o tu keybinding para iniciar una sesión de debugging con nvim-dap)
4. Selecciona: `🐍 Debug: Scraper (Smart)`

El script se comportará de dos formas:

- **Si estás en un archivo de scraper**: Detectará automáticamente el scraper y lo ejecutará, mostrando `✨ Auto-detección: [Nombre del scraper]`
- **Si no estás en un scraper**: Mostrará un menú interactivo:

```
🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯
              DEBUGGER DE SCRAPERS              
🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯

  [1] LUM - Lugar de la Memoria
  [2] BNP - Biblioteca Nacional del Perú
  [3] CCPUCP - Centro Cultural PUCP
  [4] Alianza Francesa

  [q] Salir
```

4. Selecciona el número del scraper que quieres debuggear

## 🛠️ Uso desde terminal

```bash
# Ejecutar script (mostrará menú si no detecta scraper)
.venv/bin/python scripts/debug_runner.py
```

## 🎯 Detalles Técnicos

### Detección Automática

El script detecta el scraper actual basándose en:

1. La variable de entorno `NVIM_CURRENT_FILE` (configurada desde launch.json como `${file}`)
2. Busca la carpeta del scraper en la ruta del archivo actual (`scrapers/[nombre]`)

### Configuración de Scrapers

Los scrapers se configuran centralmente en `agenda_cultural/shared/cultural_centers.py` mediante la constante `CULTURAL_CENTERS`. Esta configuración es importada automáticamente por el script de debugging.

### Variables de Entorno

| Variable | Descripción |
|----------|-------------|
| `NVIM_CURRENT_FILE` | Archivo actual (configurado desde nvim-dap como `${file}`) |
| `SCRAPER_HEADLESS` | Controla visibilidad del navegador. El script lo fuerza a `false` para debugging |

## 📝 Ejemplo de Workflow

1. Abrir `agenda_cultural/backend/scrapers/lum/scraper.py`
2. Colocar breakpoint en línea específica
3. Presionar `F5`
4. Seleccionar `🐍 Debug: Scraper (Smart)`
5. Verás: `✨ Auto-detección: LUM - Lugar de la Memoria`
6. El debugger se detendrá en el breakpoint
7. Inspeccionar variables, step through código, etc.

## 🎨 Personalización

Para personalizar el comportamiento, puedes:

1. Modificar `CULTURAL_CENTERS` en `agenda_cultural/shared/cultural_centers.py` para agregar o modificar scrapers
2. **Convención de nombres (estricta):** Para que la carga dinámica funcione, debes seguir esta regla:
    - **Diccionario:** Clave en snake_case (ej: 'nuevo_cine')
    - **Carpeta:** Debe llamarse igual que la clave ('scrapers/nuevo_cine/')
    - **Clase:** Debe ser PascalCase + "Scraper" ('NuevoCineScraper')
3. Modificar `detect_scraper()` para cambiar la lógica de detección

## 🐛 Troubleshooting

### El script no detecta el scraper actual

- Verifica que el archivo esté en la ruta `agenda_cultural/backend/scrapers/[nombre]/`
- Asegúrate de que el nombre del scraper coincida con las claves en `CULTURAL_CENTERS` (en `agenda_cultural/shared/cultural_centers.py`)
- Verifica que `NVIM_CURRENT_FILE` esté configurado correctamente en `launch.json`
- Revisa que `__init__.py` exista en todas las carpetas intermedias para permitir la importación correcta

### nvim-dap no encuentra las configuraciones

- Verifica que `.vscode/launch.json` esté en el directorio raíz del proyecto
- Reinicia nvim después de agregar nuevas configuraciones

### Errores de dependencias

```bash
# Asegúrate de tener debugpy instalado
.venv/bin/pip install debugpy

# O usa el grupo de dependencias dev
uv sync --group dev
```

### Error de importación de CULTURAL_CENTERS

Si ves el mensaje "🔥 ERROR CRÍTICO DE IMPORTACIÓN":

- Verifica que la ruta `agenda_cultural.shared.cultural_centers` exista
- Asegúrate de que `__init__.py` exista en todas las carpetas: `agenda_cultural/`, `agenda_cultural/shared/`
- Confirma que `CULTURAL_CENTERS` está definido en `agenda_cultural/shared/cultural_centers.py`
