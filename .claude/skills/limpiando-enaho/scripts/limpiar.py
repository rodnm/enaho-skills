"""Une los módulos 34 y 02 de la ENAHO 2024 en una base de personas y la valida."""

import argparse
import io
import re
import sys
import zipfile
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[4]
DATOS = RAIZ / "datos"
SALIDAS = RAIZ / "salidas"
REFERENCIA_DEPARTAMENTOS = RAIZ / "referencias" / "pobreza_departamento_2024.csv"

ANIO = 2024
CODIGO_INEI = 966

LLAVES_HOGAR = ["conglome", "vivienda", "hogar"]
LLAVES_PERSONA = LLAVES_HOGAR + ["codperso"]

COLUMNAS_SUMARIA = LLAVES_HOGAR + [
    "anio", "ubigeo", "dominio", "estrato", "pobreza", "mieperho", "factor07",
]
COLUMNAS_PERSONAS = LLAVES_PERSONA + ["p203", "p204", "p205", "p206", "p207", "p208a", "facpob07"]

# Largo fijo de cada código en la ENAHO 2024. Si es menor, se perdieron ceros a la izquierda.
LARGO_CODIGOS = {"conglome": 6, "vivienda": 3, "hogar": 2, "codperso": 2, "ubigeo": 6}

# Cifras de 2024 publicadas en la sesión; TOLERANCIA está en puntos porcentuales.
HOGARES_ESPERADOS = 33_691
FILAS_MODULO_02 = 117_721
RESIDENTES_ESPERADOS = 108_664
POBREZA_NACIONAL = 27.6
POBREZA_EXTREMA = 5.5
POBREZA_URBANA = 24.8
POBREZA_RURAL = 39.3
POBREZA_LIMA_METROPOLITANA = 28.2
TOLERANCIA = 0.1


def leer_dta(ruta_zip: Path, patron: str) -> pd.DataFrame:
    """Lee el único .dta del zip que coincide con patron, sin convertir códigos en categorías."""
    with zipfile.ZipFile(ruta_zip) as archivo:
        miembros = [n for n in archivo.namelist() if re.search(patron, n, re.IGNORECASE)]
        if len(miembros) != 1:
            sys.exit(f"Se esperaba un archivo {patron} en {ruta_zip.name}; hay {miembros}.")
        contenido = io.BytesIO(archivo.read(miembros[0]))
    return pd.read_stata(contenido, convert_categoricals=False)


def normalizar_columnas(tabla: pd.DataFrame) -> pd.DataFrame:
    """Pasa los nombres a minúscula. El del año llega con el byte de la Ñ roto: se ubica por patrón."""
    tabla = tabla.rename(columns=str.lower)
    return tabla.rename(columns=lambda c: "anio" if re.fullmatch(r"a[^a-z]{1,2}o", c) else c)


def llaves_a_texto(tabla: pd.DataFrame, columnas: list[str]) -> pd.DataFrame:
    return tabla.assign(**{c: tabla[c].astype(str).str.strip() for c in columnas})


def tasa(condicion: pd.Series, peso: pd.Series) -> float:
    return 100 * (condicion * peso).sum() / peso.sum()


class Validacion:
    """Junta las comprobaciones para escribirlas todas antes de decidir si se detiene."""

    def __init__(self) -> None:
        self.lineas: list[str] = []
        self.fallos = 0

    def registrar(self, nombre: str, correcto: bool, detalle: str) -> None:
        self.lineas.append(f"{'OK   ' if correcto else 'FALLA'} {nombre}: {detalle}")
        self.fallos += not correcto

    def igual(self, nombre: str, valor: int, esperado: int) -> None:
        self.registrar(nombre, valor == esperado, f"{valor:,} (esperado {esperado:,})")

    def cifra(self, nombre: str, valor: float, esperado: float) -> None:
        correcto = abs(valor - esperado) <= TOLERANCIA
        self.registrar(nombre, correcto, f"{valor:.2f} % (esperado {esperado} ± {TOLERANCIA})")


def validar(sumaria: pd.DataFrame, modulo02: pd.DataFrame, personas: pd.DataFrame, base: pd.DataFrame) -> Validacion:
    v = Validacion()
    v.igual("Hogares en la sumaria", len(sumaria), HOGARES_ESPERADOS)
    v.igual("Filas del módulo 02", len(modulo02), FILAS_MODULO_02)
    v.igual("Residentes habituales", len(personas), RESIDENTES_ESPERADOS)
    v.igual("Llaves de hogar repetidas", int(sumaria.duplicated(LLAVES_HOGAR).sum()), 0)
    v.igual("Llaves de persona repetidas", int(personas.duplicated(LLAVES_PERSONA).sum()), 0)
    v.igual("Filas de la base tras la unión", len(base), len(personas))
    v.igual("Personas sin hogar en la sumaria", int(base["pobreza"].isna().sum()), 0)
    for columna, largo in LARGO_CODIGOS.items():
        v.igual(f"Códigos {columna} sin {largo} caracteres", int((base[columna].str.len() != largo).sum()), 0)

    # La pobreza oficial se calcula por hogar: factor07 × mieperho expande cada hogar a sus personas.
    hogares = base.drop_duplicates(LLAVES_HOGAR)
    v.igual("Hogares en la base", len(hogares), HOGARES_ESPERADOS)
    peso = hogares["peso_hogar"]
    v.cifra("Pobreza nacional (hogares, factor07 × mieperho)", tasa(hogares["pobre"], peso), POBREZA_NACIONAL)
    v.cifra("Pobreza nacional (personas, facpob07)", tasa(base["pobre"], base["facpob07"]), POBREZA_NACIONAL)
    v.cifra("Pobreza extrema", tasa(hogares["pobreza"] == 1, peso), POBREZA_EXTREMA)
    v.cifra("Pobreza urbana", tasa(hogares["pobre"][hogares["urbano"]], peso[hogares["urbano"]]), POBREZA_URBANA)
    v.cifra("Pobreza rural", tasa(hogares["pobre"][~hogares["urbano"]], peso[~hogares["urbano"]]), POBREZA_RURAL)
    lima = hogares["dominio"] == 8
    v.cifra("Pobreza en Lima Metropolitana", tasa(hogares["pobre"][lima], peso[lima]), POBREZA_LIMA_METROPOLITANA)

    referencia = pd.read_csv(REFERENCIA_DEPARTAMENTOS, dtype={"ccdd": str})
    for fila in referencia.itertuples():
        de_aqui = hogares["departamento"] == fila.ccdd
        if de_aqui.any():
            v.cifra(f"Pobreza en {fila.departamento}", tasa(hogares["pobre"][de_aqui], peso[de_aqui]), fila.pobreza_pct)
        else:
            v.registrar(f"Pobreza en {fila.departamento}", False, "sin hogares en la base")
    return v


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    # Sin año, la skill activada sola pasa --anio vacío: const evita que eso falle.
    parser.add_argument("--anio", nargs="?", type=int, const=ANIO, default=ANIO)
    args = parser.parse_args()
    if args.anio != ANIO:
        sys.exit(f"Este proyecto solo valida la ENAHO {ANIO}; se pidió {args.anio}.")

    zip_sumaria = DATOS / f"{CODIGO_INEI}-Modulo34.zip"
    zip_personas = DATOS / f"{CODIGO_INEI}-Modulo02.zip"
    for ruta in (zip_sumaria, zip_personas):
        if not ruta.is_file():
            sys.exit(f"Falta {ruta.name} en datos/. Bájalo con la skill descargando-enaho.")

    # 1. Leer y 2. normalizar. La sumaria estándar es sumaria-2024; se descarta la variante -12g.
    sumaria = normalizar_columnas(leer_dta(zip_sumaria, rf"(^|/)sumaria-{ANIO}\.dta$"))[COLUMNAS_SUMARIA]
    modulo02 = normalizar_columnas(leer_dta(zip_personas, rf"(^|/)enaho01-{ANIO}-200\.dta$"))[COLUMNAS_PERSONAS]
    sumaria = llaves_a_texto(sumaria, LLAVES_HOGAR + ["ubigeo"])
    modulo02 = llaves_a_texto(modulo02, LLAVES_PERSONA)

    # 3. Filtrar a los residentes habituales.
    es_residente = ((modulo02["p204"] == 1) & (modulo02["p205"] == 2)) | (
        (modulo02["p204"] == 2) & (modulo02["p206"] == 1)
    )
    personas = modulo02[es_residente]

    # 4. Unir. ubigeo, dominio y estrato salen solo de la sumaria.
    base = personas.merge(sumaria, on=LLAVES_HOGAR, how="left", validate="m:1")

    # 5. Construir.
    base["departamento"] = base["ubigeo"].str[:2]
    base["urbano"] = base["estrato"] <= 5
    base["pobre"] = base["pobreza"] <= 2
    base["peso_hogar"] = base["factor07"] * base["mieperho"]

    # 6. Validar. El archivo se escribe antes de fallar para que se pueda leer qué falló.
    resultado = validar(sumaria, modulo02, personas, base)
    SALIDAS.mkdir(exist_ok=True)
    ruta_validacion = SALIDAS / "validacion.txt"
    encabezado = f"Validación de la ENAHO {ANIO} contra las cifras de la sesión y del INEI\n\n"
    ruta_validacion.write_text(encabezado + "\n".join(resultado.lineas) + "\n", encoding="utf-8")
    if resultado.fallos:
        sys.exit(f"{resultado.fallos} comprobaciones fallaron. Revisa salidas/validacion.txt.")

    # 7. Guardar.
    base.to_parquet(SALIDAS / f"personas_{ANIO}.parquet", index=False)
    print(f"Listo: {len(base):,} personas en salidas/personas_{ANIO}.parquet; validación sin fallos.")


if __name__ == "__main__":
    main()
