# -*- coding: utf-8 -*-
"""ANALISIS.PY — todo el codigo del proyecto de vehiculos electricos en Cuba.

Este es el UNICO archivo de codigo del proyecto. Aqi dentro se va metiendo todo,
organizado por secciones:

    CONFIGURACION GENERAL     constantes, colores, etiquetas, sitios
    UTILIDADES               formato de numeros y tablas de markdown
    PRIMERA FUENTE: INTERNET  los dos sitios (Revolico e iTENCEL):
                             tabla de resumen y tres graficos.
    SEGUNDA FUENTE: MERCADO   las dos tiendas (VEDCA e CubAmerica):
                             disponibilidad/precios y autonomia por tipo
                             de vehiculo frente al presupuesto (mapa de calor).
    TERCERA FUENTE: ENCUESTAS  personas que ya tienen un vehiculo electrico:
                              precio, uso, degradacion de la autonomia y
                              calidad real segun sus dueños.
    OTRAS FUENTES            Telegram (mas adelante)

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
import re
import statistics as stat
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

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

# SEGUNDA FUENTE: MERCADO. Dos tiendas de importacion con la misma forma de
# datos que los sitios de internet (productos con precio_usd y autonomia).
MERCADOS = (
    {
        "slug": "vedca",
        "nombre": "VEDCA (Islagrande)",
        "archivo": "vedca_islagrande.json",
        "lista": "productos",
        "precio": "precio_usd",
        "autonomia": "autonomia_max_km",
        "moneda": "EUR convertido a USD (1,13)",
    },
    {
        "slug": "cubamerica",
        "nombre": "CubAmerica (envíos)",
        "archivo": "cubamerica_envios.json",
        "lista": "productos",
        "precio": "precio_usd",
        "autonomia": "autonomia_max_km",
        "moneda": "USD",
    },
)

DICC_MERCADOS = {m["slug"]: m for m in MERCADOS}

# TERCERA FUENTE: ENCUESTAS. Personas que ya tienen un vehiculo electrico y
# cuentan su experiencia (precio, uso y calidad real).
ARCHIVO_ENCUESTAS = "encuestas_personas.json"
ORDEN_CALIDAD = ["Buena", "Regular", "Mala"]

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


def resumen_alcance_general(sitios=SITIOS) -> list[dict]:
    """Por sitio: productos dentro del presupuesto y la autonomia del conjunto."""
    filas = []
    for sitio in sitios:
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

def tabla_resumen_markdown(sitios=SITIOS) -> str:
    """Una sola tabla con lo esencial: promedio por tipo, lo que cabe en el
    presupuesto y la autonomia alcanzable de cada sitio."""
    alcance = {f["slug"]: f for f in resumen_alcance_general(sitios)}
    filas = []
    for sitio in sitios:
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


def _leyenda_arriba(ax, casos, handler_map=None, ncol=4):
    """Leyenda horizontal colocada encima del area del grafico."""
    ax.legend(handles=casos, frameon=False, fontsize=11.5,
              loc="lower center", bbox_to_anchor=(0.5, 1.01), ncol=ncol,
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


def orden_con_productos(sitios=SITIOS) -> list[str]:
    """Tipos que aparecen en al menos un sitio."""
    con_datos = []
    for c in ORDEN:
        for sitio in sitios:
            rp = resumen_precios(sitio)
            if rp[c].get("anuncios"):
                con_datos.append(c)
                break
    return con_datos


# ==============================================================================
# SEGUNDA FUENTE: MERCADO  (VEDCA e CubAmerica)
#   Bloque A: disponibilidad y precios de cada tienda.
#   Bloque B: autonomia por tipo de vehiculo y presupuesto, por mercado
#             (mapa de calor en dos paneles) y la mejor opcion de cada tipo.
# ==============================================================================

def _bateria_datos(texto: str | None) -> dict:
    """Separa lo que se pueda del texto libre de la bateria:
    voltaje (V), capacidad (Ah), energia (Wh) y quimica."""
    t = (texto or "").lower()
    voltaje = capacidad = energia = None
    quimica = None
    coincidencia_v = re.search(r"(\d+)\s*v\b", t)
    if coincidencia_v:
        voltaje = int(coincidencia_v.group(1))
    coincidencia_ah = re.search(r"(\d+)\s*ah\b", t)
    if coincidencia_ah:
        capacidad = int(coincidencia_ah.group(1))
    if voltaje and capacidad:
        energia = voltaje * capacidad
    if "lifepo4" in t or "lifep04" in t:
        quimica = "LiFePO4"
    elif "lead" in t or "plomo" in t or "ácido" in t or "acido" in t:
        quimica = "Plomo-ácido"
    elif "litio" in t or "lithium" in t:
        quimica = "Litio"
    return {"voltaje": voltaje, "capacidad_ah": capacidad,
            "energia_wh": energia, "quimica": quimica}


def productos_mercado() -> list[dict]:
    """Todos los productos de las tiendas de mercado, con su tienda de origen."""
    productos = []
    for mercado in MERCADOS:
        for p in cargar_sitio(mercado):
            productos.append({**p, "tienda": mercado["nombre"],
                              "tienda_slug": mercado["slug"]})
    return productos


def tabla_resumen_mercado() -> str:
    """Bloque A. Tabla de las tiendas de mercado (mismo formato que INTERNET)."""
    return tabla_resumen_markdown(MERCADOS).replace("Sitio", "Tienda", 1)


def resumen_marcas() -> list[dict]:
    """Bloque B. Por marca: cuantos productos, cuantos caben en el presupuesto,
    autonomia, precio, costo por km y bateria. Ordenado de mejor a peor
    relacion calidad-precio (menor USD por km)."""
    por_marca: dict[str, dict] = {}
    for p in productos_mercado():
        marca = p.get("marca") or "Sin marca"
        dato = por_marca.setdefault(marca, {
            "marca": marca, "n": 0, "dentro": 0,
            "precios": [], "autonomias": [], "usd_km": [],
            "voltajes": [], "capacidades": [], "energias": [], "quimicas": [],
        })
        precio = p["precio_usd"]
        autonomia = p["autonomia_max_km"]
        dato["n"] += 1
        dato["precios"].append(precio)
        dato["autonomias"].append(autonomia)
        if autonomia:
            dato["usd_km"].append(precio / autonomia)
        if precio <= PRESUPUESTO_LUCY:
            dato["dentro"] += 1
        bateria = _bateria_datos(p.get("bateria"))
        if bateria["voltaje"]:
            dato["voltajes"].append(bateria["voltaje"])
        if bateria["capacidad_ah"]:
            dato["capacidades"].append(bateria["capacidad_ah"])
        if bateria["energia_wh"]:
            dato["energias"].append(bateria["energia_wh"])
        if bateria["quimica"]:
            dato["quimicas"].append(bateria["quimica"])

    filas = []
    for dato in por_marca.values():
        filas.append({
            "marca": dato["marca"],
            "n": dato["n"],
            "dentro": dato["dentro"],
            "precio_prom": stat.mean(dato["precios"]),
            "precio_min": min(dato["precios"]),
            "autonomia_prom": stat.mean(dato["autonomias"]),
            "autonomia_max": max(dato["autonomias"]),
            "usd_km": stat.mean(dato["usd_km"]) if dato["usd_km"] else None,
            "voltaje": stat.mean(dato["voltajes"]) if dato["voltajes"] else None,
            "capacidad": stat.mean(dato["capacidades"]) if dato["capacidades"] else None,
            "energia": stat.mean(dato["energias"]) if dato["energias"] else None,
            "quimica": Counter(dato["quimicas"]).most_common(1)[0][0]
                       if dato["quimicas"] else "—",
        })
    filas.sort(key=lambda f: f["usd_km"] if f["usd_km"] is not None else 1e9)
    return filas


def tabla_marcas_markdown() -> str:
    """Tabla del ranking de marcas por relacion calidad-precio."""
    filas = []
    for f in resumen_marcas():
        filas.append([
            f["marca"],
            str(f["n"]),
            f"**{f['dentro']}**" if f["dentro"] else "0",
            "Sí" if f["dentro"] else "No",
            _formato(f["precio_prom"]),
            _formato(f["autonomia_prom"]),
            _formato(f["autonomia_max"]),
            _formato(f["usd_km"], 1),
            _formato(f["voltaje"]) if f["voltaje"] else "—",
            _formato(f["capacidad"]) if f["capacidad"] else "—",
            _formato(f["energia"]) if f["energia"] else "—",
            f["quimica"],
        ])
    return tabla_markdown(
        ["Marca", "Productos", "Caben en 1.500 USD", "¿Lucy puede comprar?",
         "Precio prom. (USD)", "Autonomía prom. (km)", "Autonomía máx. (km)",
         "USD por km", "Voltaje (V)", "Capacidad (Ah)", "Energía (Wh)",
         "Química"],
        filas,
    )


# --------------------------------- autonomia por tipo (Bloque B)

def autonomia_por_tipo(mercados=MERCADOS) -> dict:
    """Por mercado y tipo de vehiculo: cuantos productos hay, cuantos caben en
    el presupuesto y la lista de autonomias (de todos y de los que caben)."""
    datos = {}
    for mercado in mercados:
        for categoria in ORDEN:
            grupo = grupo_de(mercado, categoria)
            dentro = [p for p in grupo
                      if _precio(mercado, p) <= PRESUPUESTO_LUCY]
            datos[(mercado["slug"], categoria)] = {
                "mercado": mercado["nombre"],
                "categoria": categoria,
                "n": len(grupo),
                "n_dentro": len(dentro),
                "autonomias": sorted(int(_autonomia(mercado, p)) for p in grupo),
                "autonomias_dentro": sorted(int(_autonomia(mercado, p))
                                            for p in dentro),
            }
    return datos


def mejor_por_tipo(mercados=MERCADOS) -> dict:
    """Por mercado y tipo, el producto comprable con mejor relacion
    precio-autonomia (menor USD por km); None si no hay ninguno que cabe."""
    datos = {}
    for mercado in mercados:
        for categoria in ORDEN:
            comprables = alcanzables_de(mercado, categoria)
            if not comprables:
                datos[(mercado["slug"], categoria)] = None
                continue
            mejor = min(
                comprables,
                key=lambda p: _precio(mercado, p) / int(_autonomia(mercado, p)))
            precio = _precio(mercado, mejor)
            autonomia = int(_autonomia(mercado, mejor))
            datos[(mercado["slug"], categoria)] = {
                "mercado": mercado["nombre"],
                "categoria": categoria,
                "marca": mejor.get("marca") or "Sin marca",
                "precio": precio,
                "autonomia": autonomia,
                "usd_km": precio / autonomia,
            }
    return datos


def _figura_mapa_autonomia(matriz, datos, clave, mercados, filas, titulo, cmap,
                           tope):
    """Construye una figura con un solo mapa de calor de autonomia tipica."""
    fig, ax = plt.subplots(figsize=(7.8, 5.2))
    imagen = ax.imshow(np.ma.masked_invalid(matriz), cmap=cmap, vmin=0,
                       vmax=tope, aspect="auto")
    ax.set_xticks(range(len(mercados)))
    ax.set_xticklabels([m["nombre"].split(" (")[0] for m in mercados],
                       fontsize=13.5, fontweight="bold")
    ax.set_yticks(range(len(filas)))
    ax.set_yticklabels([ETIQUETAS[c] for c in filas], fontsize=12.5)
    ax.set_xticks(np.arange(-0.5, len(mercados), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(filas), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=3)
    ax.tick_params(which="both", length=0)
    for borde in ax.spines.values():
        borde.set_visible(False)

    for i, categoria in enumerate(filas):
        for j, mercado in enumerate(mercados):
            valor = matriz[i, j]
            if np.isfinite(valor):
                color = "white" if valor > tope * 0.6 else "#1A1A1A"
                ax.text(j, i, f"{valor:.0f} km", ha="center", va="center",
                        fontsize=15, fontweight="bold", color=color)
            else:
                texto = ("no vende"
                         if not datos[(mercado["slug"], categoria)]["n"]
                         else "nadie entra")
                ax.text(j, i, texto, ha="center", va="center",
                        fontsize=10.5, color="#6B7280")

    barra = fig.colorbar(imagen, ax=ax, fraction=0.055, pad=0.04)
    barra.set_label("Autonomía típica (km)", fontsize=11)
    barra.outline.set_visible(False)

    fig.suptitle(titulo, fontsize=16.5, fontweight="bold", y=0.99)
    fig.text(0.5, 0.905,
             "Cada celda es la autonomía típica (la mediana), en km. "
             "Más oscuro = llega más lejos.",
             ha="center", va="center", fontsize=11, color="#4B5563")
    fig.subplots_adjust(top=0.80, bottom=0.10, left=0.24, right=0.99)
    return fig


def figura_autonomia_heatmap(ruta_publicados: Path | None = None,
                             ruta_presupuesto: Path | None = None):
    """G-mercado. Dos mapas de calor separados con la autonomia tipica (mediana)
    por tipo de vehiculo y mercado: 'Todo lo que se vende' en azul y 'Solo lo que
    cabe en 1.500 USD' en rojo. Cuanto mas oscura la celda, mas lejos llega."""
    from matplotlib.colors import LinearSegmentedColormap

    datos = autonomia_por_tipo()
    mercados = list(MERCADOS)
    filas = ORDEN

    def _mediana(valores):
        return float(np.median(valores)) if valores else float("nan")

    matrices = {
        "autonomias": np.array(
            [[_mediana(datos[(m["slug"], c)]["autonomias"]) for m in mercados]
             for c in filas], dtype=float),
        "autonomias_dentro": np.array(
            [[_mediana(datos[(m["slug"], c)]["autonomias_dentro"])
              for m in mercados] for c in filas], dtype=float),
    }

    tope = 0
    for matriz in matrices.values():
        validos = matriz[np.isfinite(matriz)]
        if validos.size:
            tope = max(tope, float(validos.max()))
    tope = float(np.ceil(tope / 20.0) * 20.0)

    cmap_azul = LinearSegmentedColormap.from_list(
        "azul", ["#EAF2FF", "#1D4ED8"])
    cmap_rojo = LinearSegmentedColormap.from_list(
        "rojo", ["#FCEDED", "#C81E1E"])
    for cm in (cmap_azul, cmap_rojo):
        cm.set_bad("#E5E7EB")

    paneles = [
        ("autonomias", "Todo lo que se vende", cmap_azul),
        ("autonomias_dentro",
         f"Solo lo que cabe en {_formato(PRESUPUESTO_LUCY)} USD", cmap_rojo),
    ]

    figuras = [
        _figura_mapa_autonomia(matrices[clave], datos, clave, mercados, filas,
                               titulo, cmap, tope)
        for clave, titulo, cmap in paneles
    ]
    figuras[0] = _guardar(figuras[0], ruta_publicados)
    figuras[1] = _guardar(figuras[1], ruta_presupuesto)
    return figuras


def productos_todos() -> list[dict]:
    """Todos los productos analizados (Internet y Mercado) con tipo, marca,
    sitio, precio en USD y autonomia en km."""
    items = []
    for sitio in SITIOS + MERCADOS:
        for p in cargar_sitio(sitio):
            autonomia = _autonomia(sitio, p)
            if not autonomia:
                continue
            items.append({
                "tipo": p["tipo_vehiculo"],
                "marca": p.get("marca") or "Sin marca",
                "sitio": sitio["nombre"],
                "precio": round(float(_precio(sitio, p))),
                "autonomia": int(autonomia),
            })
    return items


def figura_explorador(ruta: Path | None = None,
                      presupuesto: float = PRESUPUESTO_LUCY):
    """Vista previa estatica del explorador: autonomia frente a precio de todos
    los productos, con la mejor autonomia alcanzable para cada presupuesto."""
    from matplotlib.lines import Line2D

    productos = productos_todos()
    fig, ax = plt.subplots(figsize=(10.6, 6.4))

    for tipo in ORDEN:
        dentro = [p for p in productos
                  if p["tipo"] == tipo and p["precio"] <= presupuesto]
        fuera = [p for p in productos
                 if p["tipo"] == tipo and p["precio"] > presupuesto]
        color = COLOR_TIPO[ETIQUETAS[tipo]]
        ax.scatter([p["precio"] for p in fuera],
                   [p["autonomia"] for p in fuera], s=26, color=color,
                   alpha=0.16, linewidth=0, zorder=2)
        ax.scatter([p["precio"] for p in dentro],
                   [p["autonomia"] for p in dentro], s=44, color=color,
                   edgecolor="white", linewidth=0.8, zorder=3,
                   label=ETIQUETAS[tipo])

    orden = sorted(productos, key=lambda p: p["precio"])
    fx, fy, mejor = [0.0], [0], 0
    for p in orden:
        if p["autonomia"] > mejor:
            mejor = p["autonomia"]
            fx.append(p["precio"])
            fy.append(mejor)
    fx.append(max(p["precio"] for p in productos))
    fy.append(mejor)
    ax.plot(fx, fy, drawstyle="steps-post", color="#111827", linewidth=2.3,
            zorder=4)

    ax.axvline(presupuesto, color="#E63946", linewidth=2,
               linestyle=(0, (1, 2.5)), zorder=1)

    alto = max((p for p in productos if p["precio"] <= presupuesto),
               key=lambda p: p["autonomia"])
    ax.scatter([alto["precio"]], [alto["autonomia"]], marker="*", s=300,
               color="#E63946", edgecolor="white", linewidth=0.9, zorder=6)
    ax.annotate(f"{alto['autonomia']} km · {ETIQUETAS[alto['tipo']]}",
                (alto["precio"], alto["autonomia"]), xytext=(10, 8),
                textcoords="offset points", fontsize=10.5, fontweight="bold",
                color="#E63946")

    ax.set_xlabel("Precio (USD)", fontsize=12.5)
    ax.set_ylabel("Autonomía (km)", fontsize=12.5)
    ax.set_xlim(0, max(p["precio"] for p in productos) * 1.02)
    ax.set_ylim(0, max(p["autonomia"] for p in productos) * 1.12)
    ax.set_title(f"Hasta dónde llega un presupuesto de "
                 f"{_formato(presupuesto)} USD", fontsize=16,
                 fontweight="bold", pad=42)
    _leyenda_arriba(ax, [
        Line2D([0], [0], marker="o", color="none",
               markerfacecolor=COLOR_TIPO[ETIQUETAS[t]], markeredgecolor="white",
               markersize=12, label=ETIQUETAS[t]) for t in ORDEN
    ] + [Line2D([0], [0], color="#111827", linewidth=2.3,
                label="Mejor autonomía a ese precio")], ncol=4)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(linestyle=":", alpha=0.4, zorder=0)
    fig.tight_layout()
    return _guardar(fig, ruta)


def ejecutar():
    """Genera y guarda los graficos de las tres fuentes analizadas."""
    CARPETA_GRAFICOS.mkdir(exist_ok=True)
    figura_precios_promedio(CARPETA_GRAFICOS / "precios_promedio_sitios.png")
    figura_disponibilidad(CARPETA_GRAFICOS / "disponibilidad_presupuesto.png")
    figura_alcance_general(CARPETA_GRAFICOS / "autonomia_alcance_sitios.png")
    figura_autonomia_heatmap(
        CARPETA_GRAFICOS / "autonomia_mercado_publicados.png",
        CARPETA_GRAFICOS / "autonomia_mercado_presupuesto.png")
    figura_encuestas_degradacion(
        CARPETA_GRAFICOS / "encuestas_uso_degradacion.png")
    figura_encuestas_calidad(CARPETA_GRAFICOS / "encuestas_calidad.png")
    figura_encuestas_real_vs_publicada(
        CARPETA_GRAFICOS / "encuestas_real_vs_publicada.png")
    figura_explorador(CARPETA_GRAFICOS / "explorador_presupuesto.png")
    return CARPETA_GRAFICOS


# ==============================================================================
# TERCERA FUENTE: ENCUESTAS  (personas que ya tienen un vehiculo electrico)
#   Bloque A: tabla descriptiva por persona.
#   Bloque B: autonomia por tipo, degradacion por marca, calidad de las
#             opiniones y contraste de la autonomia real con la publicada.
# ==============================================================================

def cargar_encuestas() -> list[dict]:
    """Devuelve la lista de personas encuestadas."""
    ruta = RAIZ / "data" / ARCHIVO_ENCUESTAS
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)["personas"]


def _perdida(persona: dict) -> tuple[float, float]:
    """Autonomia perdida desde la compra: (km, %). Positivo = perdio autonomia;
    negativo = gano (le rinde mas que cuando la compro)."""
    nueva = persona["autonomia_nueva_km"]
    actual = persona["autonomia_actual_km"]
    km = nueva - actual
    porciento = (km / nueva * 100) if nueva else 0.0
    return km, porciento


def tabla_encuestas_markdown() -> str:
    """Bloque A. Una fila por persona con sus datos y la perdida calculada."""
    filas = []
    for p in cargar_encuestas():
        km, porciento = _perdida(p)
        filas.append([
            p["id"],
            ETIQUETAS[p["tipo_vehiculo"]],
            p["marca"],
            _formato(p["anios_uso"], 1),
            _formato(p["precio_usd"]),
            _formato(p["autonomia_nueva_km"]),
            _formato(p["autonomia_actual_km"]),
            _formato(km),
            _formato(porciento, 1) + " %",
            p["calidad"],
        ])
    return tabla_markdown(
        ["Persona", "Tipo", "Marca", "Tiempo (años)", "Precio (USD)",
         "Autonomía nueva (km)", "Autonomía actual (km)", "Pérdida (km)",
         "Pérdida (%)", "Calidad"],
        filas,
    )


def resumen_encuestas_tipo() -> list[dict]:
    """Bloque B. Por tipo de vehiculo: cuantas personas, precio, autonomia
    nueva/actual y perdida promedio."""
    encuestas = cargar_encuestas()
    filas = []
    for categoria in ORDEN:
        grupo = [p for p in encuestas if p["tipo_vehiculo"] == categoria]
        if not grupo:
            continue
        perdidas = [_perdida(p)[1] for p in grupo]
        filas.append({
            "categoria": categoria,
            "n": len(grupo),
            "precio_prom": stat.mean([p["precio_usd"] for p in grupo]),
            "nueva_prom": stat.mean([p["autonomia_nueva_km"] for p in grupo]),
            "actual_prom": stat.mean([p["autonomia_actual_km"] for p in grupo]),
            "perdida_prom": stat.mean(perdidas),
        })
    return filas


def tabla_encuestas_tipo_markdown() -> str:
    """Tabla resumen por tipo de vehiculo."""
    filas = []
    for f in resumen_encuestas_tipo():
        filas.append([
            ETIQUETAS[f["categoria"]],
            str(f["n"]),
            _formato(f["precio_prom"]),
            _formato(f["nueva_prom"]),
            _formato(f["actual_prom"]),
            _formato(f["perdida_prom"], 1) + " %",
        ])
    return tabla_markdown(
        ["Tipo", "Personas", "Precio prom. (USD)", "Autonomía nueva prom. (km)",
         "Autonomía actual prom. (km)", "Pérdida prom. (%)"],
        filas,
    )


def degradacion_por_marca() -> list[dict]:
    """Bloque B. Por marca: cuantas personas, años de uso promedio y caida de la
    autonomia (%). Solo marcas con al menos una persona."""
    encuestas = cargar_encuestas()
    por_marca: dict[str, dict] = {}
    for p in encuestas:
        dato = por_marca.setdefault(p["marca"], {
            "marca": p["marca"], "n": 0, "tipos": set(),
            "anios": [], "nueva": [], "actual": [], "perdida": [],
            "notas": [],
        })
        dato["n"] += 1
        dato["tipos"].add(ETIQUETAS[p["tipo_vehiculo"]])
        dato["anios"].append(p["anios_uso"])
        dato["nueva"].append(p["autonomia_nueva_km"])
        dato["actual"].append(p["autonomia_actual_km"])
        dato["perdida"].append(_perdida(p)[1])
        if p["nota"]:
            dato["notas"].append(f"{p['id'].replace('PERSONA ', 'P')}: {p['nota']}")

    filas = []
    for dato in por_marca.values():
        filas.append({
            "marca": dato["marca"],
            "n": dato["n"],
            "tipos": ", ".join(sorted(dato["tipos"])),
            "anios_prom": stat.mean(dato["anios"]),
            "nueva_prom": stat.mean(dato["nueva"]),
            "actual_prom": stat.mean(dato["actual"]),
            "perdida_prom": stat.mean(dato["perdida"]),
            "observaciones": " ".join(dato["notas"]) if dato["notas"] else "—",
        })
    filas.sort(key=lambda f: f["perdida_prom"])
    return filas


def tabla_degradacion_markdown() -> str:
    """Tabla de degradacion de la autonomia por marca."""
    filas = []
    for f in degradacion_por_marca():
        filas.append([
            f["marca"],
            str(f["n"]),
            f["tipos"],
            _formato(f["anios_prom"], 1),
            _formato(f["nueva_prom"]),
            _formato(f["actual_prom"]),
            _formato(f["perdida_prom"], 1) + " %",
            f["observaciones"],
        ])
    return tabla_markdown(
        ["Marca", "Personas", "Tipo(s)", "Años de uso prom.",
         "Autonomía nueva prom. (km)", "Autonomía actual prom. (km)",
         "Pérdida prom. (%)", "Observaciones"],
        filas,
    )


def calidad_resumen() -> dict:
    """Bloque B. Cuantas opiniones hay de cada nivel de calidad."""
    conteo = Counter(p["calidad"] for p in cargar_encuestas())
    return {nivel: conteo.get(nivel, 0) for nivel in ORDEN_CALIDAD}


def tabla_calidad_markdown() -> str:
    """Tabla del conteo de opiniones de calidad."""
    conteo = calidad_resumen()
    total = sum(conteo.values()) or 1
    filas = []
    for nivel in ORDEN_CALIDAD:
        n = conteo[nivel]
        filas.append([nivel, str(n), _formato(n / total * 100, 1) + " %"])
    return tabla_markdown(["Calidad", "Personas", "Porcentaje"], filas)


def _autonomia_promedio_publicada(sitios, categoria: str) -> float | None:
    """Autonomia promedio publicada de una categoria en un grupo de sitios."""
    valores = [int(_autonomia(s, p))
               for s in sitios for p in grupo_de(s, categoria)]
    return stat.mean(valores) if valores else None


def real_vs_publicada() -> list[dict]:
    """Bloque B. Por tipo: autonomia de los dueños (nueva y actual) frente a la
    autonomia publicada en INTERNET y en MERCADO."""
    encuestas = cargar_encuestas()
    filas = []
    for categoria in ORDEN:
        grupo = [p for p in encuestas if p["tipo_vehiculo"] == categoria]
        if not grupo:
            continue
        filas.append({
            "categoria": categoria,
            "n": len(grupo),
            "nueva_prom": stat.mean([p["autonomia_nueva_km"] for p in grupo]),
            "actual_prom": stat.mean([p["autonomia_actual_km"] for p in grupo]),
            "internet_prom": _autonomia_promedio_publicada(SITIOS, categoria),
            "mercado_prom": _autonomia_promedio_publicada(MERCADOS, categoria),
        })
    return filas


def tabla_real_vs_publicada_markdown() -> str:
    """Tabla que compara la autonomia real (dueños) con la publicada."""
    filas = []
    for f in real_vs_publicada():
        filas.append([
            ETIQUETAS[f["categoria"]],
            str(f["n"]),
            _formato(f["nueva_prom"]),
            _formato(f["actual_prom"]),
            _formato(f["internet_prom"]),
            _formato(f["mercado_prom"]),
        ])
    return tabla_markdown(
        ["Tipo", "Personas", "Autonomía nueva real (km)",
         "Autonomía actual real (km)", "Publicada en Internet (km)",
         "Publicada en Mercado (km)"],
        filas,
    )


# --------------------------------- graficos de encuestas

COLOR_CALIDAD = {"Buena": "#10B981", "Regular": "#F9A602", "Mala": "#E63946"}

COLOR_TIPO = {"Moto eléctrica": "#1D6FE0",
              "Bicicleta eléctrica": "#10B981",
              "Patinete eléctrico": "#F9A602"}


def figura_encuestas_degradacion(ruta: Path | None = None):
    """Dispersion: años de uso (x) frente al % de autonomia perdida (y), con una
    linea de tendencia. El color indica el tipo de vehiculo."""
    from matplotlib.lines import Line2D

    encuestas = cargar_encuestas()
    xs = [p["anios_uso"] for p in encuestas]
    ys = [_perdida(p)[1] for p in encuestas]

    fig, ax = plt.subplots(figsize=(10.4, 6.6))
    for tipo in ORDEN:
        puntos = [p for p in encuestas if p["tipo_vehiculo"] == tipo]
        ax.scatter([p["anios_uso"] for p in puntos],
                   [_perdida(p)[1] for p in puntos], s=150,
                   color=COLOR_TIPO[ETIQUETAS[tipo]], edgecolor="white",
                   linewidth=1.6, alpha=0.9, zorder=3)

    base = [p for p in encuestas if not p["bateria_cambiada"] and not p["nota"]]
    pendiente, corte = np.polyfit([p["anios_uso"] for p in base],
                                  [_perdida(p)[1] for p in base], 1)
    xr = np.linspace(min(xs), max(xs), 50)
    ax.plot(xr, pendiente * xr + corte, "--", color="#6B7280",
            linewidth=2.2, zorder=2)

    ax.axhline(0, color="#9CA3AF", linewidth=1.2, linestyle=":", zorder=1)

    for p in encuestas:
        _, porciento = _perdida(p)
        if p["bateria_cambiada"] or p["nota"] or porciento < 0:
            ax.annotate(p["id"].replace("PERSONA ", "P"),
                        (p["anios_uso"], porciento),
                        textcoords="offset points", xytext=(0, 13),
                        ha="center", fontsize=9.5, fontweight="bold",
                        color="#374151")

    ax.set_xlabel("Años de uso", fontsize=12.5)
    ax.set_ylabel("Autonomía perdida (%)", fontsize=12.5)
    ax.set_xlim(-0.4, max(xs) + 0.8)
    ax.set_title("A más años de uso, más autonomía se pierde",
                 fontsize=16, fontweight="bold", pad=42)
    _leyenda_arriba(ax, [
        Line2D([0], [0], marker="o", color="none",
               markerfacecolor=COLOR_TIPO[ETIQUETAS[t]],
               markeredgecolor="white", markersize=12, label=ETIQUETAS[t])
        for t in ORDEN
    ] + [Line2D([0], [0], color="#6B7280", linewidth=2.2, linestyle="--",
                label="Tendencia")], ncol=4)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(linestyle=":", alpha=0.4, zorder=0)
    fig.tight_layout()
    return _guardar(fig, ruta)


def figura_encuestas_real_vs_publicada(ruta: Path | None = None):
    """Dumbbell: por tipo, la autonomia real de los dueños frente a la
    publicada en Internet y en Mercado, unidas por una linea."""
    from matplotlib.lines import Line2D

    filas = real_vs_publicada()
    tipos = [f["categoria"] for f in filas]
    y = list(range(len(tipos)))
    color_real, color_internet, color_mercado = "#E63946", "#1D6FE0", "#10B981"

    fig, ax = plt.subplots(figsize=(10.2, 5.0))
    for i, f in enumerate(filas):
        valores = [v for v in (f["nueva_prom"], f["internet_prom"],
                               f["mercado_prom"]) if v is not None]
        ax.plot([min(valores), max(valores)], [i, i], color="#D1D5DB",
                linewidth=5, solid_capstyle="round", zorder=1)
        for valor, color in ((f["nueva_prom"], color_real),
                             (f["internet_prom"], color_internet),
                             (f["mercado_prom"], color_mercado)):
            if valor is None:
                continue
            ax.scatter([valor], [i], s=180, color=color, edgecolor="white",
                       linewidth=1.7, zorder=3)
        ax.text(f["nueva_prom"], i - 0.20, f"{f['nueva_prom']:.0f}",
                ha="center", va="top", fontsize=11, fontweight="bold",
                color=color_real)
        ax.text(f["internet_prom"], i - 0.20, f"{f['internet_prom']:.0f}",
                ha="center", va="top", fontsize=11, fontweight="bold",
                color=color_internet)
        ax.text(f["mercado_prom"], i + 0.20, f"{f['mercado_prom']:.0f}",
                ha="center", va="bottom", fontsize=11, fontweight="bold",
                color=color_mercado)

    ax.set_yticks(y)
    ax.set_yticklabels([ETIQUETAS[t] for t in tipos], fontsize=12.5)
    ax.set_xlabel("Autonomía promedio (km)", fontsize=12.5)
    ax.set_xlim(0, 120)
    ax.set_ylim(-0.7, len(tipos) - 0.3)
    ax.set_title("La autonomía real de los dueños frente a la publicada",
                 fontsize=16, fontweight="bold", pad=42)
    _leyenda_arriba(ax, [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=color_real,
               markeredgecolor="white", markersize=12, label="Real (dueños)"),
        Line2D([0], [0], marker="o", color="none",
               markerfacecolor=color_internet, markeredgecolor="white",
               markersize=12, label="Publicada en Internet"),
        Line2D([0], [0], marker="o", color="none",
               markerfacecolor=color_mercado, markeredgecolor="white",
               markersize=12, label="Publicada en Mercado"),
    ], ncol=3)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", linestyle=":", alpha=0.4, zorder=0)
    fig.tight_layout()
    return _guardar(fig, ruta)


def figura_encuestas_calidad(ruta: Path | None = None):
    """Pastel: cuantas personas califican su vehiculo como bueno, regular o
    malo."""
    conteo = calidad_resumen()
    total = len(cargar_encuestas()) or 1
    niveles = [n for n in ORDEN_CALIDAD if conteo.get(n)]
    valores = [conteo[n] for n in niveles]
    colores = [COLOR_CALIDAD[n] for n in niveles]

    fig, ax = plt.subplots(figsize=(5.4, 4.6))
    cuñas, _, textos = ax.pie(
        valores, colors=colores, startangle=90, counterclock=False,
        autopct=lambda pct: f"{pct:.0f} %", pctdistance=0.75,
        wedgeprops={"width": 0.42, "edgecolor": "white", "linewidth": 2},
        textprops={"fontsize": 11, "fontweight": "bold", "color": "white"})
    ax.text(0, 0.12, f"{total}", ha="center", va="center", fontsize=22,
            fontweight="bold", color="#1A1A1A")
    ax.text(0, -0.16, "personas", ha="center", va="center", fontsize=10.5,
            color="#6B7280")
    ax.text(0, -0.38, "Mala: 0", ha="center", va="center", fontsize=9.5,
            color="#6B7280")

    ax.legend(
        [f"{nivel}: {conteo[nivel]}" for nivel in niveles],
        loc="lower center", bbox_to_anchor=(0.5, -0.08), ncol=len(niveles),
        frameon=False, fontsize=11)
    ax.set_title("La calidad según sus dueños", fontsize=15,
                 fontweight="bold", pad=14)
    ax.set_aspect("equal")
    fig.tight_layout()
    return _guardar(fig, ruta)


# ==============================================================================
# OTRAS FUENTES
#   Telegram (mas adelante). Aqui se van anadiendo sus datos y analisis.
# ==============================================================================


if __name__ == "__main__":
    destino = ejecutar()
    print("Gráficos guardados en:", destino)
    print()
    print("TABLA DE RESUMEN DE LOS DOS SITIOS (INTERNET)")
    print(tabla_resumen_markdown())
    print()
    print("TABLA DE RESUMEN DEL MERCADO (VEDCA e CubAmerica)")
    print(tabla_resumen_mercado())
    print()
    print("AUTONOMÍA POR TIPO Y MERCADO (todos / caben en 1.500 USD)")
    for clave, dato in autonomia_por_tipo().items():
        print(f"  {dato['mercado']:22} {ETIQUETAS[dato['categoria']]:22} "
              f"n={dato['n']:2} dentro={dato['n_dentro']:2} "
              f"| todos {dato['autonomias']} | dentro {dato['autonomias_dentro']}")
    print()
    print("MEJOR OPCIÓN DE CADA TIPO EN CADA MERCADO (menor USD por km)")
    for clave, dato in mejor_por_tipo().items():
        if dato is None:
            mercado = DICC_MERCADOS[clave[0]]["nombre"]
            print(f"  {mercado:22} {ETIQUETAS[clave[1]]:22} sin opciones dentro del presupuesto")
        else:
            print(f"  {dato['mercado']:22} {ETIQUETAS[dato['categoria']]:22} "
                  f"{dato['marca']:10} {_formato(dato['precio'])} USD / "
                  f"{dato['autonomia']} km ({_formato(dato['usd_km'], 1)} USD/km)")
    print()
    print("TERCERA FUENTE: ENCUESTAS A PERSONAS")
    print(tabla_encuestas_tipo_markdown())
    print()
    print(tabla_degradacion_markdown())
    print()
    print(tabla_calidad_markdown())
    print()
    print(tabla_real_vs_publicada_markdown())
