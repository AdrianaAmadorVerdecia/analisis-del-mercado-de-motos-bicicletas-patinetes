# -*- coding: utf-8 -*-
"""ANALISIS.PY — todo el codigo del proyecto de vehiculos electricos en Cuba.

Este es el UNICO archivo de codigo del proyecto. Aqi dentro se va metiendo todo,
organizado por secciones:

    CONFIGURACION GENERAL     constantes, colores, etiquetas
    UTILIDADES               formato de numeros y tablas de markdown
    FUENTE 1: REVOLICO       carga de datos, calculos, tablas y graficos
    OTRAS FUENTES            Telegram, encuestas, mercados (mas adelante)

El notebook `proyecto.ipynb` NO tiene codigo: solo importa desde aqui y muestra
los resultados.

Uso desde el notebook:

    from analisis import *

    print(tabla_precios())
    ejecutar()

Uso desde la terminal:

    python analisis.py
"""

from __future__ import annotations

import json
import statistics as stat
from pathlib import Path

import matplotlib.pyplot as plt

# ==============================================================================
# CONFIGURACION GENERAL
# ==============================================================================

RAIZ = Path(__file__).resolve().parent
CARPETA_GRAFICOS = RAIZ / "graficos"

TASA_CUP_POR_USD = 745
PRESUPUESTO_LUCY = 1500

ORDEN = ["Moto electrica", "Bicicleta electrica", "Patinete electrico"]

ETIQUETAS = {
    "Moto electrica": "Moto eléctrica",
    "Bicicleta electrica": "Bicicleta eléctrica",
    "Patinete electrico": "Patinete eléctrico",
}

# Colores vivos y separados entre si, para que se distingan de un vistazo.
COLORES = {
    "Moto electrica": "#E63946",
    "Bicicleta electrica": "#1D6FE0",
    "Patinete electrico": "#F9A602",
}
COLOR_FUERA = "#C9CDD2"      # anuncios que Lucy no puede comprar
COLOR_PRESUPUESTO = "#E63946"
COLOR_MEDIANA = "#2B2B2B"


# ==============================================================================
# UTILIDADES
# ==============================================================================

# ==============================================================================
# FUENTE 1: REVOLICO  (data/anuncios_revolico.json)
# ==============================================================================

RUTA_DATOS_REVOLICO = RAIZ / "data" / "anuncios_revolico.json"


def cargar_anuncios() -> list[dict]:
    """Devuelve la lista de anuncios del JSON de Revolico."""
    with open(RUTA_DATOS_REVOLICO, encoding="utf-8") as f:
        return json.load(f)["anuncios"]


def grupo(categoria: str, anuncios: list[dict] | None = None) -> list[dict]:
    """Devuelve los anuncios de una categoria."""
    anuncios = cargar_anuncios() if anuncios is None else anuncios
    return [a for a in anuncios if a["tipo_vehiculo"] == categoria]


def alcanzables(categoria: str, anuncios: list[dict] | None = None) -> list[dict]:
    """Anuncios de la categoria que caben en el presupuesto de Lucy."""
    return [a for a in grupo(categoria, anuncios) if a["precio"] <= PRESUPUESTO_LUCY]


# --------------------------------- calculos estadisticos (revolico)

def resumen_precios(anuncios: list[dict] | None = None) -> dict[str, dict]:
    """Numero de anuncios, promedio, mediana, minimo, maximo y desviacion por categoria."""
    anuncios = cargar_anuncios() if anuncios is None else anuncios
    resumen = {}
    for categoria in ORDEN:
        precios = [a["precio"] for a in grupo(categoria, anuncios)]
        autonomias = [a["autonomia_km"] for a in grupo(categoria, anuncios)]
        resumen[categoria] = {
            "anuncios": len(precios),
            "promedio": stat.mean(precios),
            "mediana": stat.median(precios),
            "minimo": min(precios),
            "maximo": max(precios),
            "desviacion": stat.pstdev(precios),
            "autonomia_mediana": stat.median(autonomias),
        }
    return resumen


def valores_atipicos(valores: list[float]) -> list[float]:
    """Valores fuera del rango intercuartilico (regla de 1.5 x IQR)."""
    q1, q3 = stat.quantiles(valores, n=4)[0], stat.quantiles(valores, n=4)[2]
    limite = 1.5 * (q3 - q1)
    return [v for v in valores if v < q1 - limite or v > q3 + limite]


def resumen_presupuesto(anuncios: list[dict] | None = None) -> dict[str, dict]:
    """Que se puede comprar con el presupuesto de Lucy, categoria por categoria."""
    anuncios = cargar_anuncios() if anuncios is None else anuncios
    resumen = {}
    for categoria in ORDEN:
        todos = grupo(categoria, anuncios)
        dentro = alcanzables(categoria, anuncios)
        fila = {"anuncios": len(todos), "alcanzables": len(dentro)}
        if dentro:
            precios = [a["precio"] for a in dentro]
            autonomias = [a["autonomia_km"] for a in dentro]
            fila.update({
                "precio_min": min(precios),
                "precio_mediana": stat.median(precios),
                "autonomia_min": min(autonomias),
                "autonomia_mediana": stat.median(autonomias),
                "autonomia_max": max(autonomias),
            })
        else:
            fila.update({k: None for k in (
                "precio_min", "precio_mediana",
                "autonomia_min", "autonomia_mediana", "autonomia_max")})
        resumen[categoria] = fila
    return resumen


# --------------------------------- tablas en markdown (revolico)

def _formato(valor, decimales: int = 0) -> str:
    """Formatea un numero con separador de miles y coma decimal."""
    if valor is None:
        return "—"
    if decimales == 0:
        return f"{valor:,.0f}".replace(",", ".")
    entero, parte = f"{valor:.{decimales}f}".split(".")
    return f"{entero.replace(',', '.')},{parte}"


def tabla_markdown(encabezados: list[str], filas: list[list[str]]) -> str:
    """Arma una tabla de markdown a partir de encabezados y filas ya formateadas."""
    separador = "| " + " | ".join("---" for _ in encabezados) + " |"
    lineas = [
        "| " + " | ".join(encabezados) + " |",
        separador,
    ]
    lineas += ["| " + " | ".join(fila) + " |" for fila in filas]
    return "\n".join(lineas)


def tabla_precios_markdown(anuncios: list[dict] | None = None) -> str:
    """Tabla de precio por categoria."""
    resumen = resumen_precios(anuncios)
    filas = []
    for categoria in ORDEN:
        r = resumen[categoria]
        filas.append([
            ETIQUETAS[categoria],
            str(r["anuncios"]),
            _formato(r["promedio"]),
            _formato(r["mediana"]),
            _formato(r["minimo"]),
            _formato(r["maximo"]),
            _formato(r["autonomia_mediana"]),
        ])
    return tabla_markdown(
        ["Categoría", "Anuncios", "Precio promedio", "Precio más común (mediana)",
         "Precio más bajo", "Precio más alto", "Autonomía más común (km)"],
        filas,
    )


def tabla_atipicos_markdown(anuncios: list[dict] | None = None) -> str:
    """Tabla que muestra si hay precios extremos que deformen el promedio."""
    anuncios = cargar_anuncios() if anuncios is None else anuncios
    filas = []
    for categoria in ORDEN:
        precios = [a["precio"] for a in grupo(categoria, anuncios)]
        atipicos = valores_atipicos(precios)
        sin_atipicos = [p for p in precios if p not in atipicos]
        filas.append([
            ETIQUETAS[categoria],
            str(len(atipicos)),
            _formato(stat.mean(precios)),
            _formato(stat.mean(sin_atipicos)),
            (f"{stat.mean(sin_atipicos) - stat.mean(precios):+,.0f}"
             .replace(",", ".")).replace("+", "+").replace("-", "−"),
        ])
    return tabla_markdown(
        ["Categoría", "Precios extremos", "Promedio", "Promedio sin extremos", "Diferencia"],
        filas,
    )


def tabla_presupuesto_markdown(anuncios: list[dict] | None = None) -> str:
    """Tabla de lo que Lucy puede comprar con su presupuesto."""
    resumen = resumen_presupuesto(anuncios)
    filas = []
    for categoria in ORDEN:
        r = resumen[categoria]
        filas.append([
            ETIQUETAS[categoria],
            str(r["anuncios"]),
            f"**{r['alcanzables']}**",
            _formato(r["precio_min"]),
            _formato(r["precio_mediana"]),
            _formato(r["autonomia_min"]),
            _formato(r["autonomia_mediana"]),
            _formato(r["autonomia_max"]),
        ])
    return tabla_markdown(
        ["Categoría", "Anuncios publicados", "Anuncios que puede comprar",
         "Precio más bajo", "Precio más común", "Autonomía mínima (km)",
         "Autonomía más común (km)", "Autonomía más alta (km)"],
        filas,
    )


def tabla_motos_alcanzables_markdown(anuncios: list[dict] | None = None) -> str:
    """Las motos baratas, que son el caso interesante dentro del presupuesto."""
    dentro = sorted(alcanzables("Moto electrica", anuncios), key=lambda a: a["precio"])
    filas = [
        [_formato(a["precio"]), str(a["autonomia_km"]), a["marca"]]
        for a in dentro
    ]
    return tabla_markdown(["Precio (USD)", "Autonomía (km)", "Marca"], filas)


# --------------------------------- graficos (revolico)

def figura_precios(ruta: Path | None = None):
    """Barras: precio promedio y mas comun de cada categoria."""
    anuncios = cargar_anuncios()
    resumen = resumen_precios(anuncios)

    nombres = [ETIQUETAS[c] for c in ORDEN]
    promedios = [resumen[c]["promedio"] for c in ORDEN]
    medianas = [resumen[c]["mediana"] for c in ORDEN]

    fig, ax = plt.subplots(figsize=(11, 6.5))
    posiciones = list(range(len(nombres)))
    ancho = 0.36

    colores_promedio = [COLORES[c] for c in ORDEN]

    ax.bar([p - ancho / 2 for p in posiciones], promedios, ancho,
           color=colores_promedio, edgecolor="white", linewidth=1.5,
           label="Precio promedio")
    ax.bar([p + ancho / 2 for p in posiciones], medianas, ancho,
           color=[c + "99" for c in colores_promedio], edgecolor="white", linewidth=1.5,
           hatch="//", label="Precio más común (mediana)")

    for p, valor in zip([q - ancho / 2 for q in posiciones], promedios):
        ax.text(p, valor + 70, f"{valor:,.0f}".replace(",", "."),
                ha="center", fontsize=12, fontweight="bold", color=COLOR_MEDIANA)
    for p, valor in zip([q + ancho / 2 for q in posiciones], medianas):
        ax.text(p, valor + 70, f"{valor:,.0f}".replace(",", "."),
                ha="center", fontsize=11, color="#555555")

    ax.set_xticks(posiciones)
    ax.set_xticklabels(
        [f"{n}\n({c} anuncios)" for n, c in
         zip(nombres, [resumen[c]["anuncios"] for c in ORDEN])],
        fontsize=12)
    ax.set_ylabel("Precio en dólares (USD)", fontsize=12)
    ax.set_ylim(0, 3100)
    ax.tick_params(axis="y", labelsize=11)
    ax.set_title("Cuánto cuesta cada tipo de vehículo eléctrico\n"
                 "224 anuncios de La Habana publicados en Revolico",
                 fontsize=15, fontweight="bold", pad=18)
    ax.legend(frameon=False, fontsize=12, loc="upper right")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    fig.tight_layout()

    if ruta is not None:
        fig.savefig(ruta, dpi=150)
        plt.close(fig)
    return fig


def _anotar(ax, punto, texto, color):
    """Escribe una etiqueta junto a un punto, con su linea guía."""
    ax.annotate(
        texto,
        xy=(punto["precio"], punto["autonomia_km"]),
        xytext=(12, 12), textcoords="offset points",
        fontsize=10.5, color=color, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=color, lw=1.2, alpha=0.95),
        arrowprops=dict(arrowstyle="->", color=color, lw=1.3),
    )


def figura_presupuesto(ruta: Path | None = None):
    """Tres paneles apilados: precio contra autonomia, con el presupuesto de Lucy."""
    anuncios = cargar_anuncios()
    resumen = resumen_presupuesto(anuncios)

    limite_x = (0, 3600)
    limite_y = (0, 185)

    fig, ejes = plt.subplots(3, 1, figsize=(13, 16.5), sharex=True)
    fig.subplots_adjust(hspace=0.18)

    for eje, categoria in zip(ejes, ORDEN):
        todos = grupo(categoria, anuncios)
        dentro = alcanzables(categoria, anuncios)
        color = COLORES[categoria]

        # franja del presupuesto
        eje.axvspan(limite_x[0], PRESUPUESTO_LUCY, color="#FFF4E0", zorder=0)
        # anuncios fuera del alcance, de fondo
        eje.scatter([a["precio"] for a in todos if a["precio"] > PRESUPUESTO_LUCY],
                    [a["autonomia_km"] for a in todos if a["precio"] > PRESUPUESTO_LUCY],
                    s=55, color=COLOR_FUERA, edgecolor="white", linewidth=0.8, zorder=2)
        # anuncios que Lucy puede comprar
        eje.scatter([a["precio"] for a in dentro], [a["autonomia_km"] for a in dentro],
                    s=95, color=color, edgecolor="white", linewidth=1.4, zorder=3)

        # linea del presupuesto
        eje.axvline(PRESUPUESTO_LUCY, color=COLOR_PRESUPUESTO, linestyle="--",
                    linewidth=2.2, zorder=1)
        # linea de la autonomia mas comun dentro del presupuesto
        if resumen[categoria]["autonomia_mediana"] is not None:
            eje.axhline(resumen[categoria]["autonomia_mediana"], color="#444444",
                        linestyle=":", linewidth=1.6, zorder=1)
            eje.text(limite_x[0] + 60, resumen[categoria]["autonomia_mediana"] + 4,
                     f"autonomía más común: {resumen[categoria]['autonomia_mediana']:.0f} km",
                     fontsize=10.5, color="#333333", style="italic")

        # los tres anuncios que cuentan la historia de cada categoría
        noteworthy = []
        if dentro:
            noteworthy.append(min(dentro, key=lambda a: a["precio"]))
            noteworthy.append(max(dentro, key=lambda a: a["autonomia_km"]))
            mejor_rendimiento = max(dentro, key=lambda a: a["autonomia_km"] / a["precio"])
            if mejor_rendimiento["id"] not in {a["id"] for a in noteworthy}:
                noteworthy.append(mejor_rendimiento)
        vistos = set()
        for punto in noteworthy:
            if punto["id"] in vistos:
                continue
            vistos.add(punto["id"])
            _anotar(eje, punto,
                    f"{punto['precio']:,.0f}".replace(",", ".") + " USD · "
                    + f"{punto['autonomia_km']} km", color)

        r = resumen[categoria]
        titulo = (f"{ETIQUETAS[categoria]}:  {r['alcanzables']} anuncios de {r['anuncios']}"
                  f"  le quedan dentro del presupuesto")
        eje.set_title(titulo, fontsize=14, fontweight="bold", color=color, loc="left", pad=12)

        eje.set_xlim(*limite_x)
        eje.set_ylim(*limite_y)
        eje.set_xticks(range(0, limite_x[1] + 1, 500))
        eje.set_yticks(range(0, limite_y[1], 20))
        eje.set_ylabel("Autonomía (km)", fontsize=12)
        eje.grid(True, linestyle=":", alpha=0.35)
        eje.spines[["top", "right"]].set_visible(False)

        if categoria == ORDEN[0]:
            eje.text(PRESUPUESTO_LUCY - 40, limite_y[1] * 0.96,
                     "◀ hasta aquí puede comprar Lucy", ha="right", fontsize=11.5,
                     color=COLOR_PRESUPUESTO, fontweight="bold")

    ejes[-1].set_xlabel("Precio en dólares (USD)", fontsize=13)
    ejes[-1].tick_params(axis="x", labelsize=11)

    fig.suptitle(
        "Qué puede comprar Lucy con 1.500 dólares\n"
        "Cada punto es un anuncio: precio hacia la derecha, autonomía hacia arriba",
        fontsize=17, fontweight="bold", y=0.985)
    if ruta is not None:
        fig.savefig(ruta, dpi=150)
        plt.close(fig)
    return fig


def ejecutar():
    """Genera y guarda todos los graficos del proyecto."""
    CARPETA_GRAFICOS.mkdir(exist_ok=True)
    figura_precios(CARPETA_GRAFICOS / "analisis_precios.png")
    figura_presupuesto(CARPETA_GRAFICOS / "analisis_presupuesto.png")
    return CARPETA_GRAFICOS


# ==============================================================================
# OTRAS FUENTES
#   Telegram, encuestas a personas y mercados de vehiculos electricos.
#   Aqui se van anadiendo sus datos y sus analisis, en el mismo archivo.
# ==============================================================================


if __name__ == "__main__":
    destino = ejecutar()
    print("Gráficos guardados en:", destino)
    print()
    print("PRECIOS POR CATEGORÍA")
    print(tabla_precios_markdown())
    print()
    print("PRECIOS EXTREMOS")
    print(tabla_atipicos_markdown())
    print()
    print("PRESUPUESTO DE LUCY")
    print(tabla_presupuesto_markdown())
    print()
    print("MOTOS ALCANZABLES")
    print(tabla_motos_alcanzables_markdown())