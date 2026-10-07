# -*- coding: utf-8 -*-
"""Scraper de iTENCEL (itencel.com).

Fuente 2 del proyecto. Portal de anuncios clasificados de Cuba. Se usa la
API REST de WordPress (/wp-json/wp/v2/rtcl_listing) para buscar anuncios
de vehiculos electricos dentro de las categorias Motos y Bicicletas; la
peticion devuelve titulo, contenido y fecha, de modo que el precio, la
bateria y la autonomia se leen directamente del texto publicado.

Las bicimotos se cuentan como bicicleta electrica (decision de la autora).
Se guardan como maximo 50 por tipo de vehiculo (moto, bicicleta, patinete).

Salida: data/itencel_anuncios.json  (cabecera con la fuente, luego la lista)
"""

import json
import re
import time
from datetime import date
from html import unescape
from pathlib import Path

import requests

# ------------------------------------------------------------------------------
# Configuracion
# ------------------------------------------------------------------------------

SITIO = "https://itencel.com"
API = SITIO + "/wp-json/wp/v2/rtcl_listing"
SALIDA = Path(__file__).resolve().parent / "data" / "itencel_anuncios.json"

TASA_CUP_POR_USD = 745     # tasa fijada por la autora para Revolico, igual se usa aqui
MAX_POR_TIPO = 50          # tope de registros por tipo de vehiculo
MIN_PRECIO_USD = 100       # por debajo son reclamos "consulte", no un precio real
TIMEOUT = 30
PAUSA_ENTRE_PETICIONES = 0.3

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# Categorias que interesan, tal como las marca el plugin en class_list.
CATEGORIAS = ("rtcl_category-motos", "rtcl_category-bicicletas")

# Terminos de busqueda que abarcan los anuncios electricos. La API busca en
# titulo y contenido, asi que alcanza a patinetes y bicimotos sin "electric".
BUSCADOS = ("electrica", "electrico", "el\u00e9ctrica", "el\u00e9ctrico",
            "ebike", "patinete", "scooter", "bateria")

# La API ordena por fecha (mas recientes primero). Con las primeras paginas
# basta para cubrir el inventario actual; lo demas son anuncios pasados.
MAX_PAGINAS_POR_TERMINO = 6


def pedir_pagina(sesion, termino, pagina):
    """Una pagina de la API. Devuelve (items, total_paginas) o (None, 0)."""
    r = sesion.get(API, params={"search": termino, "per_page": 100, "page": pagina},
                   timeout=TIMEOUT)
    if r.status_code != 200:
        return None, 0
    try:
        return json.loads(r.text), int(r.headers.get("X-WP-TotalPages") or "1")
    except ValueError:
        return None, 0


def candidatos(sesion):
    """Anuncios de motos/bicicletas que mencionan algo electrico."""
    vistos, total_pedidas = {}, 0
    for termino in BUSCADOS:
        pagina, huecos = 1, 0
        while pagina <= MAX_PAGINAS_POR_TERMINO:
            items, _ = pedir_pagina(sesion, termino, pagina)
            total_pedidas += 1
            if items is None:
                break
            nuevos = 0
            for p in items:
                clases = set(p.get("class_list") or [])
                if not (clases & set(CATEGORIAS)):
                    continue
                enlace = p.get("link") or ""
                if not enlace:
                    continue
                titulo = re.sub(r"\s+", " ",
                                (p.get("title") or {}).get("rendered") or "").strip()
                contenido = re.sub(r"\s+", " ",
                                   re.sub(r"<[^>]+>", " ",
                                          (p.get("content") or {}).get("rendered") or "")).strip()
                if enlace in vistos:
                    continue
                vistos[enlace] = {
                    "titulo": unescape(titulo),
                    "contenido": unescape(contenido),
                    "fecha": p.get("date") or "",
                    "url": enlace,
                }
                nuevos += 1
            print("  %-12s pagina %d/%-3d (%d nuevos)" % (termino, pagina,
                                                          MAX_PAGINAS_POR_TERMINO, nuevos))
            if len(items) < 100:
                break
            if nuevos == 0:
                huecos += 1
                if huecos >= 2:            # dos paginas seguidas sin motos/bicis
                    break
            else:
                huecos = 0
            pagina += 1
            time.sleep(PAUSA_ENTRE_PETICIONES)
    print("Peticiones a la API:", total_pedidas)
    return list(vistos.values())


def es_el_ectrico(texto):
    """Verdadero si el anuncio describe un vehiculo electrico o ebike."""
    return bool(re.search(r"lectric|ebike", texto, re.I))


def es_un_vehiculo(titulo, contenido):
    """Verdadero si se vende un vehiculo y no solo una pieza o bateria."""
    es_vehiculo = r"\bmoto\w*|\bbici\w*|bicimoto|patinet|scooter|ebike|triciclo"
    if re.search(r"\bbater\w*", titulo, re.I) and \
            not re.search(es_vehiculo, titulo, re.I):
        return False                      # titulo: solo vende la bateria
    return bool(re.search(es_vehiculo, titulo + " " + contenido, re.I))


def tipo_de(titulo):
    """Tipo de vehiculo segun el titulo del anuncio."""
    t = titulo.lower()
    if re.search(r"\bpatinet|scooter|patinete", t):
        return "Patinete electrico"
    if re.search(r"\bbicimoto|bimoto", t):
        return "Bicicleta electrica"
    if re.search(r"\bmoto", t):
        return "Moto electrica"
    return "Bicicleta electrica"


# ------------------------------------------------------------------------------
# Bateria y autonomia desde el texto publicado
# ------------------------------------------------------------------------------

def _numero(cadena):
    return float(cadena.replace(",", "."))


def entero_si_entero(valor):
    if valor is None:
        return None
    return int(valor) if float(valor).is_integer() else valor


QUIMICA = re.compile(
    r"(lifepo4|li[-\s]?ion|lithium(?:[-\s]?ion)?|litio|lib|gel|agm|"
    r"plomo|lead(?:[-\s]?acid)?|nicd|nimh)", re.I)


def _limpiar_bateria(trozo):
    """Recorta el fragmento de bateria hasta datos que no le pertenecen."""
    trozo = re.sub(r"\s+", " ", trozo).strip(":-\u2013\u2014. ")
    trozo = trozo.replace("\u00a0", " ")
    if re.search(r"\b\d+(?:[.,]\d+)?\s*(?:v\b|volt|ah|amp)", trozo, re.I):
        antes = trozo.split(",", 1)[0]
        if re.search(r"\b\d+(?:[.,]\d+)?\s*(?:v\b|volt|ah|amp)", antes, re.I):
            trozo = antes
    trozo = re.split(r"\b\d+(?:[.,]\d+)?\s*(?:lbs|kg|cc|lb|wg|kgs)\b",
                     trozo, maxsplit=1)[0]
    trozo = re.split(r"\b(?:neumatico|neumatico|rin|motor)\b",
                     trozo, maxsplit=1)[0]
    return trozo.strip(" .:,-")


def bateria_desde(texto):
    """Tipo de bateria tal como aparece en el texto, si aparece."""
    frases = []
    for m in re.finditer(r"\bbater\w*\b[^\w]*([^\u2022;|\n]{2,70})",
                         texto, re.I):
        trozo = _limpiar_bateria(m.group(1))
        if not trozo:
            continue
        if re.search(r"\bsin\b", trozo, re.I) and not re.search(r"\d", trozo):
            continue                      # "SIN BATERIA": no es un dato util
        frases.append(trozo)
    for trozo in frases:                      # la mas completa (con Volt/Ah)
        if re.search(r"\b\d+(?:[.,]\d+)?\s*(?:v\b|volt|ah|amp)", trozo, re.I):
            return trozo[:70]
    for trozo in frases:                      # o la que diga el material
        if QUIMICA.search(trozo):
            return trozo[:70]
    quimica = QUIMICA.search(texto)
    volt = re.search(r"\b(\d+(?:[.,]\d+)?)\s*(?:volt\w*|v)\b", texto, re.I)
    amp = re.search(r"\b(\d+(?:[.,]\d+)?)\s*(?:amp\w*|ah?)\b", texto, re.I)
    partes = []
    if quimica:
        partes.append(quimica.group(1).strip())
    if volt and 12 <= _numero(volt.group(1)) <= 120:
        partes.append("%s Volt" % volt.group(1))
    if amp and 1 <= _numero(amp.group(1)) <= 300:
        partes.append("%s Ah" % amp.group(1))
    if partes:
        return " / ".join(partes)
    return None


def autonomia_desde(texto):
    """Autonomia publicada: texto y minimo/maximo, o (None, None, None)."""

    def valida(a, b):
        """Descartes numericos: la autonomia real esta entre 5 y 500 km."""
        return (a is not None and b is not None and a >= 5 and b >= 5
                and a <= 500 and b <= 500)

    def numeros_de(cadena):
        rango = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:[-/\u2013\u2014]|to|hasta| y )\s*"
                          r"(\d+(?:[.,]\d+)?)\s*km(?!/h)", cadena, re.I)
        if rango:
            a, b = _numero(rango.group(1)), _numero(rango.group(2))
            if a > b:
                a, b = b, a
            return (rango.group(0), a, b)
        simple = re.search(r"\b(\d+(?:[.,]\d+)?)\s*km(?!/h)", cadena, re.I)
        if simple:
            n = _numero(simple.group(1))
            return simple.group(0), n, n
        return None, None, None

    def cortar(frase):
        return re.split(r"\b(?:rims?|tires?|motor|colour|color)\b",
                        frase, maxsplit=1)[0].strip()

    frases = []
    for m in re.finditer(r"autonom\w*\s*(?:de\s*)?[:\-]?\s*"
                         r"([^\u2022;|\n]{0,60})", texto, re.I):
        frase = re.sub(r"\s+", " ", m.group(1)).strip(":-\u2013\u2014. ")
        frase = frase.replace("\u00a0", " ").strip()
        if frase:
            frases.append(frase)
    for frase in frases:                      # prefiere el rango (40-50 km)
        _, mn, mx = numeros_de(frase)
        if mn is not None and mn != mx and valida(mn, mx):
            return cortar(frase), entero_si_entero(mn), entero_si_entero(mx)
    for frase in frases:
        _, mn, mx = numeros_de(frase)
        if mn is not None and valida(mn, mx):
            return cortar(frase), entero_si_entero(mn), entero_si_entero(mx)
    _, mn, mx = numeros_de(re.sub(r"\s+", " ", texto))
    if valida(mn, mx):
        return None, entero_si_entero(mn), entero_si_entero(mx)
    return None, None, None


def guardar_autonomia(registro, texto_autonomia, a_min, a_max):
    """Anade autonomia al registro solo si hay datos validos."""
    if a_min is None and a_max is None:
        return
    km = texto_autonomia
    if km is None:
        km = "%d km" % a_min if a_min == a_max else "%d–%d km" % (a_min, a_max)
    registro["autonomia_km"] = km
    registro["autonomia_min_km"] = a_min
    registro["autonomia_max_km"] = a_max


def precio_desde_texto(texto):
    """Precio citado dentro del texto del anuncio, en USD o convertido."""
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
    """Marca del fabricante si aparece; si no, generica."""
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
# Guardado
# ------------------------------------------------------------------------------

def guardar(datos):
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


# ------------------------------------------------------------------------------
# Programa principal
# ------------------------------------------------------------------------------

def main():
    sesion = requests.Session()
    sesion.headers["User-Agent"] = UA
    sesion.headers["Accept-Language"] = "es-ES,es;q=0.8,en;q=0.5"

    posibles = candidatos(sesion)
    print("Candidatos electricos en Motos/Bicicletas:", len(posibles))

    relevantes = [a for a in posibles
              for cuerpo in [(a["titulo"] + " " + a["contenido"])]
              if es_el_ectrico(cuerpo)
              and es_un_vehiculo(a["titulo"], a["contenido"])]
    relevantes.sort(key=lambda a: a["fecha"], reverse=True)   # mas recientes primero

    totales_por_tipo = {"Moto electrica": 0, "Bicicleta electrica": 0,
                        "Patinete electrico": 0}
    elegidos = {"Moto electrica": [], "Bicicleta electrica": [],
                "Patinete electrico": []}
    for a in relevantes:
        tipo = tipo_de(a["titulo"])
        a["tipo"] = tipo
        totales_por_tipo[tipo] += 1
        if len(elegidos[tipo]) < MAX_POR_TIPO:
            elegidos[tipo].append(a)

    lista = (elegidos["Moto electrica"] + elegidos["Bicicleta electrica"]
             + elegidos["Patinete electrico"])
    print("Electricos:", len(relevantes), "| elegidos:", len(lista),
          "| por tipo:", totales_por_tipo)

    descartados = {"No electrico / fuera de alcance": len(posibles) - len(relevantes)}
    exceso = sum(max(0, totales_por_tipo[t] - len(elegidos[t]))
                 for t in totales_por_tipo)
    if exceso:
        descartados["Tope de 50 por tipo"] = exceso

    datos = {
        "fuente": "iTENCEL (anuncios clasificados de Cuba)",
        "url": SITIO + "/anuncio-categoria/vehiculos/",
        "fecha": date.today().isoformat(),
        "moneda_original": "mayoria en USD; algunos en CUP (tasa 745 CUP = 1 USD)",
        "anuncios_escaneados": len(posibles),
        "productos_relevantes": len(lista),
        "descartados_por_tipo": descartados,
        "productos": [],
    }
    guardar(datos)

    for i, a in enumerate(lista, 1):
        cuerpo = "%s %s" % (a["titulo"], a["contenido"])
        bateria = bateria_desde(cuerpo)
        texto_aut, a_min, a_max = autonomia_desde(cuerpo)
        precio = precio_desde_texto(cuerpo)
        if precio is None:
            precio = precio_de_ficha(sesion, a["url"])
        if precio is not None and precio < MIN_PRECIO_USD:
            precio = None                # reclamos tipo "1 USD": consultar

        registro = {
            "marca": marca_de(cuerpo),
            "tipo_vehiculo": a["tipo"],
            "precio_usd": precio,
        }
        if bateria:
            registro["bateria"] = bateria
        guardar_autonomia(registro, texto_aut, a_min, a_max)

        datos["productos"].append(registro)
        guardar(datos)

        print("  [%d/%d] %-18s | %s | %s | bateria: %s | autonomia: %s"
              % (i, len(lista), a["tipo"],
                 precio if precio is not None else "?",
                 registro.get("marca"),
                 (bateria or "-")[:44], (texto_aut or "-")[:32]))

    print()
    print("Guardado en:", SALIDA)
    print("Registros:", len(datos["productos"]))


if __name__ == "__main__":
    main()