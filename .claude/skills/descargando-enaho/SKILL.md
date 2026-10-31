---
name: descargando-enaho
description: Descarga del INEI los módulos 34 (sumaria) y 02 (miembros) de la ENAHO 2024 y los límites departamentales a datos/. Úsala cuando pidan bajar o descargar la ENAHO o los microdatos del INEI, o cuando falten los zip en datos/.
argument-hint: [año]
allowed-tools: Bash(uv run *)
---

# Descargar la ENAHO

1. Corre exactamente: `uv run ${CLAUDE_SKILL_DIR}/scripts/descargar.py --anio $0`
2. Si termina con error, muéstralo tal cual y detente. No busques los datos en otra fuente.
3. Responde con lo que quedó en `datos/`: `966-Modulo34.zip`, `966-Modulo02.zip` y `peru_departamental_simple.geojson`.

Solo trabaja con 2024 (`966` es su código en el portal del INEI). Si piden otro año, el script lo rechaza: dilo y no inventes otra URL. Un zip ya válido no se vuelve a bajar. La carpeta `datos/` no se sube a git.
