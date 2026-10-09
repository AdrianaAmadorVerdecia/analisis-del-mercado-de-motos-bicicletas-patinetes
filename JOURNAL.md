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

## 2026-10-06 — Primera fuente INTERNET

Se amplió la primera fuente a **Internet** con los tres portales principales:
Revolico (224), CubAmerica (43) e iTENCEL (129), todos con marca, precio y
autonomía (batería opcional). Se arregló un bug de paginación de iTENCEL.

Se reestructuraron los análisis **por sitio**: tabla resumen, precio promedio por
tipo, lo que cabe en el presupuesto de Lucy (1.500 USD) y un análisis general de
autonomía al final, para comparar los portales con el mismo criterio. Total:
**396 productos** (140 motos, 148 bicicletas, 108 patinetes).

VEDCA (Islagrande) queda fuera de esta fuente, como mercado aparte. Pendiente:
autonomía de los 14 de CubAmerica sin publicar. Decisión: las bicimotos cuentan
como bicicleta eléctrica y todo se expresa en USD (745 CUP = 1 USD).