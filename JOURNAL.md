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

## 2026-10-10 — Segunda fuente MERCADO

Se analizó la **segunda fuente: MERCADO**, con las dos tiendas de importación
VEDCA (Islagrande) y CubAmerica (envíos), **53 productos** (VEDCA 10, CubAmerica 43).
Se corrigió la primera fuente: **CubAmerica sale de INTERNET y pasa a MERCADO** junto
con VEDCA, de modo que INTERNET queda con Revolico e iTENCEL (**353 productos**).

De MERCADO se hicieron dos análisis: la **disponibilidad y los precios** de cada tienda
(con 1.500 USD caben 7 de 10 en VEDCA y 15 de 43 en CubAmerica) y la **autonomía por
tipo de vehículo** frente al presupuesto, con un mapa de calor de dos paneles (todos
los productos publicados frente a los que caben en el presupuesto). Se decidió que este
análisis vaya **sin marcas**; los nombres aparecen solo al señalar la mejor opción de
cada tipo en cada mercado.

Pendiente: conseguir las fuentes restantes (Telegram y encuestas) y el análisis cruzado
entre INTERNET y MERCADO para decidir dónde conviene comprar.

## 2026-10-11 — Tercera fuente ENCUESTAS y conclusiones generales

Se incorporó la **tercera fuente: las encuestas a personas** que ya tienen un vehículo
eléctrico. Hasta ahora hay **20 personas de las 30 previstas** (faltan 10), guardadas en
`data/encuestas_personas.json`, normalizando meses a años, millas a km y corrigiendo
algunos datos con la autora (P20: nueva 70, actual 50).

De estas encuestas se hicieron los análisis: los datos de cada persona, el resumen por
tipo, el contraste entre la **autonomía anunciada y la real**, y la **calidad según los
dueños**. Resultados: ninguna persona calificó su vehículo como malo (75 % bueno, 25 %
regular); la autonomía cae con el uso; y los anuncios prometen más autonomía de la que
reportan los dueños. Dos casos cambiaron la batería (P11, P16) y uno reporta mejora por
asentamiento (P9), y se marcan aparte para no falsear los resultados.

Se añadió un **explorador interactivo** (`interactivo.html`) donde cualquiera escribe su
presupuesto y ve al instante en qué **fuente** (Internet o Mercado) y con qué **tipo de
vehículo** llega más lejos; el notebook lo muestra incrustado y también se publica con
GitHub Pages.

Por último se empezaron a escribir las **conclusiones generales del proyecto**, cruzando
las tres fuentes: el precio lo explican sobre todo el **tipo de vehículo**, la **autonomía
(y su batería)** y el **canal de venta**, más que la marca; y la **calidad** solo puede
medirse con el uso real.

Pendiente: cerrar las **10 encuestas que faltan**, la autonomía de 14 de los 43 productos
de CubAmerica, terminar las conclusiones y **pulir los gráficos**.