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

import matplotlib.patheffects as pe
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
def _guardar(fig, ruta: Path | None):
    if ruta is not None:
        fig.savefig(ruta, dpi=150, bbox_inches="tight")
        plt.close(fig)
    return fig


def _leyenda_arriba(ax, casos):
    """Leyenda horizontal colocada encima del area del grafico."""
    ax.legend(handles=casos, frameon=False, fontsize=12.5,
              loc="lower center", bbox_to_anchor=(0.5, 1.005), ncol=2)


# --------------------------------- graficos (revolico)

def figura_precios(ruta: Path | None = None):
    """Barras verticales: precio promedio de cada categoria, con la mediana marcada."""
    resumen = resumen_precios()

    nombres = [ETIQUETAS[c] for c in ORDEN]
    promedios = [resumen[c]["promedio"] for c in ORDEN]
    medianas = [resumen[c]["mediana"] for c in ORDEN]

    fig, ax = plt.subplots(figsize=(11, 7))
    posiciones = list(range(len(nombres)))
    ancho = 0.55
    medio = ancho / 2

    ax.bar(posiciones, promedios, ancho,
           color=[COLORES[c] for c in ORDEN], edgecolor="white", linewidth=2, zorder=2)

    # marca de la mediana: linea negra que sobresale de la barra, con borde blanco
    for p, mediana in zip(posiciones, medianas):
        ax.plot([p - medio - 0.11, p + medio + 0.11], [mediana, mediana],
                color="#111111", linewidth=4.5, zorder=4, solid_capstyle="butt",
                path_effects=[pe.withStroke(linewidth=8, foreground="white")])
        for extremo in (p - medio - 0.11, p + medio + 0.11):
            ax.plot([extremo, extremo], [mediana - 30, mediana + 30],
                    color="#111111", linewidth=4.5, zorder=4,
                    path_effects=[pe.withStroke(linewidth=8, foreground="white")])

    for p, categoria in zip(posiciones, ORDEN):
        r = resumen[categoria]
        ax.text(p, r["promedio"] + 235, f"promedio  {r['promedio']:,.0f}".replace(",", "."),
                ha="center", fontsize=13.5, fontweight="bold", color="#111111")
        ax.text(p, r["promedio"] + 95, f"mediana  {r['mediana']:,.0f}".replace(",", "."),
                ha="center", fontsize=13, fontweight="bold", color="#111111")

    ax.set_xticks(posiciones)
    ax.set_xticklabels(
        [f"{n}\n{r['anuncios']} anuncios" for n, r in zip(nombres, [resumen[c] for c in ORDEN])],
        fontsize=12.5)
    ax.set_ylabel("Precio (USD)", fontsize=12.5)
    ax.set_ylim(0, 3300)
    ax.tick_params(axis="y", labelsize=11.5)
    ax.set_title("Precio de las categorías de vehículos eléctricos en La Habana",
                 fontsize=16, fontweight="bold", pad=42)

    # leyenda general: barra = promedio, linea negra = mediana
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    _leyenda_arriba(ax, [
        Patch(facecolor="#6B7280", edgecolor="white", label="Barra: precio promedio"),
        Line2D([0], [0], color="#111111", linewidth=4.5,
               path_effects=[pe.withStroke(linewidth=8, foreground="white")],
               label="Línea negra: precio más común (mediana)"),
    ])

    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linestyle=":", alpha=0.4, zorder=0)
    fig.tight_layout()
    return _guardar(fig, ruta)


def figura_disponibilidad(ruta: Path | None = None):
    """Barras horizontales: cuantos anuncios puede comprar Lucy en cada categoria."""
    resumen = resumen_presupuesto()

    nombres = [ETIQUETAS[c] for c in ORDEN]
    alcanzables = [resumen[c]["alcanzables"] for c in ORDEN]
    totales = [resumen[c]["anuncios"] for c in ORDEN]
    posiciones = list(range(len(nombres)))

    fig, ax = plt.subplots(figsize=(11, 5.6))

    ax.barh(posiciones, alcanzables, 0.55,
            color=[COLORES[c] for c in ORDEN], edgecolor="white", linewidth=2, zorder=3)
    ax.barh(posiciones, totales, 0.55,
            color="white", edgecolor="#9CA3AF", linewidth=2, hatch="///", zorder=2)

    for p, (n_alcanzable, n_total) in enumerate(zip(alcanzables, totales)):
        ax.text(n_alcanzable + 2.5, p, f"{n_alcanzable} de {n_total} anuncios",
                va="center", fontsize=13, fontweight="bold")

    ax.set_yticks(posiciones)
    ax.set_yticklabels(nombres, fontsize=13)
    ax.set_xlabel("Número de anuncios", fontsize=12.5)
    ax.set_xlim(0, max(totales) * 1.28)
    ax.tick_params(axis="x", labelsize=11.5)
    ax.set_title(f"Anuncios al alcance de un presupuesto de {PRESUPUESTO_LUCY} USD",
                 fontsize=16, fontweight="bold", pad=44)

    from matplotlib.patches import Patch
    _leyenda_arriba(ax, [
        Patch(facecolor="#6B7280", edgecolor="white", label="Barra sólida: anuncios que puede comprar"),
        Patch(facecolor="white", edgecolor="#9CA3AF", hatch="///",
              label="Barra rayada: anuncios publicados en total"),
    ])

    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", linestyle=":", alpha=0.4, zorder=0)
    fig.tight_layout()
    return _guardar(fig, ruta)


def figura_autonomia_alcanzable(ruta: Path | None = None):
    """Barras horizontales con rango: autonomia que se compra dentro del presupuesto."""
    resumen = resumen_presupuesto()

    nombres = [ETIQUETAS[c] for c in ORDEN]
    minimos = [resumen[c]["autonomia_min"] or 0 for c in ORDEN]
    medianas = [resumen[c]["autonomia_mediana"] or 0 for c in ORDEN]
    maximos = [resumen[c]["autonomia_max"] or 0 for c in ORDEN]
    posiciones = list(range(len(nombres)))

    fig, ax = plt.subplots(figsize=(11, 5.6))

    for p, categoria, vmin, vmed, vmax in zip(
            posiciones, ORDEN, minimos, medianas, maximos):
        color = COLORES[categoria]
        # rango completo: del minimo al maximo
        ax.barh(p, vmax - vmin, 0.42, left=vmin,
                color=color, alpha=0.32, edgecolor=color, linewidth=1.6, zorder=2)
        # barra desde cero hasta la mediana
        ax.barh(p, vmed, 0.42, color=color, edgecolor="white", linewidth=2, zorder=3)
        # marca de la mediana
        ax.plot([vmed, vmed], [p - 0.29, p + 0.29], color="white", linewidth=4, zorder=4)

        ax.text(vmax + 3, p, f"{vmin:.0f} – {vmax:.0f} km", va="center",
                fontsize=12, fontweight="bold", color=color)
        ax.text(vmed / 2, p, f"{vmed:.0f} km", va="center", ha="center",
                fontsize=13, fontweight="bold", color="white", zorder=5)

    ax.set_yticks(posiciones)
    ax.set_yticklabels(nombres, fontsize=13)
    ax.set_xlabel("Autonomía (km)", fontsize=12.5)
    ax.set_xlim(0, max(maximos) * 1.32)
    ax.set_ylim(-0.6, len(ORDEN) - 0.4)
    ax.tick_params(axis="x", labelsize=11.5)
    ax.set_title(f"Autonomía disponible dentro del presupuesto de {PRESUPUESTO_LUCY} USD",
                 fontsize=16, fontweight="bold", pad=44)

    from matplotlib.patches import Patch
    _leyenda_arriba(ax, [
        Patch(facecolor="#6B7280", edgecolor="white",
              label="Barra clara: autonomía más común (mediana)"),
        Patch(facecolor="#6B7280", edgecolor="#6B7280", alpha=0.32,
              label="Barra translúcida: rango entre el mínimo y el máximo"),
    ])

    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", linestyle=":", alpha=0.4, zorder=0)
    fig.tight_layout()
    return _guardar(fig, ruta)


def ejecutar():
    """Genera y guarda todos los graficos del proyecto."""
    CARPETA_GRAFICOS.mkdir(exist_ok=True)
    figura_precios(CARPETA_GRAFICOS / "precios_categoria.png")
    figura_disponibilidad(CARPETA_GRAFICOS / "alcance_presupuesto.png")
    figura_autonomia_alcanzable(CARPETA_GRAFICOS / "autonomia_alcanzable.png")
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
