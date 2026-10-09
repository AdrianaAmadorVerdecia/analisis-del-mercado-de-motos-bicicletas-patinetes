# -*- coding: utf-8 -*-
"""Normalizacion de los datasets de las fuentes 2, 3 y 4.

Deja cada producto con SOLO estas claves:
  marca, tipo_vehiculo, precio_usd, autonomia_max_km  (obligatorias)
  bateria (opcional, dato corto: quimica / voltaje / capacidad)
Se eliminan los textos largos, los emojis y las claves sobrantes, se quitan los
registros que no cumplan las tres caracteristicas obligatorias y se aplica el
tope de 50 por tipo de vehiculo.

Uso:  python normalizar.py
"""

import json
import re
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"

MAX_POR_TIPO = 50
MIN_PRECIO_USD = 100

FUENTES = (
    "vedca_islagrande.json",
    "cubamerica_envios.json",
    "itencel_anuncios.json",
)

EMOJIS = re.compile(
    "[\U0001F000-\U0001FAFF\u2300-\u27BF\u2B00-\u2BFF\u2600-\u26FF\uFE0F]")
QUIMICA = re.compile(
    r"(lifepo4|li[-\s]?ion|lithium(?:[-\s]?ion)?|litio|lib|gel|agm|plomo|"
    r"lead(?:[-\s]?acid)?|nicd|nimh)", re.I)


def _numero(cadena):
    return float(cadena.replace(",", "."))


def entero_si_entero(valor):
    valor = round(valor, 2)
    return int(valor) if float(valor).is_integer() else valor


def bateria_corta(texto):
    """Dato corto de bateria a partir de cualquier texto: "Litio 60V / 30Ah"."""
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


def autonomia_max(registro):
    """Autonomia maxima numerica del registro, si es plausible (5-500 km)."""
    for clave in ("autonomia_max_km", "autonomia_max", "a_max"):
        valor = registro.get(clave)
        if isinstance(valor, (int, float)):
            valor = entero_si_entero(valor)
        elif isinstance(valor, str) and \
                re.match(r"^\d+(?:[.,]\d+)?$", valor.strip()):
            try:
                valor = entero_si_entero(float(valor.strip().replace(",", ".")))
            except ValueError:
                valor = None
        else:
            valor = None
        if valor is not None and 5 <= valor <= 500:
            return valor
    texto = registro.get("autonomia_km") or registro.get("autonomia") or ""
    if texto:
        numeros = [float(x.replace(",", "."))
                   for x in re.findall(r"\d+(?:[.,]\d+)?\s*km", str(texto), re.I)]
        numeros = [n for n in numeros if 5 <= n <= 500]
        if numeros:
            return entero_si_entero(max(numeros))
    return None


def producto_limpio(registro):
    """Devuelve el registro minimo o None si falta alguna obligatoria."""
    marca = (registro.get("marca") or "").strip()
    tipo = (registro.get("tipo_vehiculo") or "").strip()
    precio = registro.get("precio_usd")
    try:
        precio = round(float(precio), 2)
    except (TypeError, ValueError):
        precio = None
    auto = autonomia_max(registro)
    if not marca or not tipo or precio is None or precio < MIN_PRECIO_USD \
            or auto is None:
        return None
    limpio = {
        "marca": marca,
        "tipo_vehiculo": tipo,
        "precio_usd": precio,
        "autonomia_max_km": auto,
    }
    bateria = bateria_corta(registro.get("bateria"))
    if bateria:
        limpio["bateria"] = bateria
    return limpio


def normalizar(archivo):
    ruta = DATA / archivo
    datos = json.load(open(ruta, encoding="utf-8"))
    originales = datos["productos"]
    producto_tipo = producto_limpio

    en_tope = {}
    final, descartados = [], {}
    for reg in originales:
        limpio = producto_tipo(reg)
        if limpio is None:
            descartados["Sin marca/precio/autonomia"] = \
                descartados.get("Sin marca/precio/autonomia", 0) + 1
            continue
        tipo = limpio["tipo_vehiculo"]
        en_tope[tipo] = en_tope.get(tipo, 0) + 1
        if en_tope[tipo] > MAX_POR_TIPO:
            descartados["Tope de %d por tipo" % MAX_POR_TIPO] = \
                descartados.get("Tope de %d por tipo" % MAX_POR_TIPO, 0) + 1
            continue
        final.append(limpio)

    datos["productos"] = final
    datos["productos_relevantes"] = len(final)
    datos["total_originales"] = len(originales)
    datos["descartados_por_tipo"] = descartados
    json.dump(datos, open(ruta, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("%-30s %d -> %d | por tipo: %s"
          % (archivo, len(originales), len(final),
             {t: sum(1 for x in final if x["tipo_vehiculo"] == t)
              for t in sorted(set(x["tipo_vehiculo"] for x in final))}))
    return len(final)


if __name__ == "__main__":
    total = 0
    for f in FUENTES:
        total += normalizar(f)
    print("TOTAL:", total)