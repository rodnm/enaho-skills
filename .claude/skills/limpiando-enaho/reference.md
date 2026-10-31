# Referencia de la ENAHO 2024

Nombres, etiquetas y códigos leídos de los `.dta` del INEI (código de encuesta `966`). Cada zip trae además `Diccionario2024.pdf` y `FichaTecnica.pdf`, con todas las variables.

## Módulo 34, `sumaria-2024.dta`: una fila por hogar

| Variable | Etiqueta | Códigos o uso |
|---|---|---|
| `conglome`, `vivienda`, `hogar` | Llaves del hogar | Texto de 6, 3 y 2 caracteres |
| `ubigeo` | Ubicación geográfica | Texto de 6 caracteres; `ubigeo[:2]` es el departamento |
| `dominio` | Dominio geográfico | 1 costa norte, 2 costa centro, 3 costa sur, 4 sierra norte, 5 sierra centro, 6 sierra sur, 7 selva, 8 Lima Metropolitana |
| `estrato` | Estrato geográfico | 1 a 5: 2 000 habitantes o más (urbano). 6: 500 a 1 999 habitantes. 7 y 8: áreas de empadronamiento rural (rural) |
| `pobreza` | Pobreza | 1 pobre extremo, 2 pobre no extremo, 3 no pobre |
| `mieperho` | Total de miembros del hogar | Conteo de `p204 == 1`, incluye a los miembros ausentes |
| `factor07` | Factor de expansión anual | Por hogar; `factor07 × mieperho` expande a personas |

## Módulo 02, `enaho01-2024-200.dta`: una fila por persona

| Variable | Etiqueta | Códigos o uso |
|---|---|---|
| `codperso` | Número de orden de la persona | Texto de 2 caracteres; completa la llave de persona |
| `p203` | Parentesco con el jefe(a) del hogar | 0 panel, 1 jefe(a), 2 esposo(a), 3 hijo(a), 4 yerno/nuera, 5 nieto(a), 6 padres/suegros, 7 otros parientes, 8 trabajador del hogar, 9 pensionista, 10 otros no parientes, 11 hermano(a) |
| `p204` | ¿Es miembro del hogar? | 1 sí, 2 no |
| `p205` | ¿Ausente del hogar 30 días o más? | 1 sí, 2 no. Solo si `p204 == 1` |
| `p206` | ¿Presente en el hogar 30 días o más? | 1 sí, 2 no. Solo si `p204 == 2` |
| `p207` | Sexo | 1 hombre, 2 mujer |
| `p208a` | Edad en años cumplidos | 0 a 98 |
| `facpob07` | Factor de expansión anual de población | Por persona |

## Variables que construye `limpiar.py`

| Variable | Definición |
|---|---|
| `anio` | La columna del año, renombrada |
| `departamento` | `ubigeo[:2]` |
| `urbano` | `estrato <= 5` |
| `pobre` | `pobreza <= 2` |
| `peso_hogar` | `factor07 × mieperho` |

## Qué peso usar

| Cifra | Peso | Filas |
|---|---|---|
| Pobreza nacional, por área, dominio o departamento | `peso_hogar` | Una por hogar |
| Pobreza por sexo o edad | `facpob07` | Todas |

Usar `peso_hogar` sin quitar duplicados cuenta cada hogar tantas veces como residentes tenga. Con `facpob07` la cifra nacional da 27.53 % en vez de 27.58 %, pero 14 departamentos se alejan más de 0.1 puntos de la referencia (Puno 40.42 % frente a 39.9 %).

## Seis trampas

1. **Ceros a la izquierda.** `conglome` «015009» y `ubigeo` «010101» son texto. Como número pierden el cero y la unión falla.
2. **Nombres rotos.** La columna del año llega como `aÑo` con el byte dañado. Hay que normalizar antes de usarla.
3. **No todos son residentes.** El módulo 02 tiene 117,721 filas y 108,664 residentes habituales: `(p204 == 1 & p205 == 2) | (p204 == 2 & p206 == 1)`.
4. **Uniones que duplican.** Sin `validate="m:1"`, un hogar repetido multiplica personas sin avisar.
5. **Encuestas no son personas.** Los 33,691 hogares representan 34.5 millones de personas con su factor.
6. **Códigos, no números.** `pobreza` 1, 2 y 3 son categorías: pobre es `pobreza <= 2`, nunca un promedio.
