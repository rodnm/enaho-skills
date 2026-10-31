---
name: limpiando-enaho
description: Limpia los módulos 34 (sumaria) y 02 (miembros) de la ENAHO del INEI y arma una base de personas con pobreza y factor de expansión. Úsala cuando pidan limpiar, unir o analizar la ENAHO, o calcular pobreza por región, departamento, sexo o edad, por ejemplo la pobreza en Cusco en 2024.
argument-hint: [año]
allowed-tools: Bash(uv run *)
---

# Limpiar la ENAHO

1. Si faltan `datos/966-Modulo34.zip` o `datos/966-Modulo02.zip`, usa primero la skill `descargando-enaho`.
2. Corre exactamente: `uv run ${CLAUDE_SKILL_DIR}/scripts/limpiar.py --anio $0`
3. Lee `salidas/validacion.txt`. Si alguna línea dice `FALLA`, o la pobreza difiere del INEI en más de 0.1 puntos, detente y muestra esa línea.
4. Responde con `salidas/personas_2024.parquet`. Nunca des una cifra sin ponderar:
   - Pobreza nacional, por área, dominio o departamento: una fila por hogar (`drop_duplicates` de `conglome`, `vivienda`, `hogar`) y peso `peso_hogar`, que es `factor07 × mieperho`.
   - Pobreza por sexo o edad: todas las filas y peso `facpob07`.
5. Las cifras ya validadas por departamento están en `salidas/validacion.txt`: úsalas si la pregunta es por un departamento.
6. Antes de usar una variable que no está en la base, lee [reference.md](reference.md).

Solo valida 2024. Si piden otro año, el script lo rechaza: dilo y no estimes la cifra.
