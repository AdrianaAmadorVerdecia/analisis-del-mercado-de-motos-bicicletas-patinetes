# Journal — Análisis del mercado de vehículos eléctricos en La Habana

**Proyecto:** ¿Se puede construir una comparación objetiva entre precio, marca y calidad
a partir de la información que los vendedores publican en sus anuncios?

**Autora:** Adriana Amador Verdecia · Ciencia de Datos — Primer año · MATCOM, Universidad de La Habana

Bitácora del proyecto: un resumen por día con lo que se hizo, las decisiones importantes
y algún problema general.

---

## 2026-10-04 — Fuente Revolico

Se definió el problema de investigación y se eligió como primera fuente el mercado
informal Revolico. Se escribió `scraper_revolico.py`, se depuraron los anuncios y quedó
el dataset con **224 anuncios de La Habana** (75 motos, 75 bicicletas, 74 patinetes).
Se montó el repositorio público, se redactó en el notebook la introducción (Lucy, 20 años,
1.500 USD) y los tres primeros análisis: precio por categoría, disponibilidad dentro del
presupuesto y autonomía alcanzable. Todo el código pasó a `analisis.py` y el notebook quedó
sin código, solo texto, tablas e imágenes.

Se decidió guardar los precios **en USD** (745 CUP = 1 USD), exigir marca, precio y
autonomía pero dejar la **batería opcional**, avanzar **fuente por fuente** y no hacer
ninguna gráfica sin indicación.
Como problema general quedó que **la autonomía alta es escasa dentro del presupuesto**
(solo 3 de 154 alcanzables llegan a 80 km).

## 2026-10-06 — Revolico concluido y resto de "sitios web"

Se cerró Revolico con su bloque de conclusiones (la categoría explica el precio y con
1.500 USD se llega a casi todo menos a las motos, solo 6 de 75). Se obtuvo VEDCA desde el
marketplace de Islagrande: de 29 productos publicados quedaron **10 únicos (5 motos y 5
bicicletas)**, con batería y autonomía en todos; su problema general es que casi todo
está agotado.

CubAmerica se leyó por su API de WooCommerce y dejó **57 productos** (18 motos, 30
bicicletas —incluidas 14 bicimotos— y 9 patinetes), con precio, batería y autonomía.
ITENCEL, portal de clasificados mucho mayor de lo previsto, se leyó por su API de
WordPress y quedó en **89 productos** (24 motos, 38 bicicletas, 27 patinetes); a los
anuncios sin precio en el texto se les leyó la ficha y se extrajo el precio publicado,
y los pocos que no lo declaran quedan honestamente sin él.

Se decidió que **las bicimotos cuentan como bicicleta eléctrica**, guardar la marca de
VEDCA, convertir los precios de EUR a USD (1,13) y limitar cada fuente a 50 por tipo de
vehículo. Como problema general, iTENCEL no publica fechas ni todos sus anuncios traen
precio en el texto. Las fuentes de hoy quedan sin analizar su comparación.