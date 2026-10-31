"""Baja a datos/ los módulos 34 y 02 de la ENAHO 2024 y los límites departamentales."""

import argparse
import json
import os
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[4]
DATOS = RAIZ / "datos"

ANIO = 2024
CODIGO_INEI = 966
URL_INEI = "https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA"
MODULOS = ("34", "02")
URL_GEOJSON = (
    "https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/"
    "sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson"
)

INTENTOS = 3
PAUSA_SEGUNDOS = 5
TIEMPO_LIMITE_SEGUNDOS = 300


def zip_valido(ruta: Path) -> bool:
    if not ruta.is_file() or ruta.stat().st_size == 0:
        return False
    try:
        with zipfile.ZipFile(ruta) as archivo:
            return archivo.testzip() is None and len(archivo.namelist()) > 0
    except zipfile.BadZipFile:
        return False


def geojson_valido(ruta: Path) -> bool:
    if not ruta.is_file():
        return False
    try:
        return len(json.loads(ruta.read_text(encoding="utf-8"))["features"]) == 25
    except (json.JSONDecodeError, KeyError, TypeError, UnicodeDecodeError):
        return False


def descargar(url: str, destino: Path, es_valido) -> None:
    """Baja url a destino. Solo reemplaza destino cuando el archivo nuevo es válido."""
    if es_valido(destino):
        print(f"Ya estaba y es válido: {destino.name}")
        return

    temporal = destino.with_name(destino.name + ".part")
    pedido = urllib.request.Request(url, headers={"User-Agent": "enaho-skills"})
    ultimo_error = "el archivo bajado no es válido"

    for intento in range(1, INTENTOS + 1):
        print(f"Bajando {destino.name} (intento {intento} de {INTENTOS})")
        try:
            with urllib.request.urlopen(pedido, timeout=TIEMPO_LIMITE_SEGUNDOS) as respuesta:
                temporal.write_bytes(respuesta.read())
            if es_valido(temporal):
                os.replace(temporal, destino)
                print(f"Listo: {destino.name} ({destino.stat().st_size:,} bytes)")
                return
            ultimo_error = "el archivo bajado no es válido"
        except OSError as error:
            ultimo_error = str(error)
        temporal.unlink(missing_ok=True)
        if intento < INTENTOS:
            time.sleep(PAUSA_SEGUNDOS)

    sys.exit(f"No se pudo bajar {url}: {ultimo_error}")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--anio", nargs="?", type=int, const=ANIO, default=ANIO)
    args = parser.parse_args()
    if args.anio != ANIO:
        sys.exit(f"Este proyecto solo trabaja con la ENAHO {ANIO}; se pidió {args.anio}.")

    DATOS.mkdir(exist_ok=True)
    for modulo in MODULOS:
        nombre = f"{CODIGO_INEI}-Modulo{modulo}.zip"
        descargar(f"{URL_INEI}/{nombre}", DATOS / nombre, zip_valido)
    descargar(URL_GEOJSON, DATOS / "peru_departamental_simple.geojson", geojson_valido)


if __name__ == "__main__":
    main()
