"""Grafica la pobreza de la ENAHO 2024 por área, sexo o edad en figuras/."""

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

RAIZ = Path(__file__).resolve().parents[4]
BASE = RAIZ / "salidas" / "personas_2024.parquet"
FIGURAS = RAIZ / "figuras"

LLAVES_HOGAR = ["conglome", "vivienda", "hogar"]

COLOR_BARRA = "#2a78d6"
COLOR_TEXTO = "#0b0b0b"
COLOR_SECUNDARIO = "#52514e"
COLOR_FONDO = "#fcfcfb"

GRUPOS_EDAD = [0, 15, 30, 45, 60, 200]
NOMBRES_EDAD = ["0 a 14 años", "15 a 29 años", "30 a 44 años", "45 a 59 años", "60 años y más"]
NOTA_HOGAR = "Ponderado por hogar con factor07 × mieperho."
NOTA_PERSONA = "Ponderado por persona con facpob07."


def tasa_por_grupo(tabla: pd.DataFrame, grupo: pd.Series, peso: str) -> pd.Series:
    ponderado = (tabla["pobre"] * tabla[peso]).groupby(grupo, observed=True).sum()
    return 100 * ponderado / tabla[peso].groupby(grupo, observed=True).sum()


def por_area(base: pd.DataFrame) -> pd.Series:
    # Como la cifra oficial: una fila por hogar, expandida a sus personas.
    hogares = base.drop_duplicates(LLAVES_HOGAR)
    area = hogares["urbano"].map({True: "Urbana", False: "Rural"})
    return tasa_por_grupo(hogares, area, "peso_hogar").sort_values(ascending=False)


def por_sexo(base: pd.DataFrame) -> pd.Series:
    sexo = base["p207"].map({1: "Hombres", 2: "Mujeres"})
    return tasa_por_grupo(base, sexo, "facpob07").sort_values(ascending=False)


def por_edad(base: pd.DataFrame) -> pd.Series:
    # Las edades conservan su orden natural.
    edad = pd.cut(base["p208a"], bins=GRUPOS_EDAD, right=False, labels=NOMBRES_EDAD)
    return tasa_por_grupo(base, edad, "facpob07")


GRAFICOS = {
    "area": (por_area, "área de residencia", NOTA_HOGAR),
    "sexo": (por_sexo, "sexo", NOTA_PERSONA),
    "edad": (por_edad, "grupo de edad", NOTA_PERSONA),
}


def dibujar(tasas: pd.Series, tema: str, nota: str, destino: Path) -> None:
    figura, eje = plt.subplots(figsize=(7, 4.4), facecolor=COLOR_FONDO)
    eje.set_facecolor(COLOR_FONDO)
    posiciones = range(len(tasas))
    barras = eje.bar(posiciones, tasas.to_numpy(), width=0.62, color=COLOR_BARRA)
    eje.bar_label(barras, fmt="%.1f %%", padding=4, color=COLOR_TEXTO, fontsize=12, fontweight="bold")

    eje.set_xticks(list(posiciones), [str(nombre) for nombre in tasas.index], color=COLOR_TEXTO, fontsize=11)
    eje.set_ylim(0, max(tasas.max() * 1.18, 10))
    eje.set_ylabel("% de personas en situación de pobreza", color=COLOR_SECUNDARIO, fontsize=10)
    eje.tick_params(axis="y", colors=COLOR_SECUNDARIO, labelsize=9, length=0)
    eje.tick_params(axis="x", length=0)
    for lado in ("top", "right", "left"):
        eje.spines[lado].set_visible(False)
    eje.spines["bottom"].set_color(COLOR_SECUNDARIO)

    figura.suptitle(
        f"Pobreza monetaria por {tema}, Perú 2024",
        x=0.02, y=0.97, ha="left", color=COLOR_TEXTO, fontsize=14, fontweight="bold",
    )
    figura.text(0.02, 0.02, f"Fuente: INEI, ENAHO 2024. {nota}", color=COLOR_SECUNDARIO, fontsize=8.5)
    figura.tight_layout(rect=(0, 0.05, 1, 0.94))

    FIGURAS.mkdir(exist_ok=True)
    figura.savefig(destino, dpi=200, facecolor=COLOR_FONDO, metadata={"Software": None})
    plt.close(figura)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--por", choices=sorted(GRAFICOS), help="Sin este argumento hace los tres gráficos.")
    args = parser.parse_args()

    if not BASE.is_file():
        sys.exit(f"Falta {BASE.name} en salidas/. Créala con la skill limpiando-enaho.")
    base = pd.read_parquet(BASE)

    for nombre in [args.por] if args.por else sorted(GRAFICOS):
        calcular, tema, nota = GRAFICOS[nombre]
        tasas = calcular(base)
        destino = FIGURAS / f"pobreza_por_{nombre}.png"
        dibujar(tasas, tema, nota, destino)
        cifras = ", ".join(f"{grupo}: {valor:.1f} %" for grupo, valor in tasas.items())
        print(f"{destino.relative_to(RAIZ).as_posix()} ({cifras})")


if __name__ == "__main__":
    main()
