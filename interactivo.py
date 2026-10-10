"""Genera `interactivo.html`: un explorador interactivo del estudio.

Reune los datos ya analizados (productos de Internet y Mercado, y las
encuestas) y construye una pagina HTML autocontenida con Plotly que:

 1. Muestra la dispersion de la degradacion de la autonomia (años de uso frente
    al % perdido) con linea de tendencia y tooltips.
 2. Deja que cualquier persona escriba un presupuesto y ve hasta donde le
    alcanza en autonomia, que tipo de vehiculo y cual es la mejor opcion.

Se puede abrir en cualquier navegador y tambien incrustar en el notebook.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import analisis as a

RAIZ = Path(__file__).resolve().parent
DESTINO = RAIZ / "interactivo.html"


def datos_productos() -> list[dict]:
    """Productos de las dos fuentes (Internet y Mercado) con precio y autonomia."""
    return [{
        "tipo": a.ETIQUETAS[p["tipo"]],
        "marca": p["marca"],
        "sitio": p["sitio"],
        "precio": p["precio"],
        "autonomia": p["autonomia"],
    } for p in a.productos_todos()]


def datos_encuestas() -> list[dict]:
    """Personas encuestadas con su degradacion de autonomia."""
    encuestas = []
    for p in a.cargar_encuestas():
        _, porciento = a._perdida(p)
        encuestas.append({
            "id": p["id"].replace("PERSONA ", "P"),
            "tipo": a.ETIQUETAS[p["tipo_vehiculo"]],
            "marca": p["marca"],
            "anios": p["anios_uso"],
            "pct": round(porciento, 1),
            "nueva": p["autonomia_nueva_km"],
            "actual": p["autonomia_actual_km"],
            "nota": p["nota"],
        })
    return encuestas


def tendencia() -> list[float]:
    """Recta de tendencia (años -> % perdido) sin los casos excepcionales."""
    base = [p for p in a.cargar_encuestas()
            if not p["bateria_cambiada"] and not p["nota"]]
    xs = [p["anios_uso"] for p in base]
    ys = [a._perdida(p)[1] for p in base]
    pendiente, corte = np.polyfit(xs, ys, 1)
    todos = [p["anios_uso"] for p in a.cargar_encuestas()]
    x0, x1 = min(todos), max(todos)
    return [x0, pendiente * x0 + corte, x1, pendiente * x1 + corte]


def empaquetar() -> dict:
    return {
        "productos": datos_productos(),
        "encuestas": datos_encuestas(),
        "tipos": a.COLOR_TIPO,
        "orden": [a.ETIQUETAS[t] for t in a.ORDEN],
        "tendencia": tendencia(),
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
          padding:22px 24px 16px; margin-bottom:22px;
          box-shadow:0 6px 20px rgba(15,23,42,.05); }
  .card h2 { font-size:19px; margin:0 0 4px; }
  .sub { color:var(--gris); font-size:14px; margin:0 0 14px; line-height:1.5; }
  .controles { display:flex; flex-wrap:wrap; align-items:center; gap:14px; margin:6px 0 18px; }
  .controles label { font-weight:600; font-size:15px; }
  .controles input[type=number] { width:130px; padding:9px 12px; font-size:17px;
          font-weight:700; border:1.5px solid var(--borde); border-radius:10px; color:var(--tinta); }
  .controles input[type=range] { flex:1; min-width:180px; accent-color:#1d6fe0; }
  .controles button { padding:9px 16px; font-size:14px; font-weight:600; cursor:pointer;
          border:none; border-radius:10px; background:#1d6fe0; color:#fff; }
  .controles button:hover { background:#155bc0; }
  .resumen { font-size:17px; line-height:1.55; background:#f0f6ff; border:1px solid #d6e6ff;
          border-radius:12px; padding:14px 16px; margin-bottom:16px; }
  .resumen b { color:#0f172a; }
  .opciones { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
          gap:12px; margin-bottom:8px; }
  .op { border:1px solid var(--borde); border-radius:12px; padding:12px 14px; background:#fbfcfe; }
  .op h4 { margin:0 0 6px; font-size:14px; }
  .op p { margin:2px 0; font-size:13.5px; color:#374151; line-height:1.45; }
  .op-vacia { opacity:.6; }
  .plot { width:100%; }
  .cuadre { display:grid; grid-template-columns:1fr 1fr; gap:18px; }
  @media (max-width:760px){ .cuadre { grid-template-columns:1fr; } }
  footer { text-align:center; color:var(--gris); font-size:12.5px; margin-top:24px; line-height:1.6; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Explorador de vehículos eléctricos</h1>
    <p>Precio, autonomía y calidad real de las motos, bicicletas y patinetes eléctricos
       anunciados en La Habana, según los anuncios de Internet, el mercado de
       importación y las encuestas a sus dueños.</p>
  </header>

  <section class="card">
    <h2>1. ¿Cuánta autonomía se pierde con los años?</h2>
    <p class="sub">Cada punto es una persona encuestada. Pasa el cursor por encima
       para ver su marca, su autonomía y cuánto ha perdido.</p>
    <div id="dispersion" class="plot"></div>
  </section>

  <section class="card">
    <h2>2. ¿Hasta dónde llega tu presupuesto?</h2>
    <p class="sub">Escribe cuánto puedes gastar: verás cuánta autonomía alcanzas,
       qué tipo de vehículo y cuál es la mejor opción de las analizadas.</p>
    <div class="controles">
      <label for="presupuesto">Presupuesto (USD):</label>
      <input id="presupuesto" type="number" min="100" max="6000" step="50">
      <input id="rango" type="range" min="100" max="6000" step="50">
      <button id="btn1500" type="button">Lucy: 1.500 USD</button>
    </div>
    <div id="resumen" class="resumen"></div>
    <div class="cuadre">
      <div id="frontera" class="plot"></div>
      <div id="portipo" class="plot"></div>
    </div>
    <div id="opciones" class="opciones" style="margin-top:14px;"></div>
  </section>

  <footer>
    Fuentes: Revolico e iTENCEL (Internet), VEDCA y CubAmerica (Mercado) y 20 encuestas
    a dueños. Precios en USD (745 CUP = 1 USD).<br>
    Trabajo de Ciencia de Datos · MATCOM, Universidad de La Habana.
  </footer>
</div>

<script>
const DATA = /*__DATA__*/;
const TIPOS = DATA.tipos;
const ORDEN = DATA.orden;
const PRODUCTOS = DATA.productos;
const ENCUESTAS = DATA.encuestas;

const fmt = n => Math.round(n).toLocaleString("es-ES");
const USD_KM = p => p.precio / p.autonomia;
const plural = (n, uno, muchos) => n + " " + (n === 1 ? uno : muchos);

const layoutBase = {
  paper_bgcolor:"#fff", plot_bgcolor:"#fff",
  font:{color:"#374151", size:12.5},
  margin:{l:64, r:22, t:16, b:52},
  hoverlabel:{bgcolor:"#fff", bordercolor:"#d1d5db", font:{color:"#0f172a", size:12.5}},
};

/* ---------- 1. Dispersión de la degradación ---------- */
function dibujarDispersion(){
  const traces = ORDEN.map(tipo => {
    const pts = ENCUESTAS.filter(e => e.tipo === tipo);
    return {
      x: pts.map(e => e.anios),
      y: pts.map(e => e.pct),
      text: pts.map(e =>
        "<b>Persona " + e.id + "</b><br>" + e.tipo + " · " + e.marca +
        "<br>Años de uso: " + e.anios +
        "<br>Autonomía: " + e.nueva + " → " + e.actual + " km" +
        "<br>Pérdida: " + e.pct + " %" +
        (e.nota ? "<br><i>" + e.nota + "</i>" : "")),
      hovertemplate: "%{text}<extra></extra>",
      mode: "markers", type: "scatter", name: tipo,
      marker: { color: TIPOS[tipo], size: 15,
                line: { color: "#fff", width: 1.6 }, opacity: .92 },
    };
  });
  const tr = DATA.tendencia;
  const linea = {
    x: [tr[0], tr[2]], y: [tr[1], tr[3]], mode: "lines",
    name: "Tendencia", line: { color: "#6b7280", width: 2.5, dash: "dash" },
    hoverinfo: "skip",
  };
  const layout = Object.assign({}, layoutBase, {
    height: 430,
    xaxis: { title: "Años de uso", gridcolor: "#eef1f4", zeroline: false },
    yaxis: { title: "Autonomía perdida (%)", gridcolor: "#eef1f4",
             zeroline: true, zerolinecolor: "#9ca3af" },
    legend: { orientation: "h", y: 1.14, x: 0 },
  });
  Plotly.newPlot("dispersion", traces.concat([linea]), layout,
                 { responsive: true, displaylogo: false });
}

/* ---------- 2. Explorador de presupuesto ---------- */
const inputN = document.getElementById("presupuesto");
const inputR = document.getElementById("rango");
const resumen = document.getElementById("resumen");
const opciones = document.getElementById("opciones");

const maxPrecio = Math.max.apply(null, PRODUCTOS.map(p => p.precio));
const techoX = Math.ceil(maxPrecio / 500) * 500;

function dibujarFrontera(B, dentro){
  const conAut = PRODUCTOS;
  const traces = ORDEN.map(tipo => {
    const sub = conAut.filter(p => p.tipo === tipo);
    return {
      x: sub.map(p => p.precio), y: sub.map(p => p.autonomia),
      text: sub.map(p =>
        "<b>" + p.tipo + "</b><br>" + p.marca + " · " + p.sitio +
        "<br>Precio: $" + fmt(p.precio) + "<br>Autonomía: " + p.autonomia + " km" +
        "<br>$" + USD_KM(p).toFixed(1) + " por km"),
      hovertemplate: "%{text}<extra></extra>",
      mode: "markers", type: "scatter", name: tipo,
      marker: { color: TIPOS[tipo], size: 10,
                line: { color: "#fff", width: 1 },
                opacity: sub.map(p => p.precio <= B ? .95 : .18) },
    };
  });

  // Frontera: mejor autonomía alcanzable para cada precio.
  const orden = PRODUCTOS.slice().sort((a, b) => a.precio - b.precio);
  let fx = [0], fy = [0], mejor = 0;
  orden.forEach(p => { if (p.autonomia > mejor){ mejor = p.autonomia;
                       fx.push(p.precio); fy.push(mejor); } });
  fx.push(techoX); fy.push(mejor);
  const frontera = {
    x: fx, y: fy, mode: "lines", name: "Mejor autonomía a ese precio",
    line: { color: "#111827", width: 2.6, shape: "hv" }, hoverinfo: "skip",
  };

  const lineaPpto = {
    type: "line", x0: B, x1: B, y0: 0, y1: 1, yref: "paper",
    line: { color: "#e63946", width: 2, dash: "dot" },
  };
  const layout = Object.assign({}, layoutBase, {
    height: 430,
    xaxis: { title: "Precio (USD)", gridcolor: "#eef1f4", range: [0, techoX] },
    yaxis: { title: "Autonomía (km)", gridcolor: "#eef1f4" },
    legend: { orientation: "h", y: 1.14, x: 0 },
    shapes: [lineaPpto],
  });
  Plotly.react("frontera", traces.concat([frontera]), layout,
               { responsive: true, displaylogo: false });
}

function dibujarPorTipo(dentro){
  const maxs = ORDEN.map(tipo => {
    const s = dentro.filter(p => p.tipo === tipo);
    return s.length ? Math.max.apply(null, s.map(p => p.autonomia)) : 0;
  });
  const trace = {
    x: ORDEN, y: maxs, type: "bar",
    marker: { color: ORDEN.map(t => TIPOS[t]) },
    text: maxs.map(v => v ? v + " km" : "—"), textposition: "outside",
    cliponaxis: false,
    hovertemplate: "%{x}<br>Hasta %{y} km<extra></extra>",
  };
  const layout = Object.assign({}, layoutBase, {
    height: 430, showlegend: false,
    xaxis: { title: "", tickfont: { size: 11 } },
    yaxis: { title: "Autonomía máxima alcanzable (km)", gridcolor: "#eef1f4" },
  });
  Plotly.react("portipo", [trace], layout, { responsive: true, displaylogo: false });
}

function actualizar(){
  let B = parseFloat(inputN.value);
  if (!isFinite(B)) B = 0;
  B = Math.max(0, B);
  const dentro = PRODUCTOS.filter(p => p.precio <= B);

  if (!dentro.length){
    resumen.innerHTML = "Con <b>$" + fmt(B) + "</b> no alcanza ningún vehículo " +
      "con autonomía publicada entre los analizados.";
    opciones.innerHTML = "";
  } else {
    const maxAut = Math.max.apply(null, dentro.map(p => p.autonomia));
    const maxProd = dentro.filter(p => p.autonomia === maxAut)[0];
    const mejor = dentro.reduce((x, p) => USD_KM(p) < USD_KM(x) ? p : x);
    resumen.innerHTML =
      "Con <b>$" + fmt(B) + "</b> hay <b>" +
      plural(dentro.length, "vehículo", "vehículos") +
      "</b> a tu alcance. La mayor autonomía que puedes comprar es <b>" +
      maxAut + " km</b> (" + maxProd.tipo.toLowerCase() + " " + maxProd.marca +
      ", en " + maxProd.sitio + "). La mejor relación precio-autonomía es " +
      "<b>$" + USD_KM(mejor).toFixed(1) + " por km</b> (" + mejor.tipo.toLowerCase() +
      " " + mejor.marca + ", en " + mejor.sitio + ").";

    opciones.innerHTML = ORDEN.map(tipo => {
      const sub = dentro.filter(p => p.tipo === tipo);
      if (!sub.length){
        return '<div class="op op-vacia"><h4>' + tipo + '</h4>' +
               '<p>Ninguna opción alcanza con este presupuesto.</p></div>';
      }
      const m = sub.reduce((x, p) => USD_KM(p) < USD_KM(x) ? p : x);
      const maxT = Math.max.apply(null, sub.map(p => p.autonomia));
      return '<div class="op"><h4>' + tipo + '</h4>' +
        '<p><b>Mejor opción:</b> ' + m.marca + ' · ' + m.sitio + '</p>' +
        '<p>$' + fmt(m.precio) + ' · ' + m.autonomia + ' km · $' +
        USD_KM(m).toFixed(1) + '/km</p>' +
        '<p>' + plural(sub.length, "opción", "opciones") + ' · hasta ' + maxT + ' km</p></div>';
    }).join("");
  }

  dibujarFrontera(B, dentro);
  dibujarPorTipo(dentro);
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

dibujarDispersion();
fijar(DATA.presupuesto);
</script>
</body>
</html>
"""


if __name__ == "__main__":
    ruta = generar()
    print(f"Generado: {ruta}")
