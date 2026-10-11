"""Genera `interactivo.html`: un explorador interactivo del estudio.

Reune los productos ya analizados de Internet y Mercado y construye una pagina
HTML autocontenida con Plotly en la que cualquier persona escribe un
presupuesto y ve, al instante, en que fuente (Internet o Mercado) y con que tipo
de vehiculo le conviene comprar, y cual es la mejor opcion de cada caso.

No dibuja nubes de puntos: compara con barras la mayor autonomia alcanzable por
tipo y fuente, y resume la mejor opcion en tarjetas.

Se puede abrir en cualquier navegador y tambien incrustar en el notebook.
"""

from __future__ import annotations

import json
from pathlib import Path

import analisis as a

RAIZ = Path(__file__).resolve().parent
DESTINO = RAIZ / "interactivo.html"

FUENTES = (("Internet", "#2563EB"), ("Mercado", "#EA580C"))


def datos_productos() -> list[dict]:
    """Productos de Internet y Mercado con tipo, fuente, sitio, precio y autonomia."""
    return [{
        "tipo": a.ETIQUETAS[p["tipo"]],
        "marca": p["marca"],
        "fuente": p["fuente"],
        "sitio": p["sitio"],
        "precio": p["precio"],
        "autonomia": p["autonomia"],
    } for p in a.productos_todos()]


def empaquetar() -> dict:
    return {
        "productos": datos_productos(),
        "tipos": a.COLOR_TIPO,
        "orden": [a.ETIQUETAS[t] for t in a.ORDEN],
        "fuentes": [{"nombre": f, "color": c} for f, c in FUENTES],
        "presupuesto": a.PRESUPUESTO_LUCY,
    }


def generar(destino: Path = DESTINO) -> Path:
    datos = empaquetar()
    html = PLANTILLA.replace("/*__DATA__*/", json.dumps(datos, ensure_ascii=False))
    destino.write_text(html, encoding="utf-8")
    # Copia para GitHub Pages (se sirve como pagina web en la raiz del sitio).
    docs = RAIZ / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "index.html").write_text(html, encoding="utf-8")
    (docs / ".nojekyll").write_text("", encoding="utf-8")
    return destino


PLANTILLA = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Explorador · Vehículos eléctricos en La Habana</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js" charset="utf-8"></script>
<style>
  :root { --tinta:#0f172a; --gris:#6b7280; --borde:#e5e7eb; --fondo:#f4f6fa; }
  * { box-sizing:border-box; }
  body { margin:0; padding:28px 16px 60px; background:var(--fondo); color:var(--tinta);
         font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }
  .wrap { max-width:1000px; margin:0 auto; }
  header { text-align:center; margin-bottom:26px; }
  header h1 { font-size:30px; margin:0 0 8px; letter-spacing:-.02em; }
  header p { margin:0 auto; max-width:640px; color:var(--gris); font-size:15px; line-height:1.5; }
  .card { background:#fff; border:1px solid var(--borde); border-radius:16px;
          padding:22px 24px 18px; margin-bottom:22px;
          box-shadow:0 6px 20px rgba(15,23,42,.05); }
  .card h2 { font-size:20px; margin:0 0 4px; }
  .card h3 { font-size:14px; text-transform:uppercase; letter-spacing:.04em;
             color:var(--gris); margin:22px 0 10px; }
  .sub { color:var(--gris); font-size:14px; margin:0 0 14px; line-height:1.5; }
  .controles { display:flex; flex-wrap:wrap; align-items:center; gap:14px; margin:6px 0 18px; }
  .controles label { font-weight:600; font-size:15px; }
  .controles input[type=number] { width:130px; padding:9px 12px; font-size:17px;
          font-weight:700; border:1.5px solid var(--borde); border-radius:10px; color:var(--tinta); }
  .controles input[type=range] { flex:1; min-width:180px; accent-color:#1d6fe0; }
  .controles button { padding:9px 16px; font-size:14px; font-weight:600; cursor:pointer;
          border:none; border-radius:10px; background:#1d6fe0; color:#fff; }
  .controles button:hover { background:#155bc0; }
  .resumen { font-size:17px; line-height:1.6; background:#f0f6ff; border:1px solid #d6e6ff;
          border-radius:12px; padding:14px 16px; margin-bottom:16px; }
  .resumen b { color:#0f172a; }
  .resumen .lin { display:block; }
  .opciones { display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr));
          gap:12px; }
  .op { border:1px solid var(--borde); border-radius:12px; padding:12px 14px; background:#fbfcfe; }
  .op h4 { margin:0 0 6px; font-size:14px; display:flex; align-items:center; gap:8px; }
  .op h4 .punto { width:11px; height:11px; border-radius:50%; display:inline-block; }
  .op p { margin:2px 0; font-size:13.5px; color:#374151; line-height:1.45; }
  .op-gana { border-color:#1d6fe0; background:#f0f6ff; box-shadow:0 0 0 2px #d6e6ff inset; }
  .op-gana h4 .tag { font-size:10.5px; text-transform:uppercase; letter-spacing:.04em;
          background:#1d6fe0; color:#fff; border-radius:6px; padding:2px 7px; margin-left:auto; }
  .op-vacia { opacity:.6; }
  .plot { width:100%; }
  footer { text-align:center; color:var(--gris); font-size:12.5px; margin-top:24px; line-height:1.6; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>¿Dónde y qué te conviene comprar?</h1>
    <p>Escribe cuánto puedes gastar y el explorador cruza los precios y la autonomía
       de las motos, bicicletas y patinetes eléctricos anunciados en La Habana, tanto
       en Internet (Revolico e iTENCEL) como en el mercado de importación
       (VEDCA y CubAmerica).</p>
  </header>

  <section class="card">
    <h2>Tu presupuesto</h2>
    <p class="sub">Con ese dinero, la página te dice en qué <b>fuente</b> conviene
       comprar, con qué <b>tipo de vehículo</b> llegas más lejos y cuál es la
       <b>mejor opción</b> de cada caso.</p>
    <div class="controles">
      <label for="presupuesto">Presupuesto (USD):</label>
      <input id="presupuesto" type="number" min="100" max="6000" step="50">
      <input id="rango" type="range" min="100" max="6000" step="50">
      <button id="btn1500" type="button">Lucy: 1.500 USD</button>
    </div>
    <div id="resumen" class="resumen"></div>
    <div id="comparacion" class="plot"></div>
    <h3>Mejor opción por fuente</h3>
    <div id="fuentes" class="opciones"></div>
    <h3>Mejor opción por tipo de vehículo</h3>
    <div id="tipos" class="opciones"></div>
  </section>

  <footer>
    Fuentes: Revolico e iTENCEL (Internet) y VEDCA y CubAmerica (Mercado).
    Precios en USD (745 CUP = 1 USD).<br>
    Trabajo de Ciencia de Datos · MATCOM, Universidad de La Habana.
  </footer>
</div>

<script>
const DATA = /*__DATA__*/;
const ORDEN = DATA.orden;
const TIPOS = DATA.tipos;
const FUENTES = DATA.fuentes;
const PRODUCTOS = DATA.productos;

const fmt = n => Math.round(n).toLocaleString("es-ES");
const USD_KM = p => p.precio / p.autonomia;
const plural = (n, uno, muchos) => n + " " + (n === 1 ? uno : muchos);
const mejorDe = arr => arr.reduce((x, p) => USD_KM(p) < USD_KM(x) ? p : x);
const maxDe = (arr, f) => Math.max.apply(null, arr.map(f));

const layoutBase = {
  paper_bgcolor:"#fff", plot_bgcolor:"#fff",
  font:{color:"#374151", size:12.5},
  margin:{l:60, r:22, t:14, b:48},
  hoverlabel:{bgcolor:"#fff", bordercolor:"#d1d5db", font:{color:"#0f172a", size:12.5}},
};

/* Barras: mayor autonomía alcanzable por tipo y fuente. */
function dibujarComparacion(dentro){
  const traces = FUENTES.map(f => {
    const y = ORDEN.map(tipo => {
      const s = dentro.filter(p => p.fuente === f.nombre && p.tipo === tipo);
      return s.length ? Math.max.apply(null, s.map(p => p.autonomia)) : null;
    });
    return {
      x: ORDEN, y: y, type: "bar", name: f.nombre,
      marker: { color: f.color },
      text: y.map(v => v == null ? "" : v + " km"), textposition: "outside",
      cliponaxis: false,
      hovertemplate: "%{x} · " + f.nombre + "<br>Hasta %{y} km<extra></extra>",
    };
  });
  const layout = Object.assign({}, layoutBase, {
    height: 400, barmode: "group",
    xaxis: { title: "" },
    yaxis: { title: "Autonomía máxima alcanzable (km)", gridcolor: "#eef1f4" },
    legend: { orientation: "h", y: 1.16, x: 0 },
  });
  Plotly.react("comparacion", traces, layout, { responsive:true, displaylogo:false });
}

const inputN = document.getElementById("presupuesto");
const inputR = document.getElementById("rango");
const resumen = document.getElementById("resumen");
const divFuentes = document.getElementById("fuentes");
const divTipos = document.getElementById("tipos");

function tarjeta(titulo, color, sub, gana){
  return '<div class="op' + (gana ? " op-gana" : "") + '">' +
    '<h4>' + (color ? '<span class="punto" style="background:' + color + '"></span>' : "") +
    titulo + (gana ? '<span class="tag">más conviene</span>' : "") + '</h4>' + sub + '</div>';
}

function resumenDe(dentro){
  if (!dentro.length){
    return '<p>Ninguna opción alcanza con este presupuesto.</p>';
  }
  const lejos = dentro.reduce((x, p) => p.autonomia > x.autonomia ? p : x);
  const rel = mejorDe(dentro);
  return '<p><b>Más lejos:</b> ' + lejos.marca + ' · ' + lejos.sitio + '</p>' +
    '<p>' + lejos.autonomia + ' km por $' + fmt(lejos.precio) + '</p>' +
    '<p><b>Menor $/km:</b> ' + rel.marca + ' · ' + rel.sitio + ' ($' +
    USD_KM(rel).toFixed(1) + '/km)</p>' +
    '<p>' + plural(dentro.length, "opción", "opciones") + '</p>';
}

function actualizar(){
  let B = parseFloat(inputN.value);
  if (!isFinite(B)) B = 0;
  B = Math.max(0, B);
  const dentro = PRODUCTOS.filter(p => p.precio <= B);

  if (!dentro.length){
    resumen.innerHTML = "Con <b>$" + fmt(B) + "</b> no alcanza ningún vehículo " +
      "con autonomía publicada entre los analizados.";
    divFuentes.innerHTML = "";
    divTipos.innerHTML = "";
    Plotly.react("comparacion", [], Object.assign({}, layoutBase, {
      height:400, barmode:"group", xaxis:{title:""},
      yaxis:{title:"Autonomía máxima alcanzable (km)"},
    }), { responsive:true, displaylogo:false });
    return;
  }

  // Fuente y tipo donde más lejos se llega con ese presupuesto.
  const porFuente = FUENTES.map(f => ({
    f: f, dentro: dentro.filter(p => p.fuente === f.nombre)
  })).filter(o => o.dentro.length);
  const fuenteGana = porFuente.reduce((a, b) => {
    const ma = maxDe(a.dentro, p => p.autonomia), mb = maxDe(b.dentro, p => p.autonomia);
    if (ma !== mb) return ma > mb ? a : b;
    return USD_KM(mejorDe(a.dentro)) <= USD_KM(mejorDe(b.dentro)) ? a : b;
  });

  const porTipo = ORDEN.map(t => ({
    tipo: t, dentro: dentro.filter(p => p.tipo === t)
  })).filter(o => o.dentro.length);
  const tipoRinde = porTipo.reduce((a, b) =>
    maxDe(a.dentro, p => p.autonomia) >= maxDe(b.dentro, p => p.autonomia) ? a : b);

  const mejorAlcance = dentro.reduce((x, p) => p.autonomia > x.autonomia ? p : x);

  resumen.innerHTML =
    '<span class="lin">Con <b>$' + fmt(B) + '</b> hay <b>' +
    plural(dentro.length, "vehículo", "vehículos") + '</b> a tu alcance.</span>' +
    '<span class="lin">Donde más lejos llegas es en <b>' + fuenteGana.f.nombre +
    '</b>. El tipo que más rinde es <b>' + tipoRinde.tipo + '</b> (hasta <b>' +
    maxDe(tipoRinde.dentro, p => p.autonomia) + ' km</b>).</span>' +
    '<span class="lin"><b>La que más lejos te lleva:</b> ' + mejorAlcance.marca +
    ' · ' + mejorAlcance.sitio + ' (' + mejorAlcance.tipo.toLowerCase() +
    '), $' + fmt(mejorAlcance.precio) + ' con ' + mejorAlcance.autonomia +
    ' km.</span>';

  divFuentes.innerHTML = FUENTES.map(f => {
    const d = dentro.filter(p => p.fuente === f.nombre);
    return tarjeta(f.nombre, f.color, resumenDe(d),
                   fuenteGana.f.nombre === f.nombre);
  }).join("");

  divTipos.innerHTML = ORDEN.map(tipo => {
    const d = dentro.filter(p => p.tipo === tipo);
    return tarjeta(tipo, TIPOS[tipo], resumenDe(d), false);
  }).join("");

  dibujarComparacion(dentro);
}

function fijar(valor){
  let v = Math.round(valor / 50) * 50;
  v = Math.max(100, Math.min(6000, v));
  inputN.value = v; inputR.value = v;
  actualizar();
}

inputN.addEventListener("input", () => fijar(parseFloat(inputN.value) || 0));
inputR.addEventListener("input", () => fijar(parseFloat(inputR.value) || 0));
document.getElementById("btn1500").addEventListener("click", () => fijar(1500));

fijar(DATA.presupuesto);
</script>
</body>
</html>
"""


if __name__ == "__main__":
    ruta = generar()
    print(f"Generado: {ruta}")
