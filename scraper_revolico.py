# -*- coding: utf-8 -*-
"""
scraper_revolico.py
===================
Proyecto: relacion precio - marca - calidad en los vehiculos electricos
anunciados en Revolico (La Habana).

Que produce este programa:
  data/anuncios_revolico.json  -> 225 anuncios (75 por tipo) listos para importar

Tipos (solo tres, nada de bicimotos ni motos de combustion):
  - Moto electrica
  - Bicicleta electrica
  - Patinete electrico

Reglas de limpieza aplicadas:
  - Solo provincia de La Habana (todos sus municipios)
  - Obligatorio: marca + precio + autonomia.  La bateria se guarda si el
    anuncio la menciona; si no, queda vacia.
  - Precio dentro de un rango realista por tipo (fuera 1 USD, 10 USD, etc.)
  - Fuera anuncios de tienda, con varios productos o precios
  - Fuera anuncios mal elaborados (titulo o descripcion demasiado cortos)
  - Fuera duplicados y precios que contradicen el texto
  - Fuera el mismo vendedor repetido con muchos anuncios

Uso:
    python scraper_revolico.py                  # corrida completa: 75 por tipo
    python scraper_revolico.py --piloto 3       # prueba rapida con 3 por tipo
    python scraper_revolico.py --limite 40      # menos por tipo

Tasa de cambio: 745 CUP = 1 USD
"""
import argparse
import json
import os
import re
import sys
import time
import unicodedata
from collections import defaultdict
from datetime import datetime

import requests

# La consola de Windows no suele ser UTF-8: sin esto, imprimir un anuncio con
# emojis (los hay a montones) rompe el programa.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

# ----------------------------------------------------------------------------
# Configuracion
# ----------------------------------------------------------------------------

TASA_CUP_POR_USD = 745
BASE = "https://www.revolico.com"
BUSCAR = BASE + "/search"

DIR_PROYECTO = os.path.dirname(os.path.abspath(__file__))
CARPETA_DATA = os.path.join(DIR_PROYECTO, "data")
RUTA_JSON = os.path.join(CARPETA_DATA, "anuncios_revolico.json")

ID_LA_HABANA = "1"                # provinceId de La Habana
OBJETIVO_POR_TIPO = 75
MAX_PAGINAS_POR_BUSQUEDA = 12
MAX_ANUNCIOS_POR_VENDEDOR = 2      # el mismo vendedor no puede traer 3+ anuncios
ESPERA = 0.6                       # segundos entre peticiones
PASADAS = 3                        # intentos de lectura por anuncio (fallos de red)

# Cada tipo: palabras de busqueda y rango de precio realista en USD.
TIPOS = {
    "Moto electrica": {
        "busquedas": [
            "moto electrica", "moto electrica 72v",
            "moto electrica nueva", "moto electrica bateria litio",
        ],
        "precio_min": 400,
        "precio_max": 15000,
    },
    "Bicicleta electrica": {
        "busquedas": [
            "bicicleta electrica", "bicicleta electrica plegable",
            "bicicleta", "bicicleta electrica 48v",
        ],
        "precio_min": 150,
        "precio_max": 4000,
    },
    "Patinete electrico": {
        "busquedas": [
            "patinete electrico", "patineta electrica",
            "patinete", "patinete electrico 1000w",
        ],
        "precio_min": 60,
        "precio_max": 2500,
    },
}

CAMPOS = [
    "id", "tipo_vehiculo", "titulo", "url", "marca",
    "precio", "moneda", "autonomia_km", "tipo_bateria",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Palabras del titulo que confirman que el anuncio es del vehiculo buscado.
CONFIRMA = {
    "Moto electrica": re.compile(r"\bmoto", re.IGNORECASE),
    "Bicicleta electrica": re.compile(r"bicicleta|bici\b|cycle", re.IGNORECASE),
    "Patinete electrico": re.compile(r"patin(?:ete|eta)|monopat[ií]n", re.IGNORECASE),
}

# Lo que NO es un vehiculo electrico (tiendas de moviles, ECOFLOW, recambios...).
NO_ES_VEHICULO = re.compile(
    r"movil|celular|smartphone|tablet|laptop|notebook|televis|ecoflow|"
    r"planta\s?solar|panel\s?solar|router|audifono|smart\s?watch|consola|"
    r"playstation|xbox|impresora|camara|drone|licuadora|lavadora|nevera|"
    r"refrigerador|microondas|generador|soldadora|herramienta|motorola|"
    r"repuesto|accesorio|llanta|neumatico|cargador|bateria\s+para|"
    r"bicicleta\s+(?:de\s+)?(?:montada|infantil|ni[ñn]os|recorrido|estatica|"
    r"ejercicio|spinning|gimnasio|ruta|.senderismo|ciclismo|infantil)",
    re.IGNORECASE,
)

# Anuncios de negocio, no de un vehiculo concreto.
PALABRAS_TIENDA = re.compile(
    r"\b(?:tienda|tiendas|vendemos|vendo\s+varios|varios\s+disponibles|"
    r"tenemos\s+(?:disponible|de)|somos\s+tienda|se\s+vende\s+de\s+todo|"
    r"aceptamos\s+encargo|reventa|mayorista|distribuidor)\b",
    re.IGNORECASE,
)

MARCAS = (
    "yoazaky", "vyri", "rimonk", "topmaq", "bucatti", "volta", "vedca", "orix",
    "izuki", "demak", "silvio", "marti", "corban", "iwaki", "zontes", "kvitova",
    "challenger", "evolution", "jmd", "grillo", "maf", "mishozuki", "halcon",
    "ava", "galactica", "midha", "caroma", "oris", "laituning", "motico",
    "okday", "askmy", "bello", "dttzh", "porto", "portobello", "corleone",
    "onebot", "vivamax", "panda", "treck", "galaxy", "jialing", "jinlun",
    "bevomecon", "delux", "soco", "sunra", "ymotor", "levdeo", "fang",
    "bird", "segway", "ninebot", "gotway", "kuake", "fiido", "himo", "trotro",
    "dualstep", "inmotion", "firefly", "ojoy", "carrera", "t4", "t3",
    "voltride", "olux", "ecoco", "xmen", "ufo", "citycar", "apollo", "phoenix",
    "roadster", "yuma", "globus", "mustang", "panther", "maza", "taurus",
    "viking", "anode", "aima", "ruichi", "luen", "lavo", "xpedition", "xp",
    "voltride", "volt ride", "vorta", "mikasuki", "mikasuck", "electra",
    "vado", "evok", "wuyang", "luyuan", "qsmotor", "niu", "super soco",
    # modelos que aparecen en las bicicletas electricas de La Habana
    "cs3", "k1", "t1", "t-1", "a12", "gs3", "viporvive", "murasaki",
    "eskute", "infinity", "x80", "x80 pro", "sport", "bucatt", "s3", "m1",
)

RE_EMOJI = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002190-\U000021FF"
    "\U00002700-\U000027BF"
    "\U00002B00-\U00002BFF"
    "\U0001F1E6-\U0001F1FF"
    "\U0000FE0F"
    "]",
    flags=re.UNICODE,
)
RE_NO_ALFA = re.compile(r"[^a-z0-9 ]+")

# ----------------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------------

SESION = requests.Session()
SESION.headers.update(HEADERS)


def sin_acentos(texto):
    texto = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in texto if not unicodedata.combining(c))


def pedir(url, intentos=2, timeout=12):
    """Pide la pagina. Si falla, no insiste mucho: es preferible saltarse un
    anuncio a perder minutos esperando a un servidor lento."""
    for intento in range(1, intentos + 1):
        try:
            r = SESION.get(url, timeout=timeout)
            if r.status_code == 200:
                return r.text
            print(f"    [HTTP {r.status_code}] {url}", flush=True)
        except requests.RequestException as e:
            print(f"    [reintento {intento}] {type(e).__name__}", flush=True)
        if intento < intentos:
            time.sleep(ESPERA * intento)
    return None


def json_de_la_pagina(html):
    m = re.search(r"<script[^>]*__NEXT_DATA__[^>]*>(.*?)</script>", html, re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return {}


def anuncios_en_json(datos):
    salida = []

    def caminar(d):
        if isinstance(d, dict):
            if d.get("__typename") == "AdType" and d.get("id"):
                salida.append(d)
            for v in d.values():
                if v is not None:
                    caminar(v)
        elif isinstance(d, list):
            for v in d:
                caminar(v)

    caminar(datos)
    return salida


def mapa_de(datos, typename):
    mapa = {}

    def caminar(d):
        if isinstance(d, dict):
            if d.get("__typename") == typename and d.get("id"):
                mapa[str(d["id"])] = d.get("name")
            for v in d.values():
                if v is not None:
                    caminar(v)
        elif isinstance(d, list):
            for v in d:
                caminar(v)

    caminar(datos)
    return mapa


def fecha_dia(iso):
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return iso[:10]


def numero(texto):
    try:
        return round(float(str(texto).replace(",", ".")))
    except (ValueError, TypeError):
        return None


def clave_titulo(titulo):
    """Firma de un titulo para detectar duplicados: sin emojis, sin numeros,
    sin tildes y sin palabras sueltas."""
    t = RE_EMOJI.sub(" ", sin_acentos(titulo or "").lower())
    t = re.sub(r"\b\d+\b", " ", t)
    t = RE_NO_ALFA.sub(" ", t)
    return " ".join(p for p in t.split() if len(p) > 2)


# ----------------------------------------------------------------------------
# Busqueda de candidatos
# ----------------------------------------------------------------------------


def buscar_candidatos(tipo, config, paginas):
    vistos = set()
    candidatos = []
    provincias = {}
    for palabra in config["busquedas"]:
        q = palabra.replace(" ", "+")
        for pagina in range(1, paginas + 1):
            url = f"{BUSCAR}?q={q}&page={pagina}"
            html = pedir(url)
            if not html:
                break
            datos = json_de_la_pagina(html)
            if not provincias:
                provincias = mapa_de(datos, "ProvinceType")
            anuncios = anuncios_en_json(datos)
            if not anuncios:
                break
            nuevos = 0
            for a in anuncios:
                vid = str(a["id"])
                if vid in vistos:
                    continue
                vistos.add(vid)
                candidatos.append({
                    "id": vid,
                    "titulo": a.get("title") or "",
                    "url": BASE + (a.get("permalink") or ""),
                    "precio_original": a.get("price"),
                    "moneda": a.get("currency"),
                    "provincia_id": str(a.get("provinceId")) if a.get("provinceId") else "",
                    "provincia": provincias.get(str(a.get("provinceId"))),
                    "fecha_publicacion": fecha_dia(a.get("updatedOnToOrder")),
                })
                nuevos += 1
            print(f"    [{palabra}] pag {pagina}: {nuevos} nuevos "
                  f"(acumulado {len(candidatos)})", flush=True)
            if nuevos == 0:
                break
            time.sleep(ESPERA)
    candidatos.sort(key=lambda a: a["fecha_publicacion"] or "", reverse=True)
    return candidatos


# ----------------------------------------------------------------------------
# Lectura del anuncio completo
# ----------------------------------------------------------------------------


def leer_anuncio(anuncio):
    """Entra al anuncio y devuelve (descripcion, nombre_vendedor)."""
    html = pedir(anuncio["url"], intentos=2, timeout=10)
    if not html:
        return None, None
    datos = json_de_la_pagina(html)
    for nodo in anuncios_en_json(datos):
        if str(nodo.get("id")) == anuncio["id"]:
            vendedor = ""
            autor = nodo.get("user") or nodo.get("advertiser") or {}
            if isinstance(autor, dict):
                vendedor = autor.get("name") or autor.get("displayName") or ""
            if not vendedor:
                vendedor = nodo.get("userName") or nodo.get("sellerName") or ""
            return nodo.get("description"), vendedor
    return None, None


# ----------------------------------------------------------------------------
# Extraccion de datos
# ----------------------------------------------------------------------------

RE_AUTONOMIA_ANTES = re.compile(
    r"(?:autonomia|recorrido|rango|distancia)\D{0,25}?(\d{1,3})(?:\s*-\s*(\d{1,3}))?"
    r"\s*(?:kms?|kilometros?|km)",
    re.IGNORECASE,
)
RE_AUTONOMIA_DESPUES = re.compile(
    r"(\d{1,3})(?:\s*-\s*(\d{1,3}))?\s*(?:kms?|kilometros?|km)\s*(?:de\s+)?"
    r"(?:autonomia|recorrido)",
    re.IGNORECASE,
)
RE_AUTONOMIA_SIMPLE = re.compile(
    r"(?:autonomia|recorrido|rango|distancia)\D{0,25}?(\d{1,3})\b", re.IGNORECASE
)
RE_PRECIO_EN_TEXTO = re.compile(
    r"(\d[\d\.,]*)\s*(usd|mlc|cup|\$)", re.IGNORECASE
)


def extraer_marca(texto):
    t = sin_acentos(texto).lower()
    for marca in MARCAS:
        if re.search(r"\b" + re.escape(marca) + r"\b", t):
            return marca.capitalize()
    return None


def extraer_autonomia(texto):
    t = sin_acentos(texto or "")
    for patron in (RE_AUTONOMIA_ANTES, RE_AUTONOMIA_DESPUES):
        m = patron.search(t)
        if m:
            v = numero(m.group(1))
            if v and 5 <= v <= 500:
                return v
    m = RE_AUTONOMIA_SIMPLE.search(t)
    if m:
        v = numero(m.group(1))
        if v and 5 <= v <= 500:
            return v
    return None


def extraer_tipo_bateria(texto):
    t = sin_acentos(texto).lower()
    if re.search(r"lifepo4|li-?ion|ion de litio|litio|lithium", t):
        return "Litio"
    if re.search(r"\bgel\b|\bagm\b|sealed|sellada", t):
        return "Gel"
    if re.search(r"\bplomo\b|acido|\bpb\b", t):
        return "Plomo"
    return None


def precio_en_usd(precio, moneda):
    if precio is None:
        return None
    try:
        valor = float(precio)
    except (TypeError, ValueError):
        return None
    if valor <= 0:
        return None
    if moneda in ("USD", "MLC"):
        return round(valor, 2)
    if moneda == "CUP":
        return round(valor / TASA_CUP_POR_USD, 2)
    return None


def contradice_precio(texto, usd):
    """True si el texto menciona otro precio muy distinto al publicado."""
    precios = []
    for m in RE_PRECIO_EN_TEXTO.finditer(texto or ""):
        v = numero(m.group(1))
        moneda = m.group(2).lower()
        if v is None:
            continue
        if moneda in ("usd", "mlc", "$"):
            precios.append(v)
        elif moneda == "cup":
            precios.append(round(v / TASA_CUP_POR_USD, 2))
    otros = [p for p in precios if abs(p - usd) / max(usd, 1) > 0.5]
    return bool(otros)


def parece_tienda(titulo, descripcion):
    texto = (titulo or "") + " " + (descripcion or "")
    if PALABRAS_TIENDA.search(texto):
        return True
    if len(set(RE_PRECIO_EN_TEXTO.findall(texto))) > 1:
        precios = len(re.findall(r"\d[\d\.,]*\s*(?:usd|mlc|cup|\$)", texto, re.IGNORECASE))
        if precios > 3:
            return True
    return False


# ----------------------------------------------------------------------------
# Filtro de calidad
# ----------------------------------------------------------------------------

MOTIVOS = {
    "fuera_de_la_habana": 0,
    "no_es_el_vehiculo": 0,
    "precio_irreal": 0,
    "contradiccion_precio": 0,
    "sin_marca": 0,
    "sin_autonomia": 0,
    "anuncio_tienda": 0,
    "mal_elaborado": 0,
    "vendedor_repetido": 0,
    "duplicado": 0,
}

# Titulos de ejemplo de cada motivo de rechazo (para ampliar listas si hace falta).
EJEMPLOS = defaultdict(list)


def revisar(anuncio, descripcion, vendedor, tipo, config, vistos_titulos, conteo_vendedor):
    """Devuelve (registro, True) si el anuncio entra al dataset."""
    titulo = anuncio["titulo"]

    if anuncio["provincia_id"] != ID_LA_HABANA:
        return None, "fuera_de_la_habana"
    if not CONFIRMA[tipo].search(titulo):
        return None, "no_es_el_vehiculo"
    if NO_ES_VEHICULO.search(titulo):
        return None, "no_es_el_vehiculo"

    texto = titulo + " " + (descripcion or "")
    if len(titulo.strip()) < 15:
        return None, "mal_elaborado"
    if not descripcion or len(descripcion.strip()) < 40:
        return None, "mal_elaborado"

    if parece_tienda(titulo, descripcion):
        return None, "anuncio_tienda"

    usd = precio_en_usd(anuncio["precio_original"], anuncio["moneda"])
    if usd is None or not (config["precio_min"] <= usd <= config["precio_max"]):
        return None, "precio_irreal"
    if contradice_precio(texto, usd):
        return None, "contradiccion_precio"

    marca = extraer_marca(texto)
    if not marca:
        return None, "sin_marca"
    autonomia = extraer_autonomia(texto)
    if not autonomia:
        return None, "sin_autonomia"

    clave = clave_titulo(titulo)
    if clave and clave in vistos_titulos:
        return None, "duplicado"
    if vendedor and conteo_vendedor.get(vendedor, 0) >= MAX_ANUNCIOS_POR_VENDEDOR:
        return None, "vendedor_repetido"

    registro = {
        "id": anuncio["id"],
        "tipo_vehiculo": tipo,
        "titulo": titulo.strip(),
        "url": anuncio["url"],
        "marca": marca,
        "precio": usd,
        "moneda": anuncio["moneda"],
        "autonomia_km": autonomia,
        "tipo_bateria": extraer_tipo_bateria(texto) or "",
    }
    return registro, "aceptado"


# ----------------------------------------------------------------------------
# Guardado (siempre ordenado)
# ----------------------------------------------------------------------------


def ordenar(anuncios):
    return sorted(
        anuncios,
        key=lambda a: (a["tipo_vehiculo"], a["precio"], a["titulo"].lower()),
    )


def guardar(anuncios):
    os.makedirs(CARPETA_DATA, exist_ok=True)
    ordenados = ordenar(anuncios)
    with open(RUTA_JSON, "w", encoding="utf-8") as f:
        json.dump({"anuncios": ordenados}, f, ensure_ascii=False, indent=2)


def cargar():
    try:
        with open(RUTA_JSON, encoding="utf-8") as f:
            return json.load(f)["anuncios"]
    except (OSError, ValueError, KeyError):
        return []



# ----------------------------------------------------------------------------
# Revision del dataset ya guardado
# ----------------------------------------------------------------------------


def revisar_guardados():
    """
    Vuelve a leer cada anuncio guardado y le aplica los filtros actuales.
    Sirve para corregir el dataset cuando cambian las reglas (por ejemplo, si
    se detecta una marca que no existe) sin volver a scrapear desde cero.
    Los anuncios que ya no pasan los filtros se eliminan; despues se puede
    volver a lanzar el scraping para reponer los que falten.
    """
    anuncios = cargar()
    if not anuncios:
        print("No hay anuncios en el JSON.", flush=True)
        return

    print(f"Revisando {len(anuncios)} anuncios con los filtros actuales...\n", flush=True)
    id_veces = defaultdict(int)
    vistos_titulos = defaultdict(set)
    marca_veces = defaultdict(int)
    quedan = []
    eliminados = defaultdict(int)
    ejemplos = defaultdict(int)

    for i, a in enumerate(anuncios, 1):
        tipo = a["tipo_vehiculo"]
        if tipo not in TIPOS:
            eliminados["tipo_desconocido"] += 1
            continue
        if id_veces[a["id"]]:
            eliminados["id_repetido"] += 1     # el mismo anuncio en dos categorias
            continue
        if clave_titulo(a["titulo"]) in vistos_titulos[tipo]:
            eliminados["duplicado"] += 1
            continue

        descripcion, vendedor = leer_anuncio({"id": a["id"], "url": a["url"]})
        time.sleep(ESPERA)
        if descripcion is None:
            # fallo de red: el anuncio se queda como esta, no se descarta por eso
            id_veces[a["id"]] += 1
            vistos_titulos[tipo].add(clave_titulo(a["titulo"]))
            quedan.append(a)
            continue

        original = a["precio"] * TASA_CUP_POR_USD if a["moneda"] == "CUP" else a["precio"]
        candidato = {
            "id": a["id"],
            "titulo": a["titulo"],
            "url": a["url"],
            "precio_original": original,
            "moneda": a["moneda"],
            "provincia_id": ID_LA_HABANA,
            "provincia": "La Habana",
        }
        registro, motivo = revisar(candidato, descripcion, vendedor, tipo,
                                   TIPOS[tipo], set(), dict())
        if motivo != "aceptado":
            eliminados[motivo] += 1
            if ejemplos[motivo] < 8:
                ejemplos[motivo] += 1
                print(f"     - {motivo}: {RE_EMOJI.sub(' ', a['titulo'])[:60]} "
                      f"(marca: {a['marca']})", flush=True)
            continue

        id_veces[a["id"]] += 1
        vistos_titulos[tipo].add(clave_titulo(registro["titulo"]))
        marca_veces[registro["marca"]] += 1
        quedan.append(registro)
        if i % 20 == 0:
            print(f"  {i}/{len(anuncios)} revisados, {len(quedan)} siguen validos", flush=True)

    guardar(quedan)
    print(f"\nAnuncios que pasan los filtros: {len(quedan)}", flush=True)
    for tipo in TIPOS:
        print(f"  {tipo}: {sum(1 for a in quedan if a['tipo_vehiculo'] == tipo)}", flush=True)
    print(f"Eliminados: { {k: v for k, v in eliminados.items() if v} }", flush=True)


# ----------------------------------------------------------------------------
# Programa principal
# ----------------------------------------------------------------------------


def scraping(limite=None, piloto=None):
    objetivo = piloto or limite or OBJETIVO_POR_TIPO
    guardados = cargar()
    if guardados:
        print(f"Continuando desde una corrida anterior: {len(guardados)} anuncios", flush=True)

    # un anuncio no puede estar en dos categorias a la vez
    ids_guardados = {a["id"] for a in guardados}

    for tipo, config in TIPOS.items():
        ya_de_tipo = [a for a in guardados if a["tipo_vehiculo"] == tipo]
        if len(ya_de_tipo) >= objetivo:
            print(f"\n=== {tipo}: ya hay {len(ya_de_tipo)}, no busco mas ===", flush=True)
            continue

        print(f"\n=== {tipo} (objetivo {objetivo}) ===", flush=True)
        print("  1) buscando anuncios...", flush=True)
        paginas = 2 if piloto else MAX_PAGINAS_POR_BUSQUEDA
        candidatos = buscar_candidatos(tipo, config, paginas)
        print(f"  candidatos: {len(candidatos)}", flush=True)

        aceptados = ya_de_tipo
        ids = set(ids_guardados)
        vistos_titulos = {clave_titulo(a["titulo"]) for a in guardados}
        conteo_vendedor = defaultdict(int)
        print("  2) leyendo y depurando anuncios...", flush=True)

        revisados = 0
        sin_leer = 0
        pendientes = list(candidatos)
        for pasada in range(1, PASADAS + 1):
            if len(aceptados) >= objetivo or not pendientes:
                break
            if pasada > 1:
                print(f"    reintento {pasada}: {len(pendientes)} anuncios sin leer", flush=True)
            seguir = []
            for candidato in pendientes:
                if len(aceptados) >= objetivo:
                    break
                if candidato["id"] in ids:
                    continue
                revisados += 1
                descripcion, vendedor = leer_anuncio(candidato)
                time.sleep(ESPERA)
                if descripcion is None:
                    seguir.append(candidato)      # fallo de red: se reintenta
                    continue
                registro, motivo = revisar(
                    candidato, descripcion, vendedor, tipo, config,
                    vistos_titulos, conteo_vendedor,
                )
                if motivo != "aceptado":
                    MOTIVOS[motivo] += 1
                    if len(EJEMPLOS[motivo]) < 20:
                        EJEMPLOS[motivo].append(
                            RE_EMOJI.sub(" ", candidato["titulo"])[:60]
                        )
                    continue

                aceptados.append(registro)
                ids.add(registro["id"])
                ids_guardados.add(registro["id"])
                vistos_titulos.add(clave_titulo(registro["titulo"]))
                if vendedor:
                    conteo_vendedor[vendedor] += 1
                guardados.append(registro)
                guardar(guardados)
                if len(aceptados) % 10 == 0:
                    print(f"    {tipo}: {len(aceptados)}/{objetivo} ({revisados} revisados)",
                          flush=True)
            pendientes = seguir
        sin_leer = len(pendientes)

        print(f"  {tipo}: {len(aceptados)}/{objetivo} guardados ({revisados} revisados)",
              flush=True)
        print(f"  descartados: { {k: v for k, v in MOTIVOS.items() if v} }", flush=True)
        if sin_leer:
            print(f"  sin poder leer (fallo de red): {sin_leer}", flush=True)
        if EJEMPLOS.get("sin_marca"):
            print("  ejemplos de anuncios sin marca detectada:", flush=True)
            for t in EJEMPLOS["sin_marca"][:12]:
                limpio = RE_EMOJI.sub("", t).strip()
                print(f"     - {limpio}", flush=True)
        MOTIVOS.clear()
        MOTIVOS.update({k: 0 for k in
                        ("fuera_de_la_habana", "no_es_el_vehiculo", "precio_irreal",
                         "contradiccion_precio", "sin_marca", "sin_autonomia",
                         "anuncio_tienda", "mal_elaborado", "vendedor_repetido",
                         "duplicado")})

    guardar(guardados)
    print(f"\nTotal en el JSON: {len(guardados)}", flush=True)
    for tipo in TIPOS:
        print(f"  {tipo}: {sum(1 for a in guardados if a['tipo_vehiculo'] == tipo)}", flush=True)
    print(f"Archivo: {RUTA_JSON}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper de vehiculos electricos en Revolico")
    parser.add_argument("--limite", type=int, default=None,
                        help="anuncios por tipo (por defecto 75)")
    parser.add_argument("--piloto", type=int, default=None,
                        help="prueba rapida: N anuncios por tipo")
    parser.add_argument("--revisar", action="store_true",
                        help="vuelve a aplicar los filtros a los anuncios ya guardados")
    args = parser.parse_args()
    try:
        if args.revisar:
            revisar_guardados()
        else:
            scraping(limite=args.limite, piloto=args.piloto)
    except KeyboardInterrupt:
        print("\nSe detuvo el programa.", file=sys.stderr)
        sys.exit(130)