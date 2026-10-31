# Evaluación: tres pedidos con y sin skills

**Resultado:** con skills, los tres pedidos dieron la cifra esperada, y dos de ellos activaron dos skills seguidas. Sin skills, Claude también acertó las cifras cuando pudo llegar a los datos, pero no respetó las reglas de formato ni validó contra el INEI.

## Resultados

| Pedido | Variante | Skills activadas | Cifra | ¿Ponderó? | Figura |
|---|---|---|---|---|---|
| ¿Cuál fue la pobreza en Cusco en 2024? | Con skills | `limpiando-enaho` | **18.5 %** | Sí, `factor07 × mieperho` | No aplica |
| | Control | Ninguna | No respondió | No | No aplica |
| Grafica la pobreza urbana y rural con la ENAHO 2024 | Con skills | `graficando-enaho`, `limpiando-enaho` | **24.8 % y 39.3 %** | Sí, `factor07 × mieperho` | Cumple las reglas |
| | Control | Ninguna | 24.8 % y 39.3 % | Sí, `factor07 × mieperho` | Barras apiladas de dos colores, a 150 dpi |
| Haz un mapa de la pobreza por departamento con la ENAHO 2024 | Con skills | `mapeando-enaho`, `limpiando-enaho` | **Cajamarca 45.0 %, Ica 6.0 %** | Sí, `factor07 × mieperho` | Cumple las reglas |
| | Control | Ninguna | Cajamarca 45.0 %, Ica 6.0 % | Sí, `factor07 × mieperho` | Escala de varios colores que empieza en 6, no en 0 |

En el control del Cusco, Claude intentó buscar en internet, no tenía permiso y no miró los datos de la carpeta.

## Qué aportan las skills

Las cifras no son la diferencia principal: con los datos a la vista, el control dedujo el peso correcto por su cuenta. Las skills aportan esto:

| | Con skills | Control |
|---|---|---|
| **Reproducibilidad** | Mapa, gráfico y `validacion.txt` idénticos byte a byte en todas las corridas | Cada corrida escribe su propio script, con otros nombres y otras carpetas |
| **Validación** | 44 comprobaciones de llaves, filas y cifras oficiales; se detiene si una falla | La cifra del INEI «recordada», sin contrastarla |
| **Reglas de formato** | Fijas en el script | Las que elija el modelo |
| **Respuesta a una pregunta directa** | Usa los datos | No los buscó en el pedido del Cusco |

## Por qué hay un control aparte

El comando de la sesión, `claude -p --disallowedTools Skill`, no sirvió como comparación. Sin la herramienta `Skill`, Claude encontró los scripts en `.claude/skills/` y los corrió igual:

| Pedido con `--disallowedTools Skill` | Qué pasó |
|---|---|
| Cusco | No respondió: intentó buscar en internet y no tenía permiso |
| Urbano y rural | Corrió `limpiar.py` y `graficar.py`: 24.8 % y 39.3 % |
| Mapa | Corrió `limpiar.py` y `mapear.py`: Cajamarca 45.0 %, Ica 6.0 % |

Por eso el **control** repite los pedidos en una carpeta sin `.claude/` ni `referencias/`, solo con `datos/`.

## Cómo se corrió

Cada corrida usó una copia limpia, con `datos/` y sin `salidas/`, `figuras/` ni `mapas/`:

```bash
claude -p "<pedido>" --model sonnet --setting-sources project --strict-mcp-config \
  --no-session-persistence --output-format stream-json --verbose \
  --permission-mode acceptEdits \
  --allowedTools Skill Read Write Edit Glob Grep "Bash(uv *)" "Bash(python *)" "Bash(ls *)" "Bash(mkdir *)"
```

- Las skills activadas se leyeron de los eventos `stream-json`.
- Las variantes sin skills agregan `--disallowedTools Skill`.
- `--setting-sources project` y `--strict-mcp-config` dejan fuera la configuración personal y los servidores MCP.

## Límites

- Es una corrida por variante: muestra lo que pasó, no una tasa de acierto.
- Se usó Sonnet. Otro modelo puede activar las skills de otra forma.
- Los pedidos de gráfico y mapa nombran la ENAHO, como el comando de la sesión.
- Sin `WebSearch` en la lista de permisos, el pedido del Cusco no pudo ir a internet. Con ese permiso, el resultado del control podría ser otro.
- Las cifras de referencia son las de la sesión; no se contrastaron con los informes publicados por el INEI.
