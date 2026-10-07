# -*- coding: utf-8 -*-
"""Scraper de CubAmerica (envioscubamerica.com).

Fuente 2 del proyecto. Tienda WooCommerce que vende desde el exterior y
envia a Cuba. Publica precios en USD, y en el nombre o la descripcion de
cada producto suele venir la bateria (Volt / Ah) y, a veces, la autonomia.

Se guardan unicamente motos, bicicletas y patinetes electricos. Las
bicimotos se cuentan como bicicleta electrica (decision de la autora).
Triciclos y bicicletas a pedal se descartan.

Salida: data/cubamerica_envios.json  (cabecera con la fuente, luego la lista)
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

API = "https://envioscubamerica.com/wp-json/wc/store/v1/products"
BASE_TIENDA = "https://envioscubamerica.com/categoria-producto/transporte/"
SALIDA = Path(__file__).resolve().parent / "data" / "cubamerica_envios.json"

# Categorias de la tienda que interesan: slug -> etiqueta para la cabecera.
CATEGORIAS = (
    ("motos-electricas", "Motos electricas"),
    ("bicicletas-electricas", "Scooter y Bicicletas electricas"),
)

MAX_PRODUCTOS = 100      # tope de seguridad; aqui entran los 57 sin recortar
PAUSA_ENTRE_PETICIONES = 0.8
REINTENTOS = 3
TIMEOUT = 60

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def pedir_json(sesion, params):
    """GET a la API con reintentos. Devuelve la lista de productos."""
    ultimo = None
    for intento in range(REINTENTOS):
        try:
            r = sesion.get(API, params=params, timeout=TIMEOUT)
            if r.status_code == 200:
                return json.loads(r.content.decode("utf-8-sig"))
            ultimo = "HTTP %s" % r.status_code
        except (requests.RequestException, ValueError) as exc:
            ultimo = str(exc)[:120]
        time.sleep(1.5 * (intento + 1))
    raise RuntimeError("No se pudo leer la API de CubAmerica (%s)" % ultimo)


# ------------------------------------------------------------------------------
# Clasificacion
# ------------------------------------------------------------------------------

def clasificar(nombre):
    """Tipo de vehiculo segun el nombre, o (None, motivo) si no aplica."""
    n = nombre.lower()
    if "triciclo" in n or "tricimoto" in n:
        return None, "Triciclo"
    if "bicimoto" in n or "bimoto" in n:
        return "Bicicleta electrica", None
    if re.search(r"\bmotos?\b", n):
        return "Moto electrica", None
    if "bicicleta" in n or re.search(r"\bbici", n):
        return "Bicicleta electrica", None
    if "scooter" in n or "patinete" in n or "patineta" in n:
        return "Patinete electrico", None
    return None, "Otro"


MARCAS = [
    "windone", "hiboy", "topmaq", "topmax", "bucatti", "izuki",
    "fly racing", "halcon", "panther", "leopard", "rhynox", "hezzo",
    "mikazuki", "cocuyo", "raptor", "volt-x", "volt x", "e-lite",
    "e-track", "e-on", "infinity", "shark x", "brisa", "rayo", "bolt",
    "cross", "solaura", "outraid",
]


def marca_de(nombre):
    """Marca del fabricante si aparece en el nombre; si no, generica."""
    n = nombre.lower()
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
        if trozo:
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

    def numeros_de(cadena):
        rango = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:[-/\u2013\u2014]|to|hasta| y )\s*"
                          r"(\d+(?:[.,]\d+)?)\s*km(?!/h)", cadena, re.I)
        if rango:
            return (rango.group(0), _numero(rango.group(1)),
                    _numero(rango.group(2)))
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
        m, mn, mx = numeros_de(frase)
        if m and mn != mx:
            return cortar(frase), entero_si_entero(mn), entero_si_entero(mx)
    for frase in frases:
        m, mn, mx = numeros_de(frase)
        if m:
            return cortar(frase), entero_si_entero(mn), entero_si_entero(mx)
    m, mn, mx = numeros_de(re.sub(r"\s+", " ", texto))
    if m:
        return m, entero_si_entero(mn), entero_si_entero(mx)
    return None, None, None


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

    crudo = []
    for slug, etiqueta in CATEGORIAS:
        productos = pedir_json(sesion, {"category": slug, "per_page": 100})
        print("Categoria %-32s %3d productos" % (etiqueta, len(productos)))
        crudo += [(slug, p) for p in productos]
        time.sleep(PAUSA_ENTRE_PETICIONES)

    seleccion = []
    descartados = {}
    por_slug = {}
    for slug, p in crudo:
        nombre = unescape(p.get("name") or "").strip()
        por_slug.setdefault(slug, {}).setdefault(nombre, 0)
        por_slug[slug][nombre] += 1
        tipo, motivo = clasificar(nombre)
        if tipo is None:
            descartados[motivo] = descartados.get(motivo, 0) + 1
            continue
        seleccion.append((nombre, p, tipo))

    # Sin repetidos (algun producto figura en dos categorias).
    unicos, vistos = [], set()
    for nombre, p, tipo in seleccion:
        clave = p.get("permalink") or nombre.lower()
        if clave in vistos:
            continue
        vistos.add(clave)
        unicos.append((nombre, p, tipo))

    # Tope de 50 por tipo de vehiculo (decision de la autora).
    MAX_POR_TIPO = 50
    por_tipo = {"Moto electrica": [], "Bicicleta electrica": [],
                "Patinete electrico": []}
    exceso = {}
    for nombre, p, tipo in unicos:
        lista = por_tipo.get(tipo)
        if lista is None:
            continue
        if len(lista) < MAX_POR_TIPO:
            lista.append((nombre, p, tipo))
        else:
            exceso[tipo] = exceso.get(tipo, 0) + 1
    elegidos = (por_tipo["Moto electrica"] + por_tipo["Bicicleta electrica"]
                + por_tipo["Patinete electrico"])
    for tipo, n in exceso.items():
        descartados["Tope 50 (%s)" % tipo] = n

    print("Relevantes:", len(seleccion), "| elegidos:", len(elegidos),
          "| descartados:", descartados)

    datos = {
        "fuente": "CubAmerica (envioscubamerica.com)",
        "url": BASE_TIENDA,
        "fecha": date.today().isoformat(),
        "moneda_original": "USD",
        "categorias_consultadas": dict(CATEGORIAS),
        "productos_relevantes": len(elegidos),
        "descartados_por_tipo": descartados,
        "productos": [],
    }
    guardar(datos)

    for i, (nombre, p, tipo) in enumerate(elegidos, 1):
        precio = p.get("prices") or {}
        minor = precio.get("price") or precio.get("regular_price")
        if minor is not None:
            divisor = 10 ** (precio.get("currency_minor_unit") or 2)
            usd = round(float(minor) / divisor, 2)
        else:
            usd = None

        descripcion = p.get("description") or ""
        texto = unescape(re.sub(r"<[^>]+>", " ", descripcion)).replace("\u00a0", " ")
        purga = "%s\n%s" % (nombre, re.sub(r"[ \t]+", " ", texto))

        bateria = bateria_desde(purga)
        texto_aut, a_min, a_max = autonomia_desde(purga)

        registro = {
            "marca": marca_de(nombre),
            "tipo_vehiculo": tipo,
            "precio_usd": usd,
        }
        if bateria:
            registro["bateria"] = bateria
        if texto_aut:
            registro["autonomia_km"] = texto_aut
            registro["autonomia_min_km"] = a_min
            registro["autonomia_max_km"] = a_max

        datos["productos"].append(registro)
        guardar(datos)

        print("  [%d/%d] %-18s %-8s | %s | bateria: %s | autonomia: %s"
              % (i, len(elegidos), tipo, usd if usd is not None else "?",
                 registro.get("marca"),
                 (bateria or "-")[:44], (texto_aut or "-")[:32]))
        time.sleep(PAUSA_ENTRE_PETICIONES)

    print()
    print("Guardado en:", SALIDA)
    print("Registros:", len(datos["productos"]))


if __name__ == "__main__":
    main()