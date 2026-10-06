# -*- coding: utf-8 -*-
"""Scraper de la tienda VEDCA dentro de Islagrande.

Fuente 2 del proyecto. VEDCA (Vehiculos Electricos del Caribe) publica su
catalogo en islagrande.com y si, a diferencia de Revolico, publica bateria y
autonomia en la ficha de cada producto.

Se guardan unicamente motos, bicicletas y patinetes electricos. Triciclos,
baterias sueltas y neumaticos se descartan.

Salida: data/vedca_islagrande.json  (cabecera con la fuente, luego la lista)
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

BASE = "https://islagrande.com"
TIENDA = BASE + "/marketplace/seller/collection/shop/vedca/"
CATALOGO = TIENDA + "?product_list_limit=48"  # trae los 29 productos en una sola pagina
SALIDA = Path(__file__).resolve().parent / "data" / "vedca_islagrande.json"

# El sitio publica en euros; la autora fijo esta tasa para pasar a USD.
TASA_USD_POR_EUR = 1.13
MAX_PRODUCTOS = 50          # tope de registros por fuente
PAUSA_ENTRE_PAGINAS = 0.8   # segundos entre peticiones
REINTENTOS = 3
TIMEOUT = 60

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# Tipos que interesan, reconocidos por el fragmento de la direccion web.
TIPOS = (
    ("moto-electrica", "Moto electrica"),
    ("bicicleta-electrica", "Bicicleta electrica"),
    ("patinete-electrico", "Patinete electrico"),
    ("patinete", "Patinete electrico"),
    ("scooter", "Patinete electrico"),
)

# Lo que se descarta del catalogo de la tienda.
DESCARTAR = (("triciclo", "Triciclo"), ("bateria", "Bateria"), ("neumatico", "Neumatico"))


# ------------------------------------------------------------------------------
# Utilidades
# ------------------------------------------------------------------------------

def pedir(sesion, url, params=None):
    """GET con reintentos. Si algo falla tres veces, corta con error claro."""
    ultimo = None
    for intento in range(REINTENTOS):
        try:
            r = sesion.get(url, params=params, timeout=TIMEOUT)
            if r.status_code == 200:
                return r.text
            ultimo = "HTTP %s" % r.status_code
        except requests.RequestException as exc:
            ultimo = str(exc)[:120]
        time.sleep(1.5 * (intento + 1))
    raise RuntimeError("No se pudo leer %s (%s)" % (url, ultimo))


def clasificar(url):
    """Devuelve el tipo de vehiculo segun la direccion, o None si no aplica."""
    u = url.lower()
    for fragmento, tipo in TIPOS:
        if fragmento in u:
            return tipo
    return None


def descarte_de(url):
    """Nombre del descarte si la direccion corresponde a algo fuera de alcance."""
    u = url.lower()
    for fragmento, nombre in DESCARTAR:
        if fragmento in u:
            return nombre
    return "Otro"


def texto_plano(html):
    """Quita etiquetas y devuelve el texto tal cual, con las lineas separadas."""
    html = re.sub(r"<br\b[^>]*>", "\n", html, flags=re.I)
    html = re.sub(r"</p\s*>", "\n", html, flags=re.I)
    html = re.sub(r"</li\s*>", "\n", html, flags=re.I)
    html = re.sub(r"<[^>]+>", "", html)
    return unescape(html).replace("\xa0", " ")


def bloque_div(html, desde):
    """Devuelve el interior del primer <div> que sigue en `desde`, bien cerrado."""
    inicio = html.find("<div", desde)
    if inicio < 0:
        return ""
    fin = html.find(">", inicio)
    if fin < 0:
        return ""
    profundo = 1
    pos = fin + 1
    while profundo and pos < len(html):
        abrir = html.find("<div", pos)
        cerrar = html.find("</div>", pos)
        if cerrar < 0:
            break
        if abrir != -1 and abrir < cerrar:
            profundo += 1
            pos = abrir + 4
        else:
            profundo -= 1
            pos = cerrar + 6
    return html[fin + 1:cerrar] if profundo == 0 else ""


def caracteristicas(html):
    """Pasa el bloque de caracteristicas a un diccionario Clave: valor."""
    marco = html.find('class="product attribute description"')
    if marco < 0:
        return {}
    valor = bloque_div(html, marco + 40)
    lineas = texto_plano(valor).splitlines()
    salida = {}
    for linea in lineas:
        linea = linea.strip()
        if not linea or ":" not in linea:
            continue
        clave, _, resto = linea.partition(":")
        clave, resto = clave.strip(), resto.strip()
        if not resto or not 1 < len(clave) <= 60:
            continue
        if clave.lower() not in salida:
            salida[clave] = resto
    return salida


def precio(html):
    """Precio final y moneda tal como los publica el sitio (itemprop offers)."""
    marco = html.find("product-info-price")
    ventana = html[marco:marco + 3000] if marco >= 0 else html
    monto = re.search(r'itemprop="price"\s+content="([\d.]+)"', ventana)
    moneda = re.search(r'itemprop="priceCurrency"\s+content="([A-Z]{3})"', ventana)
    if not monto:
        monto = re.search(r'data-price-amount="([\d.]+)"', ventana)
    if not monto:
        return None, None
    return float(monto.group(1)), (moneda.group(1) if moneda else None)


def disponibilidad(html):
    """Estado de la publicacion: In stock / Out of stock."""
    marco = html.find("product-info-stock-sku")
    ventana = html[marco:marco + 1200] if marco >= 0 else html
    clase = re.search(r'class="stock\s+(available|unavailable)"', ventana)
    texto = re.search(r'<span>([^<]{1,40})</span>', ventana)
    if texto:
        return texto.group(1).strip()
    if clase:
        return "In stock" if clase.group(1) == "available" else "Out of stock"
    return None


def identificador(html, url):
    """SKU del producto; si no tiene, se usa el ultimo tramo de la direccion."""
    m = re.search(r'itemprop="sku"\s*>([^<]+)<', html)
    if m and m.group(1).strip():
        return m.group(1).strip()
    return url.rstrip("/").split("/")[-1].replace(".html", "")


def bateria(caracteristicas):
    """Prioriza lo que diga bateria: tipo, capacidad o la linea completa."""
    exactas = {}
    for clave, valor in caracteristicas.items():
        exactas.setdefault(clave.strip().lower().rstrip("."), valor)
    if "battery" in exactas:
        return exactas["battery"]
    partes = []
    for clave in ("battery type", "battery specifications", "battery capacity",
                  "battery voltage", "bateria"):
        if clave in exactas and exactas[clave] not in partes:
            partes.append(exactas[clave])
    if partes:
        return " ".join(partes)
    for clave, valor in caracteristicas.items():
        if "batter" in clave.lower() or "bater" in clave.lower():
            return valor
    return None


def _numero(cadena):
    return float(cadena.replace(",", "."))


def autonomia(caracteristicas):
    """Autonomia publicada: texto original, y minimo/maximo si vienen en el texto."""
    valor = None
    for clave, texto in caracteristicas.items():
        k = clave.strip().lower()
        if k in ("range", "autonomy", "autonomia", "autonomía", "alcance"):
            valor = texto
            break
    if valor is None:
        for clave, texto in caracteristicas.items():
            if "range" in clave.lower() or "autonom" in clave.lower():
                valor = texto
                break
    if valor is None:
        return None, None, None
    rango = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:[-/]|–|—|to|hasta|a)\s*(\d+(?:[.,]\d+)?)",
                      valor, re.I)
    if rango:
        return valor, _numero(rango.group(1)), _numero(rango.group(2))
    simple = re.search(r"(\d+(?:[.,]\d+)?)\s*km", valor, re.I)
    if simple:
        n = _numero(simple.group(1))
        return valor, n, n
    return valor, None, None


def entero_si_entero(valor):
    """70.0 se guarda como 70; 70.5 se queda como 70.5."""
    if valor is None:
        return None
    return int(valor) if float(valor).is_integer() else valor


# ------------------------------------------------------------------------------
# Catalogo de la tienda
# ------------------------------------------------------------------------------

def catalogo_tienda(sesion):
    """Lista de productos publicados por VEDCA: titulo y direccion."""
    html = pedir(sesion, CATALOGO)
    patron = (r'<h2 class="product name product-item-name"[^>]*>\s*'
              r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>')
    encontrados = re.findall(patron, html, re.S)
    return [(unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", n))).strip(), u)
            for u, n in encontrados]


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
    sesion.headers["Accept-Language"] = "en-US,en;q=0.8,es;q=0.6"

    publicados = catalogo_tienda(sesion)
    print("Productos publicados por VEDCA:", len(publicados))

    seleccion = []
    descartados = {}
    for titulo, url in publicados:
        tipo = clasificar(url)
        if tipo is None:
            nombre = descarte_de(url)
            descartados[nombre] = descartados.get(nombre, 0) + 1
            continue
        seleccion.append((titulo, url, tipo))

    # Sin repetir: si un mismo titulo aparece en dos direcciones, se queda con el primero.
    unicos, vistos = [], set()
    for titulo, url, tipo in seleccion:
        if titulo in vistos:
            continue
        vistos.add(titulo)
        unicos.append((titulo, url, tipo))

    if len(unicos) > MAX_PRODUCTOS:
        print("Aviso: se recorta de", len(unicos), "a", MAX_PRODUCTOS)
        unicos = unicos[:MAX_PRODUCTOS]

    print("Relevantes (motos, bicicletas, patinetes):", len(seleccion),
          "| unicos:", len(unicos), "| descartados:", descartados)

    datos = {
        "fuente": "VEDCA (Islagrande)",
        "url": TIENDA,
        "fecha": date.today().isoformat(),
        "moneda_original": "EUR",
        "tasa_usd_por_eur": TASA_USD_POR_EUR,
        "productos_publicados": len(publicados),
        "productos_relevantes": len(unicos),
        "descartados_por_tipo": descartados,
        "productos": [],
    }
    guardar(datos)

    for i, (titulo, url, tipo) in enumerate(unicos, 1):
        try:
            html = pedir(sesion, url)
        except RuntimeError as exc:
            print("  [%d/%d] FALLO %s" % (i, len(unicos), exc))
            continue

        euros, moneda = precio(html)
        carac = caracteristicas(html)
        texto_aut, a_min, a_max = autonomia(carac)
        if euros is not None:
            euros = round(euros, 2)
            usd = round(euros * TASA_USD_POR_EUR, 2)
        else:
            usd = None

        registro = {
            "id": identificador(html, url),
            "tipo_vehiculo": tipo,
            "marca": "VEDCA",
            "titulo": titulo,
            "url": url,
            "precio_eur": euros,
            "precio_usd": usd,
            "moneda_publicada": moneda,
            "disponibilidad": disponibilidad(html),
            "bateria": bateria(carac),
            "autonomia_km": texto_aut,
            "autonomia_min_km": entero_si_entero(a_min),
            "autonomia_max_km": entero_si_entero(a_max),
            "caracteristicas": carac,
        }
        datos["productos"].append(registro)
        guardar(datos)

        print("  [%d/%d] %-16s %-8s EUR %s | USD %s | bateria: %s | autonomia: %s"
              % (i, len(unicos), tipo, "",
                 euros if euros is not None else "?",
                 usd if usd is not None else "?",
                 (registro["bateria"] or "sin declarar")[:26],
                 (texto_aut or "sin declarar")[:24]))
        time.sleep(PAUSA_ENTRE_PAGINAS)

    print()
    print("Guardado en:", SALIDA)
    print("Registros:", len(datos["productos"]))


if __name__ == "__main__":
    main()
