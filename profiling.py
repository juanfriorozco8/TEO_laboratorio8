from __future__ import annotations

import argparse
from collections.abc import Callable, Iterator
from contextlib import contextmanager
import csv
from dataclasses import dataclass
import math
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

RAIZ = Path(__file__).resolve().parent
CARPETAS: dict[int, str] = {
    1: "problema1_contador_anidado",
    2: "problema2_secuencia_break",
    3: "problema3_secuencia_paso4",
}
TAMANOS: tuple[int, ...] = (1, 10, 100, 1_000, 10_000, 100_000, 1_000_000)


@dataclass(frozen=True)
class Medicion:
    n: int
    tiempo_segundos: float | None
    estado: str
    repeticiones_por_muestra: int
    muestras: int
    limite_proceso_segundos: float | None


def compilar(problema: int, destino: Path) -> Path:
    compilador = shutil.which(os.environ.get("CXX", "c++"))
    if compilador is None:
        raise RuntimeError("Se necesita GCC o Clang con soporte para C++17.")
    ejecutable = destino / f"problema{problema}"
    subprocess.run(
        [compilador, "-std=c++17", "-O0", "-Wall", "-Wextra", "-Wpedantic", "-Werror",
         str(RAIZ / CARPETAS[problema] / "main.cpp"), "-o", str(ejecutable)],
        check=True,
    )
    return ejecutable


def muestra(ejecutable: Path, n: int, repeticiones: int, limite: float | None) -> float:
    comando = [str(ejecutable), str(n), "--profile", "--repeticiones", str(repeticiones)]
    inicio = time.monotonic()
    with subprocess.Popen(
        comando,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    ) as proceso:
        try:
            while True:
                transcurrido = time.monotonic() - inicio
                espera = 30.0 if limite is None else min(30.0, max(0.001, limite - transcurrido))
                try:
                    _, errores = proceso.communicate(timeout=espera)
                    break
                except subprocess.TimeoutExpired:
                    transcurrido = time.monotonic() - inicio
                    if limite is not None and transcurrido >= limite:
                        raise subprocess.TimeoutExpired(comando, limite)
                    print(f"  Sigue calculando n={n}: {transcurrido / 60:.1f} minutos de ejecución.", flush=True)
        except BaseException:
            if proceso.poll() is None:
                proceso.kill()
            proceso.communicate()
            raise
        if proceso.returncode != 0:
            raise subprocess.CalledProcessError(proceso.returncode, comando, stderr=errores)
    segundos = float(errores.strip())
    if segundos < 0 or not math.isfinite(segundos):
        raise RuntimeError("El programa devolvió un tiempo inválido.")
    return segundos


def medir(ejecutable: Path, n: int, limite: float | None, cantidad: int,
          guardar: Callable[[Medicion], None]) -> Medicion:
    if cantidad < 1:
        raise ValueError("La cantidad de mediciones debe ser al menos 1.")
    tiempos: list[float] = []
    try:
        for indice in range(cantidad):
            print(f"  Medición {indice + 1} de {cantidad}.", flush=True)
            tiempos.append(muestra(ejecutable, n, 1, limite))
            dato = Medicion(n, statistics.median(tiempos), "completado", 1, len(tiempos), limite)
            guardar(dato)
    except subprocess.TimeoutExpired:
        dato = (Medicion(n, statistics.median(tiempos), "completado", 1, len(tiempos), limite)
                if tiempos else Medicion(n, None, "limite_excedido", 1, 0, limite))
        guardar(dato)
        return dato
    return dato


def cargar_tabla(carpeta: Path) -> dict[int, Medicion]:
    archivo = carpeta / "tabla.csv"
    if not archivo.exists():
        return {}
    datos: dict[int, Medicion] = {}
    with archivo.open(newline="", encoding="utf-8") as entrada:
        for fila in csv.DictReader(entrada):
            n = int(fila["n"])
            segundos = float(fila["tiempo_segundos"]) if fila["tiempo_segundos"] else None
            limite = float(fila["limite_proceso_segundos"]) if fila["limite_proceso_segundos"] else None
            dato = Medicion(n, segundos, fila["estado"], int(fila["repeticiones_por_muestra"]),
                            int(fila["muestras"]), limite)
            if (n not in TAMANOS or n in datos or dato.repeticiones_por_muestra < 1
                    or dato.muestras < 0 or dato.estado not in ("completado", "limite_excedido")
                    or (segundos is not None and (not math.isfinite(segundos) or segundos < 0))
                    or (limite is not None and (not math.isfinite(limite) or limite <= 0))
                    or (dato.estado == "completado" and (segundos is None or dato.muestras < 1))
                    or (dato.estado == "limite_excedido" and (segundos is not None or limite is None))):
                raise ValueError(f"La tabla de {carpeta.name} contiene una medición inválida.")
            datos[n] = dato
    return datos


@contextmanager
def mantener_despierto() -> Iterator[None]:
    comando = shutil.which("caffeinate") if sys.platform == "darwin" else None
    proceso: subprocess.Popen[bytes] | None = None
    try:
        if comando is not None:
            proceso = subprocess.Popen([comando, "-i", "-w", str(os.getpid())],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        yield
    finally:
        if proceso is not None and proceso.poll() is None:
            try:
                proceso.terminate()
            except ProcessLookupError:
                pass
            try:
                proceso.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proceso.kill()
                proceso.wait()


def guardar_tabla(carpeta: Path, datos: list[Medicion]) -> None:
    temporal: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", newline="", encoding="utf-8", dir=carpeta,
                                         prefix=".tabla-", delete=False) as archivo:
            temporal = Path(archivo.name)
            tabla = csv.writer(archivo)
            tabla.writerow([
                "n", "tiempo_segundos", "estado", "repeticiones_por_muestra", "muestras",
                "limite_proceso_segundos",
            ])
            for dato in datos:
                tabla.writerow([
                    dato.n, dato.tiempo_segundos, dato.estado, dato.repeticiones_por_muestra,
                    dato.muestras, dato.limite_proceso_segundos,
                ])
        temporal.replace(carpeta / "tabla.csv")
    finally:
        if temporal is not None:
            temporal.unlink(missing_ok=True)


def guardar_grafica(problema: int, datos: list[Medicion]) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    completos = [dato for dato in datos if dato.tiempo_segundos is not None]
    incompletos = [dato for dato in datos if dato.tiempo_segundos is None]
    figura, ejes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
    figura.suptitle(f"Problema {problema}: tamaño de entrada vs. tiempo", weight="bold")
    for eje in ejes:
        eje.plot(
            [dato.n for dato in completos],
            [max(dato.tiempo_segundos or 0.0, 1e-12) for dato in completos],
            "o-", color="#185b85", label="Tiempo medido",
        )
        eje.set_xlabel("Tamaño de entrada n")
        eje.set_ylabel("Tiempo por ejecución (segundos)")
        eje.grid(True, alpha=0.25)
    ejes[0].set_title("Mediciones completas: escala lineal")
    ejes[1].set_title("Todos los tamaños: escala logarítmica")
    ejes[1].set_xscale("log")
    ejes[1].set_yscale("log")
    if incompletos:
        ejes[1].scatter(
            [dato.n for dato in incompletos],
            [dato.limite_proceso_segundos for dato in incompletos],
            marker="x", color="#a83523", s=70, label="Límite del proceso; sin tiempo final",
        )
    ejes[1].set_xticks(list(TAMANOS))
    ejes[1].set_xlim(0.75, 1_400_000)
    ejes[1].legend(fontsize=8)
    figura.savefig(
        RAIZ / CARPETAS[problema] / "grafica.png", dpi=180,
        bbox_inches="tight", pad_inches=0.15,
    )
    plt.close(figura)


def main() -> int:
    parser = argparse.ArgumentParser(description="Ejecutar y medir los programas del Laboratorio 8.")
    parser.add_argument("--problema", type=int, choices=CARPETAS)
    parser.add_argument("--ejecutar", type=int, metavar="N", help="Mostrar la salida de un problema para N.")
    parser.add_argument("--limite", type=float, default=5.0, help="Máximo de segundos por proceso (5 por defecto).")
    parser.add_argument("--sin-limite", action="store_true", help="Medir hasta que cada proceso termine.")
    parser.add_argument("--muestras", type=int, default=1, help="Mediciones por tamaño (1 por defecto, sin corrida piloto).")
    parser.add_argument("--repetir", action="store_true", help="Volver a medir también los tamaños ya completados.")
    opciones = parser.parse_args()
    if not math.isfinite(opciones.limite) or opciones.limite <= 0:
        parser.error("El límite debe ser positivo y finito.")
    if opciones.muestras < 1:
        parser.error("--muestras debe ser al menos 1.")
    if opciones.ejecutar is not None:
        if opciones.problema is None or not 1 <= opciones.ejecutar <= 1_000_000:
            parser.error("--ejecutar requiere --problema y un N entre 1 y 1000000.")
    elegidos = (opciones.problema,) if opciones.problema is not None else tuple(CARPETAS)
    limite: float | None = None if opciones.sin_limite else opciones.limite
    try:
        with tempfile.TemporaryDirectory(prefix="laboratorio8-") as temporal, mantener_despierto():
            destino = Path(temporal)
            os.environ["MPLCONFIGDIR"] = str(destino / "matplotlib")
            if opciones.ejecutar is None:
                import matplotlib
            for problema in elegidos:
                ejecutable = compilar(problema, destino)
                if opciones.ejecutar is not None:
                    subprocess.run([str(ejecutable), str(opciones.ejecutar)], check=True)
                    continue
                carpeta = RAIZ / CARPETAS[problema]
                anteriores = cargar_tabla(carpeta)

                def guardar(dato: Medicion) -> None:
                    anteriores[dato.n] = dato
                    guardar_tabla(carpeta, sorted(anteriores.values(), key=lambda fila: fila.n))

                for n in TAMANOS:
                    anterior = anteriores.get(n)
                    if not opciones.repetir and anterior is not None and anterior.estado == "completado":
                        print(f"Problema {problema}, n={n}: conservado ({anterior.tiempo_segundos:.9g} s).", flush=True)
                        continue
                    print(f"Problema {problema}, n={n}...", flush=True)
                    dato = medir(ejecutable, n, limite, opciones.muestras, guardar)
                    if dato.tiempo_segundos is None:
                        print("  Límite excedido; sin tiempo final.", flush=True)
                    else:
                        print(f"  {dato.tiempo_segundos:.9g} s", flush=True)
                guardar_grafica(problema, sorted(anteriores.values(), key=lambda fila: fila.n))
                print(f"Problema {problema}: tabla y gráfica guardadas en {CARPETAS[problema]}.", flush=True)
    except KeyboardInterrupt:
        print("\nEjecución detenida. Las mediciones terminadas quedaron guardadas.", file=sys.stderr)
        return 130
    except ModuleNotFoundError:
        print("Para generar las gráficas, instala Matplotlib: python3 -m pip install matplotlib", file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
