# -*- coding: utf-8 -*-
"""ANALISIS.PY — todo el codigo del proyecto de vehiculos electricos en Cuba.

Este es el UNICO archivo de codigo del proyecto. Aqi dentro se va metiendo todo,
organizado por secciones:

    CONFIGURACION GENERAL     constantes, colores, etiquetas, sitios
    UTILIDADES               formato de numeros y tablas de markdown
    PRIMERA FUENTE: INTERNET  los dos sitios (Revolico e iTENCEL):
                             tabla de resumen y tres graficos. VEDCA y
                             CubAmerica quedaron fuera de internet para
                             usarse luego como mercado aparte.
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
        "slug": "itencel",
        "nombre": "iTENCEL",
        "archivo": "itencel_anuncios.json",
        "lista": "productos",
        "precio": "precio_usd",
        "autonomia": "autonomia_max_km",
        "moneda": "mayoría en USD",
    },
)

# Sitios que se guardaron pero quedaron fuera de la primera fuente (mercados):
#   - VEDCA (Islagrande): 10 productos en data/vedca_islagrande.json
#   - CubAmerica:         43 productos en data/cubamerica_envios.json

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
# PRIMERA FUENTE: INTERNET  (los dos sitios)
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


def _leyenda_arriba(ax, casos, handler_map=None):
    """Leyenda horizontal colocada encima del area del grafico."""
    ax.legend(handles=casos, frameon=False, fontsize=11.5,
              loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=4,
              handler_map=handler_map)


class _SegmentoLegendario:
    """Marcador de leyenda que dibuja un segmento: linea horizontal con dos
    barras verticales cortas en los extremos (rango minima-maximo)."""

    def legend_artist(self, legend, orig_handle, fontsize, handlebox):
        import matplotlib.lines as mlines

        x0, y0 = handlebox.xdescent, handlebox.ydescent
        ancho, alto = handlebox.width, handlebox.height
        color = orig_handle.get_color()
        grosor = orig_handle.get_linewidth()

        centro_y = y0 + alto / 2
        margen = ancho * 0.06
        linea = mlines.Line2D([x0 + margen, x0 + ancho - margen],
                              [centro_y, centro_y],
                              color=color, linewidth=grosor, zorder=3)
        barra = mlines.Line2D([x0 + margen, x0 + margen],
                              [centro_y - alto * 0.4, centro_y + alto * 0.4],
                              color=color, linewidth=grosor, zorder=3)
        barra2 = mlines.Line2D([x0 + ancho - margen, x0 + ancho - margen],
                               [centro_y - alto * 0.4, centro_y + alto * 0.4],
                               color=color, linewidth=grosor, zorder=3)
        handlebox.add_artist(linea)
        handlebox.add_artist(barra)
        handlebox.add_artist(barra2)
        handlebox.set_clip_on(False)
        return [linea, barra, barra2]


def figura_precios_promedio(ruta: Path | None = None):
    """G1. Barras agrupadas: precio promedio por tipo, un grupo por sitio."""
    from matplotlib.patches import Patch

    tipos = orden_con_productos()
    x = list(range(len(tipos)))
    ancho = 0.35
    maximo = 0

    fig, ax = plt.subplots(figsize=(11.5, 6.4))
    for i, sitio in enumerate(SITIOS):
        rp = resumen_precios(sitio)
        valores = [rp[c].get("promedio") if rp[c].get("anuncios") else None
                   for c in tipos]
        maximo = max([maximo] + [v for v in valores if v is not None] or [0])
        corrimiento = (i - (len(SITIOS) - 1) / 2) * ancho
        centros = [xi + corrimiento for xi in x]
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
    ax.set_title("Precio promedio por tipo de vehículo en los dos sitios",
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
    """G2. Barras horizontales agrupadas por tipo: cuantos productos de cada
    sitio y categoria entran en el presupuesto frente al total publicado."""
    from matplotlib.patches import Patch

    PALETA_2 = {
        "revolico": "#4C6EF5",
        "itencel": "#F4955A",
    }

    tipos = orden_con_productos()
    y = list(range(len(tipos)))
    alto = 0.35
    maximo = 0

    filas = {s["slug"]: resumen_presupuesto(s) for s in SITIOS}
    for c in tipos:
        for s in SITIOS:
            maximo = max(maximo, filas[s["slug"]][c]["anuncios"])

    fig, ax = plt.subplots(figsize=(11.5, 5.6))
    for i, sitio in enumerate(SITIOS):
        rp = filas[sitio["slug"]]
        totales = [rp[c]["anuncios"] for c in tipos]
        alcanzables = [rp[c]["alcanzables"] for c in tipos]
        corrimiento = (i - (len(SITIOS) - 1) / 2) * alto
        centros = [yi + corrimiento for yi in y]
        ax.barh(centros, totales, alto,
                color="white", edgecolor="#B9C0C9", linewidth=2, hatch="///", zorder=2)
        ax.barh(centros, alcanzables, alto,
                color=PALETA_2[sitio["slug"]],
                edgecolor="white", linewidth=2, zorder=3)
        for cc, t, a in zip(centros, totales, alcanzables):
            ax.text(t + maximo * 0.02, cc, f"{a} de {t}",
                    va="center", fontsize=10.5, fontweight="bold")

    ax.set_yticks(y)
    ax.set_yticklabels([ETIQUETAS[c] for c in tipos], fontsize=12.5)
    ax.set_xlabel("Número de productos", fontsize=12.5)
    ax.set_xlim(0, maximo * 1.25)
    ax.tick_params(axis="x", labelsize=11)
    ax.set_title(f"Productos que caben en el presupuesto de {PRESUPUESTO_LUCY} USD, "
                 "por tipo de vehículo y sitio", fontsize=16, fontweight="bold", pad=44)

    _leyenda_arriba(ax, [
        Patch(facecolor=PALETA_2[s["slug"]], edgecolor="white",
              label=f"{s['nombre']} (cabe en el presupuesto)") for s in SITIOS
    ] + [
        Patch(facecolor="white", edgecolor="#B9C0C9", hatch="///",
              label="Total publicado"),
    ])

    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", linestyle=":", alpha=0.4, zorder=0)
    fig.tight_layout()
    return _guardar(fig, ruta)


def figura_alcance_general(ruta: Path | None = None):
    """G3. Dot plot / range plot: por sitio, rango de autonomia alcanzable
    (linea del minimo al maximo) con el promedio marcado como punto rojo."""
    from matplotlib.lines import Line2D

    filas = resumen_alcance_general()
    nombres = [f["nombre"] for f in filas]
    minimos = [f["autonomia_min"] or 0 for f in filas]
    promedios = [f["autonomia_promedio"] or 0 for f in filas]
    maximos = [f["autonomia_max"] or 0 for f in filas]
    alcanzables = [f["alcanzables"] for f in filas]
    totales = [f["total"] for f in filas]
    posiciones = list(range(len(nombres)))
    tope = max(maximos) if max(maximos) else 1

    fig, ax = plt.subplots(figsize=(11.5, 4.8))
    for p, vmin, vmed, vmax in zip(
            posiciones, minimos, promedios, maximos):
        ax.plot([vmin, vmax], [p, p], color="#4B5563", linewidth=3,
                solid_capstyle="round", zorder=2)
        ax.plot([vmin, vmin], [p - 0.25, p + 0.25], color="#4B5563",
                linewidth=3, zorder=3)
        ax.plot([vmax, vmax], [p - 0.25, p + 0.25], color="#4B5563",
                linewidth=3, zorder=3)
        ax.plot([vmed], [p], linestyle="none", marker="o", color="#E63946",
                markersize=17, markeredgecolor="white", markeredgewidth=2, zorder=4)
        ax.text(vmin, p + 0.34, f"{vmin:.0f}", ha="center", va="bottom",
                fontsize=11, color="#4B5563", fontweight="bold")
        ax.text(vmax, p + 0.34, f"{vmax:.0f}", ha="center", va="bottom",
                fontsize=11, color="#4B5563", fontweight="bold")
        ax.text(vmed, p - 0.34, f"promedio {vmed:.0f} km", ha="center", va="top",
                fontsize=11.5, fontweight="bold", color="#B1121C")

    ax.set_yticks(posiciones)
    ax.set_yticklabels(
        [f"{nombre}  ({n_dentro} de {n_total})"
         for nombre, n_dentro, n_total in zip(nombres, alcanzables, totales)],
        fontsize=13)
    ax.set_xlabel("Autonomía (km)", fontsize=12.5)
    ax.set_xlim(0, tope * 1.18)
    ax.set_ylim(-0.7, len(nombres) - 0.3)
    ax.tick_params(axis="x", labelsize=11.5)
    ax.set_title("Hasta dónde llega Lucy con su presupuesto de "
                 f"{PRESUPUESTO_LUCY} USD en cada sitio (autonomía alcanzable)",
                 fontsize=16, fontweight="bold", pad=44)

    seg_rango = Line2D([0, 1], [0, 0], color="#4B5563", linewidth=3,
                       label="Rango de autonomía (mín – máx, con marcas de extremo)")
    _leyenda_arriba(
        ax,
        [seg_rango,
         Line2D([0], [0], color="none", marker="o", markerfacecolor="#E63946",
                markeredgecolor="white", markersize=14,
                label="Promedio de lo que cabe en el presupuesto")],
        handler_map={seg_rango: _SegmentoLegendario()})

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
    print("TABLA DE RESUMEN DE LOS DOS SITIOS")
    print(tabla_resumen_markdown())