# -*- coding: utf-8 -*-
"""ANALISIS.PY — todo el codigo del proyecto de vehiculos electricos en Cuba.

Este es el UNICO archivo de codigo del proyecto. Aqi dentro se va metiendo todo,
organizado por secciones:

    CONFIGURACION GENERAL     constantes, colores, etiquetas, sitios
    UTILIDADES               formato de numeros y tablas de markdown
    PRIMERA FUENTE: INTERNET  los tres sitios (Revolico, CubAmerica, iTENCEL):
                             tabla de resumen y tres graficos. VEDCA quedó fuera
                             de internet para usarse luego como mercado aparte.
    OTRAS FUENTES            Telegram, encuestas, mercados (mas adelante)

El notebook `proyecto.ipynb` NO tiene codigo: solo importa desde aqui y muestra
los resultados.

Uso desde el notebook:

    from analisis import *

    print(tabla_resumen_markdown())
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

# Cada sitio de la primera fuente: donde viven sus datos y que campos usar.
SITIOS = (
    {
        "slug": "revolico",
        "nombre": "Revolico",
        "archivo": "anuncios_revolico.json",
        "lista": "anuncios",
        "precio": "precio",
        "autonomia": "autonomia_km",
        "moneda": "CUP a USD (745 = 1)",
    },
    {
        "slug": "cubamerica",
        "nombre": "CubAmerica",
        "archivo": "cubamerica_envios.json",
        "lista": "productos",
        "precio": "precio_usd",
        "autonomia": "autonomia_max_km",
        "moneda": "USD",
    },
    {
        "slug": "itencel",
        "nombre": "iTENCEL",
        "archivo": "itencel_anuncios.json",
        "lista": "productos",
        "precio": "precio_usd",
        "autonomia": "autonomia_max_km",
        "moneda": "mayoría en USD",
    },
)

DICC_SITIOS = {s["slug"]: s for s in SITIOS}

# Color por sitio, usado en los tres graficos.
COLOR_SITIOS = {
    "revolico": "#E63946",
    "vedca": "#1D6FE0",
    "cubamerica": "#10B981",
    "itencel": "#F9A602",
}
COLOR_FUERA = "#C9CDD2"
COLOR_PRESUPUESTO = "#E63946"


# ==============================================================================
# UTILIDADES
# ==============================================================================

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


# ==============================================================================
# PRIMERA FUENTE: INTERNET  (los tres sitios)
# ==============================================================================

def cargar_sitio(sitio: dict) -> list[dict]:
    """Devuelve la lista de productos del sitio indicado."""
    ruta = RAIZ / "data" / sitio["archivo"]
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)[sitio["lista"]]


def _precio(sitio, producto):
    return producto[sitio["precio"]]


def _autonomia(sitio, producto):
    return producto[sitio["autonomia"]]


def grupo_de(sitio: dict, categoria: str,
             productos: list[dict] | None = None) -> list[dict]:
    """Productos de un sitio que pertenecen a una categoria."""
    productos = cargar_sitio(sitio) if productos is None else productos
    return [p for p in productos if p["tipo_vehiculo"] == categoria]


def alcanzables_de(sitio: dict, categoria: str,
                   productos: list[dict] | None = None) -> list[dict]:
    """Productos del sitio que caben en el presupuesto de Lucy."""
    return [p for p in grupo_de(sitio, categoria, productos)
            if _precio(sitio, p) <= PRESUPUESTO_LUCY]


# --------------------------------- calculos estadisticos

def resumen_precios(sitio: dict) -> dict[str, dict]:
    """Promedio, mediana, minimo y maximo del precio por categoria."""
    productos = cargar_sitio(sitio)
    resumen = {}
    for categoria in ORDEN:
        precios = [_precio(sitio, p) for p in grupo_de(sitio, categoria, productos)]
        if not precios:
            resumen[categoria] = {"anuncios": 0}
            continue
        resumen[categoria] = {
            "anuncios": len(precios),
            "promedio": stat.mean(precios),
            "mediana": stat.median(precios),
            "minimo": min(precios),
            "maximo": max(precios),
        }
    return resumen


def resumen_presupuesto(sitio: dict) -> dict[str, dict]:
    """Que puede comprar Lucy con su presupuesto en este sitio, por categoria."""
    productos = cargar_sitio(sitio)
    resumen = {}
    for categoria in ORDEN:
        todos = grupo_de(sitio, categoria, productos)
        dentro = alcanzables_de(sitio, categoria, productos)
        fila = {"anuncios": len(todos), "alcanzables": len(dentro)}
        if dentro:
            precios = sorted(_precio(sitio, p) for p in dentro)
            autonomias = sorted(int(_autonomia(sitio, p)) for p in dentro)
            fila.update({
                "precio_min": min(precios),
                "precio_mediana": stat.median(precios),
                "precio_max": max(precios),
                "autonomia_min": min(autonomias),
                "autonomia_mediana": stat.median(autonomias),
                "autonomia_max": max(autonomias),
            })
        else:
            fila.update({k: None for k in (
                "precio_min", "precio_mediana", "precio_max",
                "autonomia_min", "autonomia_mediana", "autonomia_max")})
        resumen[categoria] = fila
    return resumen


def resumen_alcance_general() -> list[dict]:
    """Por sitio: productos dentro del presupuesto y la autonomia del conjunto."""
    filas = []
    for sitio in SITIOS:
        dentro = [p for p in cargar_sitio(sitio)
                  if _precio(sitio, p) <= PRESUPUESTO_LUCY]
        autonomias = sorted(int(_autonomia(sitio, p)) for p in dentro)
        fila = {
            "slug": sitio["slug"],
            "nombre": sitio["nombre"],
            "total": len(cargar_sitio(sitio)),
            "alcanzables": len(dentro),
        }
        if dentro:
            fila.update({
                "autonomia_min": autonomias[0],
                "autonomia_promedio": stat.mean(autonomias),
                "autonomia_mediana": stat.median(autonomias),
                "autonomia_max": autonomias[-1],
            })
        else:
            fila.update({"autonomia_min": None, "autonomia_promedio": None,
                         "autonomia_mediana": None, "autonomia_max": None})
        filas.append(fila)
    return filas


# --------------------------------- tabla de resumen (la unica del cuaderno)

def tabla_resumen_markdown() -> str:
    """Una sola tabla con lo esencial: promedio por tipo, lo que cabe en el
    presupuesto y la autonomia alcanzable de cada sitio."""
    alcance = {f["slug"]: f for f in resumen_alcance_general()}
    filas = []
    for sitio in SITIOS:
        rp = resumen_precios(sitio)
        al = alcance[sitio["slug"]]
        filas.append([
            sitio["nombre"],
            str(al["total"]),
            f"**{al['alcanzables']}**",
            _formato(rp["Moto electrica"].get("promedio")),
            _formato(rp["Bicicleta electrica"].get("promedio")),
            _formato(rp["Patinete electrico"].get("promedio")),
            _formato(al["autonomia_promedio"]),
            _formato(al["autonomia_max"]),
        ])
    return tabla_markdown(
        ["Sitio", "Productos", "Caben en 1.500 USD", "Moto (prom. USD)",
         "Bicicleta (prom. USD)", "Patinete (prom. USD)",
         "Autonomía promedio alcanzable (km)", "Autonomía máxima alcanzable (km)"],
        filas,
    )


# --------------------------------- graficos

def _guardar(fig, ruta: Path | None):
    if ruta is not None:
        fig.savefig(ruta, dpi=150, bbox_inches="tight")
        plt.close(fig)
    return fig


def _leyenda_arriba(ax, casos):
    """Leyenda horizontal colocada encima del area del grafico."""
    ax.legend(handles=casos, frameon=False, fontsize=11.5,
              loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=4)


def figura_precios_promedio(ruta: Path | None = None):
    """G1. Barras agrupadas: precio promedio por tipo, un grupo por sitio."""
    from matplotlib.patches import Patch

    tipos = orden_con_productos()
    x = list(range(len(tipos)))
    ancho = 0.2
    maximo = 0

    fig, ax = plt.subplots(figsize=(11.5, 6.4))
    for i, sitio in enumerate(SITIOS):
        rp = resumen_precios(sitio)
        valores = [rp[c].get("promedio") if rp[c].get("anuncios") else None
                   for c in tipos]
        maximo = max([maximo] + [v for v in valores if v is not None] or [0])
        centros = [xi + (i - 1.5) * ancho for xi in x]
        presentes = [(xx, v) for xx, v in zip(centros, valores) if v is not None]
        if not presentes:
            continue
        ax.bar([xx for xx, _ in presentes], [v for _, v in presentes],
               ancho, color=COLOR_SITIOS[sitio["slug"]],
               edgecolor="white", linewidth=1.6, zorder=3)
        for xx, v in presentes:
            ax.text(xx, v + 55, f"{v:,.0f}".replace(",", "."),
                    ha="center", fontsize=9.5, color="#111111")

    ax.set_xticks(x)
    ax.set_xticklabels([ETIQUETAS[c] for c in tipos], fontsize=12.5)
    ax.set_ylabel("Precio promedio (USD)", fontsize=12.5)
    ax.set_ylim(0, maximo * 1.18)
    ax.tick_params(axis="y", labelsize=11)
    ax.set_title("Precio promedio por tipo de vehículo en los tres sitios",
                 fontsize=16, fontweight="bold", pad=40)

    _leyenda_arriba(ax, [
        Patch(facecolor=COLOR_SITIOS[s["slug"]], edgecolor="white",
              label=s["nombre"]) for s in SITIOS
    ])

    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linestyle=":", alpha=0.4, zorder=0)
    fig.tight_layout()
    return _guardar(fig, ruta)


def figura_disponibilidad(ruta: Path | None = None):
    """G2. Barras horizontales: lo que cabe en el presupuesto frente al total."""
    from matplotlib.patches import Patch

    filas = resumen_alcance_general()
    nombres = [f["nombre"] for f in filas]
    totales = [f["total"] for f in filas]
    alcanzables = [f["alcanzables"] for f in filas]
    posiciones = list(range(len(nombres)))

    fig, ax = plt.subplots(figsize=(11, 5.4))
    ax.barh(posiciones, totales, 0.55,
            color="white", edgecolor="#9CA3AF", linewidth=2, hatch="///", zorder=2)
    ax.barh(posiciones, alcanzables, 0.55,
            color=[COLOR_SITIOS[f["slug"]] for f in filas],
            edgecolor="white", linewidth=2, zorder=3)

    for p, n_dentro, n_total in zip(posiciones, alcanzables, totales):
        ax.text(n_dentro + (max(totales) * 0.02), p,
                f"{n_dentro} de {n_total}", va="center", fontsize=13,
                fontweight="bold")

    ax.set_yticks(posiciones)
    ax.set_yticklabels(nombres, fontsize=13)
    ax.set_xlabel("Número de productos", fontsize=12.5)
    ax.set_xlim(0, max(totales) * 1.28)
    ax.tick_params(axis="x", labelsize=11.5)
    ax.set_title(f"Productos que caben en el presupuesto de {PRESUPUESTO_LUCY} USD "
                 "en cada sitio", fontsize=16, fontweight="bold", pad=44)

    _leyenda_arriba(ax, [
        Patch(facecolor="#6B7280", edgecolor="white",
              label="Barra sólida: productos dentro del presupuesto"),
        Patch(facecolor="white", edgecolor="#9CA3AF", hatch="///",
              label="Barra rayada: productos publicados en total"),
    ])

    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", linestyle=":", alpha=0.4, zorder=0)
    fig.tight_layout()
    return _guardar(fig, ruta)


def figura_alcance_general(ruta: Path | None = None):
    """G3. Barras por sitio: autonomia alcanzable y su promedio con el presupuesto."""
    from matplotlib.patches import Patch

    filas = resumen_alcance_general()
    nombres = [f["nombre"] for f in filas]
    minimos = [f["autonomia_min"] or 0 for f in filas]
    promedios = [f["autonomia_promedio"] or 0 for f in filas]
    maximos = [f["autonomia_max"] or 0 for f in filas]
    alcanzables = [f["alcanzables"] for f in filas]
    totales = [f["total"] for f in filas]
    posiciones = list(range(len(nombres)))

    fig, ax = plt.subplots(figsize=(11, 5.6))
    for p, slug, vmin, vmed, vmax, n_dentro, n_total in zip(
            posiciones, [f["slug"] for f in filas], minimos, promedios, maximos,
            alcanzables, totales):
        color = COLOR_SITIOS[slug]
        if n_dentro == 0:
            ax.text(3, p, "sin productos dentro del presupuesto", va="center",
                    fontsize=12.5, color="#6B7280")
            continue
        ax.barh(p, vmax - vmin, 0.42, left=vmin,
                color=color, alpha=0.32, edgecolor=color, linewidth=1.6, zorder=2)
        ax.barh(p, vmed, 0.42, color=color, edgecolor="white", linewidth=2, zorder=3)
        ax.plot([vmed, vmed], [p - 0.29, p + 0.29], color="white", linewidth=4,
                zorder=4, alpha=0.85)
        ax.text(vmax + 3, p, f"{vmin:.0f} – {vmax:.0f} km", va="center",
                fontsize=12, fontweight="bold", color=color)
        ax.text(vmed / 2, p, f"promedio {vmed:.0f} km", va="center", ha="center",
                fontsize=12.5, fontweight="bold", color="white", zorder=5)

    ax.set_yticks(posiciones)
    ax.set_yticklabels(
        [f"{nombre} ({n_dentro} de {n_total})"
         for nombre, n_dentro, n_total in zip(nombres, alcanzables, totales)],
        fontsize=13)
    ax.set_xlabel("Autonomía (km)", fontsize=12.5)
    ax.set_xlim(0, max(maximos) * 1.32 if max(maximos) else 1)
    ax.set_ylim(-0.6, len(nombres) - 0.4)
    ax.tick_params(axis="x", labelsize=11.5)
    ax.set_title("Hasta dónde llega Lucy con su presupuesto de "
                 f"{PRESUPUESTO_LUCY} USD en cada sitio (autonomía alcanzable)",
                 fontsize=16, fontweight="bold", pad=52)

    _leyenda_arriba(ax, [
        Patch(facecolor="#6B7280", edgecolor="white",
              label="Barra sólida: autonomía promedio de lo que entra en el presupuesto"),
        Patch(facecolor="#6B7280", edgecolor="#6B7280", alpha=0.32,
              label="Barra translúcida: rango entre el mínimo y el máximo"),
    ])

    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", linestyle=":", alpha=0.4, zorder=0)
    fig.tight_layout()
    return _guardar(fig, ruta)


def orden_con_productos() -> list[str]:
    """Tipos que aparecen en al menos un sitio."""
    con_datos = []
    for c in ORDEN:
        for sitio in SITIOS:
            rp = resumen_precios(sitio)
            if rp[c].get("anuncios"):
                con_datos.append(c)
                break
    return con_datos


def ejecutar():
    """Genera y guarda los tres graficos de la primera fuente (INTERNET)."""
    CARPETA_GRAFICOS.mkdir(exist_ok=True)
    figura_precios_promedio(CARPETA_GRAFICOS / "precios_promedio_sitios.png")
    figura_disponibilidad(CARPETA_GRAFICOS / "disponibilidad_presupuesto.png")
    figura_alcance_general(CARPETA_GRAFICOS / "autonomia_alcance_sitios.png")
    return CARPETA_GRAFICOS


# ==============================================================================
# OTRAS FUENTES
#   Telegram, encuestas a personas y mercados de vehiculos electricos.
#   VEDCA (Islagrande) quedo fuera de la primera fuente y se usara mas
#   adelante como un mercado aparte.
#   Aqui se van anadiendo sus datos y sus analisis, en el mismo archivo.
# ==============================================================================


if __name__ == "__main__":
    destino = ejecutar()
    print("Gráficos guardados en:", destino)
    print()
    print("TABLA DE RESUMEN DE LOS TRES SITIOS")
    print(tabla_resumen_markdown())