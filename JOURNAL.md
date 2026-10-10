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

## 2026-10-11 — Tercera fuente ENCUESTAS y conclusiones

Se incorporó la **tercera fuente: las encuestas a personas** que ya tienen un vehículo
eléctrico (6 preguntas: tipo, marca, precio, tiempo, autonomía de nuevo y actual, y
calidad). Hasta ahora hay **20 personas de las 30 previstas** (faltan 10). Las respuestas
quedaron en `data/encuestas_personas.json`, normalizando meses a años, millas a km y
corrigiendo algunos datos con la autora (P20: nueva 70, actual 50).

De las encuestas salieron cuatro análisis: los datos de cada persona, el resumen por tipo,
la **degradación de la autonomía por marca** y la **calidad según los dueños**, más un
contraste de la **autonomía real frente a la publicada**. Resultados: ninguna persona
calificó su vehículo como malo (75 % bueno, 25 % regular); la autonomía cae con el uso;
y los anuncios prometen más autonomía de la que reportan los dueños. Dos casos cambiaron
la batería (P11, P16) y uno reporta mejora por asentamiento (P9): se marcan aparte para
no falsear la degradación.

El gráfico de degradación se rehízo varias veces (dispersión, barras, pendientes,
burbujas) hasta dar con el definitivo: una **dispersión con línea de tendencia** que
muestra a la vez los **años de uso** (eje x), la **autonomía perdida** (eje y) y el
**tipo de vehículo** (color). Se hicieron además un **pastel** de la calidad y un
**dumbbell** de autonomía real frente a la publicada.

Se añadió un **explorador interactivo** (`interactivo.html`, generado por
`interactivo.py`): cualquiera escribe un presupuesto y ve hasta dónde le alcanza en
autonomía, qué vehículo y la mejor opción de cada tipo entre las analizadas. El
notebook lo muestra incrustado y también se publica con GitHub Pages para verlo en
el navegador.

Por último se escribieron las **conclusiones generales del estudio**, cruzando las tres
fuentes: el precio lo explican, en orden, el **tipo de vehículo**, la **autonomía (y su
batería)** y el **canal de venta**, más que la marca; la **calidad** solo se puede medir
con el uso real y resulta **aceptable**, con la batería y la autonomía como puntos débiles.

Pendiente: recibir las **10 encuestas que faltan** para cerrar la fuente y reajustar
tablas y gráficos; y la autonomía de 14 de los 43 productos de CubAmerica.