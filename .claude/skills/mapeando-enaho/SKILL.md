---
name: mapeando-enaho
description: Hace el mapa de la pobreza por departamento del Perú con la ENAHO 2024 del INEI y los límites departamentales, uniendo por código. Úsala cuando pidan un mapa de la pobreza, un mapa por departamento o por región del Perú.
allowed-tools: Bash(uv run *)
---

# Mapear la pobreza de la ENAHO

1. Si no existe `salidas/personas_2024.parquet`, usa primero la skill `limpiando-enaho`.
2. Si falta `datos/peru_departamental_simple.geojson`, usa primero la skill `descargando-enaho`.
3. Corre exactamente: `uv run ${CLAUDE_SKILL_DIR}/scripts/mapear.py`
4. Si el script se detiene, muestra su mensaje y detente: la cifra o la unión están mal.
5. Responde con `mapas/pobreza_departamento.png` y los departamentos de mayor y menor pobreza que imprime el script.

## Reglas que fija el script

- Une por código: `ubigeo[:2]` con `FIRST_IDDP`, como texto. Nunca por nombre: «APURIMAC» no es «Apurímac».
- Exige 25 departamentos y ninguno sin dato. Se detiene si alguno difiere más de 0.1 puntos de `referencias/pobreza_departamento_2024.csv`.
- Un color de claro a oscuro, desde 0; nunca arcoíris.
- Leyenda con la unidad: % de personas.
- Lima (15) y Callao (07) van separados.
- Pondera por hogar con `factor07 × mieperho`, como la referencia de la sesión.
