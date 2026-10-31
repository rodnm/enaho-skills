"""Hace el mapa de pobreza por departamento de la ENAHO 2024 en mapas/."""

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

RAIZ = Path(__file__).resolve().parents[4]
BASE = RAIZ / "salidas" / "personas_2024.parquet"
GEOJSON = RAIZ / "datos" / "peru_departamental_simple.geojson"
REFERENCIA = RAIZ / "referencias" / "pobreza_departamento_2024.csv"
DESTINO = RAIZ / "mapas" / "pobreza_departamento.png"

LLAVES_HOGAR = ["conglome", "vivienda", "hogar"]
DEPARTAMENTOS = 25
TOLERANCIA = 0.1

# Un solo tono, de claro a oscuro.
ESCALA = LinearSegmentedColormap.from_list("azules", ["#cde2fb", "#6da7ec", "#256abf", "#0d366b"])
COLOR_BORDE = "#fcfcfb"
COLOR_TEXTO = "#0b0b0b"
COLOR_SECUNDARIO = "#52514e"
COLOR_FONDO = "#fcfcfb"


def pobreza_por_departamento(base: pd.DataFrame) -> pd.DataFrame:
    # Como la cifra oficial: una fila por hogar, expandida a sus personas.
    hogares = base.drop_duplicates(LLAVES_HOGAR)
    ponderado = (hogares["pobre"] * hogares["peso_hogar"]).groupby(hogares["departamento"]).sum()
    tasas = 100 * ponderado / hogares["peso_hogar"].groupby(hogares["departamento"]).sum()
    return tasas.rename("pobreza_pct").rename_axis("departamento").reset_index()


def unir_con_limites(tasas: pd.DataFrame, limites: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Une por código, nunca por nombre, y exige los 25 departamentos con dato."""
    limites = limites.assign(departamento=limites["FIRST_IDDP"].astype(str))
    mapa = limites.merge(tasas, on="departamento", how="outer", validate="1:1", indicator=True)
    sueltos = mapa.loc[mapa["_merge"] != "both", "departamento"].tolist()
    if sueltos:
        sys.exit(f"Estos códigos no se unieron entre la base y el GeoJSON: {sueltos}.")
    if len(mapa) != DEPARTAMENTOS or mapa["pobreza_pct"].isna().any():
        sys.exit(f"Se esperaban {DEPARTAMENTOS} departamentos con dato; hay {mapa['pobreza_pct'].notna().sum()}.")
    return mapa


def comprobar_referencia(mapa: gpd.GeoDataFrame) -> None:
    referencia = pd.read_csv(REFERENCIA, dtype={"ccdd": str}).set_index("ccdd")["pobreza_pct"]
    diferencia = (mapa.set_index("departamento")["pobreza_pct"] - referencia).abs()
    alejados = diferencia[diferencia > TOLERANCIA]
    if not alejados.empty:
        sys.exit(f"Estos departamentos difieren más de {TOLERANCIA} puntos de la referencia: {alejados.round(2).to_dict()}.")


def dibujar(mapa: gpd.GeoDataFrame) -> None:
    figura, eje = plt.subplots(figsize=(7.4, 8.8), facecolor=COLOR_FONDO)
    mapa.plot(
        column="pobreza_pct", ax=eje, cmap=ESCALA, vmin=0, vmax=mapa["pobreza_pct"].max(),
        edgecolor=COLOR_BORDE, linewidth=0.8, legend=True,
        legend_kwds={"label": "% de personas", "shrink": 0.5, "aspect": 22, "pad": 0.02},
    )
    eje.set_axis_off()

    barra = figura.axes[-1]
    barra.tick_params(colors=COLOR_SECUNDARIO, labelsize=9, length=0)
    barra.yaxis.label.set_color(COLOR_SECUNDARIO)
    for borde in barra.spines.values():
        borde.set_visible(False)

    figura.suptitle(
        "Pobreza monetaria por departamento, Perú 2024",
        x=0.03, y=0.975, ha="left", color=COLOR_TEXTO, fontsize=15, fontweight="bold",
    )
    figura.text(
        0.03, 0.02, "Fuente: INEI, ENAHO 2024. Ponderado por hogar con factor07 × mieperho.",
        color=COLOR_SECUNDARIO, fontsize=8.5,
    )
    figura.tight_layout(rect=(0, 0.04, 1, 0.95))

    DESTINO.parent.mkdir(exist_ok=True)
    figura.savefig(DESTINO, dpi=200, facecolor=COLOR_FONDO, metadata={"Software": None})
    plt.close(figura)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    if not BASE.is_file():
        sys.exit(f"Falta {BASE.name} en salidas/. Créala con la skill limpiando-enaho.")
    if not GEOJSON.is_file():
        sys.exit(f"Falta {GEOJSON.name} en datos/. Bájalo con la skill descargando-enaho.")

    mapa = unir_con_limites(pobreza_por_departamento(pd.read_parquet(BASE)), gpd.read_file(GEOJSON))
    comprobar_referencia(mapa)
    dibujar(mapa)

    ordenado = mapa.sort_values("pobreza_pct", ascending=False)
    extremos = pd.concat([ordenado.head(3), ordenado.tail(3)])
    cifras = ", ".join(f"{fila.NOMBDEP}: {fila.pobreza_pct:.1f} %" for fila in extremos.itertuples())
    print(f"{DESTINO.relative_to(RAIZ).as_posix()} ({DEPARTAMENTOS} departamentos con dato; {cifras})")


if __name__ == "__main__":
    main()
