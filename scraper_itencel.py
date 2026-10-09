# -*- coding: utf-8 -*-
"""Scraper de iTENCEL (itencel.com).

Portal de anuncios clasificados de Cuba. Se lee por la API REST de WordPress
(/wp-json/wp/v2/rtcl_listing): se buscan los anuncios de vehiculos electricos
dentro de las categorias Motos y Bicicletas y se conserva SOLO el minimo que
exige el analisis: marca, precio (USD), autonomia maxima en km y, si se
publica, un dato corto de bateria. Los anuncios que no tienen autonomia
publicada se descartan y se sustituyen por otros que si la tengan, hasta 50
por tipo de vehiculo.

Las bicimotos cuentan como bicicleta electrica (decision de la autora).

Salida: data/itencel_anuncios.json
"""

import json
import re
import time
from html import unescape
from pathlib import Path

import requests

# ------------------------------------------------------------------------------
# Configuracion
# ------------------------------------------------------------------------------

SITIO = "https://itencel.com"
API = SITIO + "/wp-json/wp/v2/rtcl_listing"
SALIDA = Path(__file__).resolve().parent / "data" / "itencel_anuncios.json"

TASA_CUP_POR_USD = 745     # tasa fijada por la autora
MAX_POR_TIPO = 50          # tope de registros por tipo de vehiculo
MIN_PRECIO_USD = 100       # reclamos "consulte" por debajo no cuentan
MAX_PAGINAS_POR_TERMINO = 80    # seguridad: nunca pasar de aqui por termino
OBJETIVO_ELIGIBLES = 520   # candidatos con autonomia para llenar los topes
TIMEOUT = 60
PAUSA_ENTRE_PETICIONES = 0.3
MAX_PETICIONES = 450          # presupuesto para no pasarse de tiempo
FECHA = "2026-10-06"       # fecha del dia, hora de Espana

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

CATEGORIAS = ("rtcl_category-motos", "rtcl_category-bicicletas")

BUSCADOS = ("electrica", "electrico", "el\u00e9ctrica", "el\u00e9ctrico",
            "ebike", "patinete", "scooter", "bateria",
            "moto electrica", "bicicleta electrica", "patinete electrico",
            "scooter electrico", "bicimoto", "moto", "bicicleta")

EMOJIS = re.compile(
    "[\U0001F000-\U0001FAFF\u2300-\u27BF\u2B00-\u2BFF\u2600-\u26FF\uFE0F]")


# ------------------------------------------------------------------------------
# Lectura de la API
# ------------------------------------------------------------------------------

def pedir_pagina(sesion, termino, pagina):
    """Una pagina de la busca con reintentos (la conexion es inestable)."""
    for intento in range(5):
        try:
            r = sesion.get(API,
                           params={"search": termino, "per_page": 100, "page": pagina},
                           timeout=TIMEOUT)
            if r.status_code == 200:
                return json.loads(r.text)
        except (requests.RequestException, ValueError):
            pass
        time.sleep(1 + 3 * intento)
    return None


def candidatos(sesion):
    """Anuncios de motos/bicicletas con autonomia publicada (recientes 1os)."""
    vistos, pedidas, eligibles, fallos_seguidos = {}, 0, 0, 0
    for termino in BUSCADOS:
        pagina, huecos = 1, 0
        while pagina <= MAX_PAGINAS_POR_TERMINO:
            items = pedir_pagina(sesion, termino, pagina)
            pedidas += 1
            if items is None:
                fallos_seguidos += 1
                print("  [!] pag %2d de %-10s sin respuesta (fallas %d)"
                      % (pagina, termino, fallos_seguidos))
                time.sleep(3)
                if fallos_seguidos >= 4:
                    pagina += 1            # se abandona esa pagina, se sigue
                else:
                    continue               # se reintenta la misma pagina
                continue
            fallos_seguidos = 0
            nuevos = 0
            for p in items:
                if not (set(p.get("class_list") or []) & set(CATEGORIAS)):
                    continue
                enlace = p.get("link") or ""
                if not enlace:
                    continue
                titulo = re.sub(r"\s+", " ",
                                (p.get("title") or {}).get("rendered") or "").strip()
                contenido = re.sub(
                    r"\s+", " ",
                    re.sub(r"<[^>]+>", " ",
                           (p.get("content") or {}).get("rendered") or "")).strip()
                if enlace in vistos:
                    continue
                cuerpo = unescape("%s %s" % (titulo, contenido))
                if not es_el_ectrico(cuerpo):
                    continue
                if not es_un_vehiculo(titulo, contenido):
                    continue
                a_min, a_max = autonomia_desde(cuerpo)
                if not (a_min or a_max):
                    continue
                vistos[enlace] = {
                    "titulo": unescape(titulo),
                    "contenido": unescape(contenido),
                    "fecha": p.get("date") or "",
                    "url": enlace,
                    "cuerpo": cuerpo,
                    "autonomia_max_km": int(a_max or a_min),
                }
                nuevos += 1
                eligibles += 1
            print("  %-12s pag %d/%-3d len %3d | acumulados %d (req %d/%d)"
                  % (termino, pagina, MAX_PAGINAS_POR_TERMINO, len(items),
                     eligibles, pedidas, MAX_PETICIONES))
            if len(items) < 100:
                print("    parada: pagina corta (len %d)" % len(items))
                break
            if nuevos == 0:
                huecos += 1
                if huecos >= 4:
                    print("    parada: sin nuevos x4")
                    break
            else:
                huecos = 0
            if pedidas >= MAX_PETICIONES:
                print("    parada: presupuesto de peticiones")
                break
            if eligibles >= OBJETIVO_ELIGIBLES:
                print("    parada: objetivo alcanzado")
                break
            if pagina >= MAX_PAGINAS_POR_TERMINO:
                print("    parada: tope de paginas del termino")
                break
            pagina += 1
            time.sleep(PAUSA_ENTRE_PETICIONES)
        if eligibles >= OBJETIVO_ELIGIBLES:
            break
    print("Peticiones a la API:", pedidas)
    return list(vistos.values())


# ------------------------------------------------------------------------------
# Filtros
# ------------------------------------------------------------------------------

def es_el_ectrico(texto):
    return bool(re.search(r"lectric|ebike", texto, re.I))


def es_un_vehiculo(titulo, contenido):
    es_vehiculo = r"\bmoto\w*|\bbici\w*|bicimoto|patinet|scooter|ebike|triciclo"
    if re.search(r"\bbater\w*", titulo, re.I) and \
            not re.search(es_vehiculo, titulo, re.I):
        return False                      # titulo: solo vende la bateria
    return bool(re.search(es_vehiculo, titulo + " " + contenido, re.I))


def tipo_de(titulo):
    t = titulo.lower()
    if re.search(r"\bpatinet|scooter|patinete", t):
        return "Patinete electrico"
    if re.search(r"\bbicimoto|bimoto", t):
        return "Bicicleta electrica"
    if re.search(r"\bmoto", t):
        return "Moto electrica"
    return "Bicicleta electrica"


# ------------------------------------------------------------------------------
# Bateria y autonomia
# ------------------------------------------------------------------------------

def _numero(cadena):
    return float(cadena.replace(",", "."))


def entero_si_entero(valor):
    valor = round(valor, 2)
    return int(valor) if float(valor).is_integer() else valor


QUIMICA = re.compile(
    r"(lifepo4|li[-\s]?ion|lithium(?:[-\s]?ion)?|litio|lib|gel|agm|plomo|"
    r"lead(?:[-\s]?acid)?|nicd|nimh)", re.I)


def bateria_corta(texto):
    """Dato corto de bateria: 'Litio 60V / 30Ah', sin emojis ni relleno."""
    if not texto:
        return None
    t = EMOJIS.sub(" ", str(texto))
    partes = []
    quimica = QUIMICA.search(t)
    if quimica:
        partes.append(quimica.group(1).strip())
    volt = re.search(r"\b(\d+(?:[.,]\d+)?)\s*(?:v\b|volt\w*)\b", t, re.I)
    if volt and 12 <= _numero(volt.group(1)) <= 120:
        partes.append("%sV" % entero_si_entero(_numero(volt.group(1))))
    amp = re.search(r"\b(\d+(?:[.,]\d+)?)\s*(?:a[h]?|amp\w*)\b", t, re.I)
    if amp and 1 <= _numero(amp.group(1)) <= 300:
        partes.append("%sAh" % entero_si_entero(_numero(amp.group(1))))
    return " / ".join(partes) if partes else None


def valida(a, b):
    return (a is not None and b is not None and a >= 5 and b >= 5
            and a <= 500 and b <= 500)


def autonomia_desde(texto):
    """Autonomia (min, max) publicada en el texto, o (None, None)."""

    def numeros_de(cadena):
        unidad = r"(?:km\b|kilometr\w*|kil\u00f3metr\w*)"
        rango = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:[-/\u2013\u2014]|to|hasta| y )\s*"
                          r"(\d+(?:[.,]\d+)?)\s*" + unidad + r"(?!/h)", cadena, re.I)
        if rango:
            a, b = _numero(rango.group(1)), _numero(rango.group(2))
            if a > b:
                a, b = b, a
            return a, b
        simple = re.search(r"\b(\d+(?:[.,]\d+)?)\s*" + unidad + r"(?!/h)",
                           cadena, re.I)
        if simple:
            n = _numero(simple.group(1))
            return n, n
        millas = re.search(r"\b(\d+(?:[.,]\d+)?)\s*(?:mill\w*|miles)\b(?!\s*/\s*h\b|\s*por hora\b)",
                           cadena, re.I)
        if millas:
            n = _numero(millas.group(1)) * 1.609
            return round(n, 1), round(n, 1)
        return None, None

    frases = []
    for m in re.finditer(r"autonom\w*\s*(?:de\s*)?[:\-]?\s*"
                         r"([^\u2022;|\n]{0,60})", texto, re.I):
        frase = re.sub(r"\s+", " ", m.group(1)).strip(":-\u2013\u2014. ")
        frase = frase.replace("\u00a0", " ").strip()
        if frase:
            frases.append(frase)
    for frase in frases:
        mn, mx = numeros_de(frase)
        if mn is not None and mn != mx and valida(mn, mx):
            return mn, mx
    for frase in frases:
        mn, mx = numeros_de(frase)
        if mn is not None and valida(mn, mx):
            return mn, mx
    mn, mx = numeros_de(re.sub(r"\s+", " ", texto))
    if valida(mn, mx):
        return mn, mx
    return None, None


def precio_desde_texto(texto):
    m = re.search(r"(\d[\d.,]*)\s*(USD|CUP|usd|cup)\b", texto, re.I)
    if not m:
        return None
    moneda = m.group(2).upper()
    monto = float(m.group(1).replace(".", "").replace(",", ""))
    if moneda == "CUP":
        return round(monto / TASA_CUP_POR_USD, 2)
    return round(monto, 2)


def precio_de_ficha(sesion, url):
    """Precio que muestra la ficha del anuncio (primer campo de la pagina)."""
    try:
        r = sesion.get(url, timeout=TIMEOUT)
        if r.status_code != 200:
            return None
        m = re.search(r"rtcl-price-amount[^>]*>([\d][\d.,]*)", r.text)
        if not m:
            return None
        return round(float(m.group(1).replace(".", "").replace(",", "")), 2)
    except requests.RequestException:
        return None


# ------------------------------------------------------------------------------
# Marca
# ------------------------------------------------------------------------------

MARCAS = [
    "windone", "hiboy", "topmaq", "topmax", "bucatti", "izuki",
    "fly racing", "halcon", "panther", "leopard", "rhynox", "hezzo",
    "mikazuki", "cocuyo", "raptor", "volt-x", "volt x", "e-lite",
    "e-track", "e-on", "infinity", "shark x", "brisa", "rayo", "bolt",
    "cross", "vedca", "panda city", "panda", "fenih", "jj9", "phoenix",
    "volpam", "etekhop", "werhy", "hover-1", "caroma", "ele-008",
    "wq-w4", "5th wheel", "viento rapido",
]


def marca_de(texto):
    n = texto.lower()
    mejores = []
    for marca in MARCAS:
        i = n.find(marca)
        if i >= 0:
            mejores.append((i, len(marca), marca))
    if not mejores:
        return "Generica"
    mejores.sort()
    mayor = max((m for m in mejores if m[0] == mejores[0][0]), key=lambda m: m[1])
    return mayor[2].title()


# ------------------------------------------------------------------------------
# Guardado y principal
# ------------------------------------------------------------------------------

def guardar(datos):
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def main():
    sesion = requests.Session()
    sesion.headers["User-Agent"] = UA
    sesion.headers["Accept-Language"] = "es-ES,es;q=0.8,en;q=0.5"

    posibles = candidatos(sesion)
    posibles = [p for p in posibles
                if es_el_ectrico(p["cuerpo"])
                and es_un_vehiculo(p["titulo"], p["contenido"])]
    posibles.sort(key=lambda a: a["fecha"], reverse=True)
    print("Candidatos con autonomia publicada:", len(posibles))

    elegidos = {"Moto electrica": [], "Bicicleta electrica": [],
                "Patinete electrico": []}
    saltados = {"Sin marcador de autonomia": 0,
                "Precio no publicado / reclamo": 0}
    descartes_tipo = {}

    for a in posibles:
        tipo = tipo_de(a["titulo"])
        if len(elegidos[tipo]) >= MAX_POR_TIPO:
            continue
        cuerpo = a["cuerpo"]
        marca = marca_de(cuerpo)
        precio = precio_desde_texto(cuerpo)
        if precio is None:
            precio = precio_de_ficha(sesion, a["url"])
        if precio is None or precio < MIN_PRECIO_USD:
            saltados["Precio no publicado / reclamo"] += 1
            descartes_tipo[tipo] = descartes_tipo.get(tipo, 0) + 1
            continue
        elegidos[tipo].append({
            "marca": marca,
            "tipo_vehiculo": tipo,
            "precio_usd": round(precio, 2),
            "autonomia_max_km": a["autonomia_max_km"],
        })
        bateria = bateria_corta(cuerpo)
        if bateria:
            elegidos[tipo][-1]["bateria"] = bateria

    lista = (elegidos["Moto electrica"] + elegidos["Bicicleta electrica"]
             + elegidos["Patinete electrico"])
    print("Elegidos:", len(lista),
          "| por tipo:", {t: len(elegidos[t]) for t in elegidos})

    datos = {
        "fuente": "iTENCEL (anuncios clasificados de Cuba)",
        "url": SITIO + "/anuncio-categoria/vehiculos/",
        "fecha": FECHA,
        "moneda_original": "mayoria en USD; algunos en CUP (tasa 745 CUP = 1 USD)",
        "anuncios_escaneados": len(posibles),
        "productos_relevantes": len(lista),
        "descartados_por_tipo": {**descartes_tipo, **saltados},
        "productos": [],
    }
    guardar(datos)

    for i, r in enumerate(lista, 1):
        datos["productos"].append(r)
        guardar(datos)
        print("  [%d/%d] %-17s %6s | %s | auto %4s km | %s"
              % (i, len(lista), r["tipo_vehiculo"], r["precio_usd"],
                 r["marca"], r["autonomia_max_km"],
                 r.get("bateria") or "-"))

    print()
    print("Guardado en:", SALIDA)
    print("Registros:", len(datos["productos"]))


if __name__ == "__main__":
    main()