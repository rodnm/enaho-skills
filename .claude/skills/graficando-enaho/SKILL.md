---
name: graficando-enaho
description: Grafica en barras la pobreza de la ENAHO 2024 del INEI por área urbana y rural, sexo o edad, con ponderación y formato fijos. Úsala cuando pidan un gráfico o una figura de la pobreza en Perú, por ejemplo graficar la pobreza urbana y rural.
argument-hint: [area|sexo|edad]
allowed-tools: Bash(uv run *)
---

# Graficar la pobreza de la ENAHO

1. Si no existe `salidas/personas_2024.parquet`, usa primero la skill `limpiando-enaho`.
2. Elige el corte de la pregunta y corre exactamente: `uv run ${CLAUDE_SKILL_DIR}/scripts/graficar.py --por area` (o `sexo`, o `edad`).
3. Responde con la ruta de `figuras/pobreza_por_<corte>.png` y las cifras que imprime el script. No las recalcules.

## Reglas que fija el script

- Barras que empiezan en cero, ordenadas de mayor a menor; las edades van en su orden natural.
- Un solo color y el valor escrito en cada barra.
- El título dice qué y cuándo.
- Nota al pie: «Fuente: INEI, ENAHO 2024», más el peso usado.
- PNG a 200 dpi en `figuras/`.

## Pesos

- **Área:** por hogar con `factor07 × mieperho`, porque así salen las cifras oficiales de 24.8 % y 39.3 %. Con `facpob07` darían 24.7 % y 39.4 %.
- **Sexo y edad:** por persona con `facpob07`, porque son atributos de cada persona.

Si piden un corte que no está en el script, dilo antes de improvisar otro gráfico.
