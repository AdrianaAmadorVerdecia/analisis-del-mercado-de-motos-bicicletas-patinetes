# Informe metodológico — El precio de la autonomía

**Autora:** Adriana Amador Verdecia · Ciencia de Datos, primer año · MATCOM, Universidad de La Habana

**Planteamiento.** Nos planteamos determinar **qué variables explican el precio** de los vehículos eléctricos privados en Cuba y **hasta qué punto es posible medir su calidad** con la información que publica el mercado. Para ello se caracterizó la oferta de **motos, bicicletas y patinetes** en La Habana a través de tres fuentes independientes —Internet, Mercado y Encuestas—, con un presupuesto de referencia de **1.500 USD**.

## 1. Métodos

**Enfoque.** Estudio **descriptivo y comparativo**, de carácter **transversal**, sobre la oferta de vehículos eléctricos de movilidad personal en La Habana. Se usaron **tres fuentes independientes** para triangular los resultados: **Internet** (Revolico e iTENCEL), **Mercado** (VEDCA y CubAmerica) y **Encuestas** (35 personas con vehículo propio).

**Obtención de los datos.**

- **Internet:** 353 anuncios (Revolico 224, iTENCEL 129), mediante **web scraping** (`codigo/scraper_revolico.py`, `codigo/scraper_itencel.py`). Los precios de Revolico, publicados en CUP, se convirtieron a USD con la tasa **745 CUP = 1 USD**.
- **Mercado:** 53 productos (VEDCA 10 en EUR, CubAmerica 43 en USD), por scraping de las páginas de producto (`codigo/scraper_vedca.py`, `codigo/scraper_cubamerica.py`), con conversión EUR→USD a **1,13**. CubAmerica no publica la autonomía de **14 de sus 43 productos**; esos casos entran en precio y disponibilidad, pero no en autonomía.
- **Encuestas (fuente primaria):** **35 encuestas** con un cuestionario de **6 preguntas cerradas** (tipo, marca, precio, tiempo de uso, autonomía recién comprado y actual, y calidad buena/regular/mala). Las respuestas se anotaron en libreta y se fotografiaron como evidencia (`data/evidencia encuestas/`, 13 imágenes) y se digitalizaron en `data/encuestas_personas.json`.

**Variables del estudio:** tipo de vehículo, marca, precio (USD), autonomía (km), años de uso y calidad percibida.

**Procedimiento de análisis.**

1. Estadística descriptiva por tipo y sitio (total, cuántos caben en 1.500 USD, precio promedio/mediana/rango).
2. Disponibilidad dentro del presupuesto por tipo y sitio.
3. Autonomía por tipo y presupuesto, con mapas de calor (todos los productos frente a los alcanzables).
4. Degradación real de la autonomía (pérdida = nueva − actual, en km y %).
5. Contraste anunciado vs. real (autonomía publicada − autonomía real de fábrica, por tipo; barras divergentes).
6. Calidad según los dueños (distribución en tres niveles).
7. Explorador interactivo por presupuesto.

**Herramientas.** Python 3 con `matplotlib` y `numpy`; Plotly.js para el explorador publicado en GitHub Pages; notebook `proyecto.ipynb` y código en `codigo/analisis.py`; Git/GitHub para el control de versiones.

## 2. Resultados

### 2.1 Internet (Revolico e iTENCEL)

| Sitio | Productos | Caben en 1.500 USD | Moto prom. (USD) | Bici prom. (USD) | Patinete prom. (USD) | Autonomía prom. alcanzable | Autonomía máx. alcanzable |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Revolico | 224 | **154** | 2.386 | 745 | 733 | 50 km | 100 km |
| iTENCEL | 129 | **64** | 2.636 | 2.188 | 1.064 | 59 km | 130 km |

### 2.2 Mercado (VEDCA y CubAmerica)

| Tienda | Productos | Caben en 1.500 USD | Moto prom. (USD) | Bici prom. (USD) | Patinete prom. (USD) | Autonomía prom. alcanzable | Autonomía máx. alcanzable |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VEDCA | 10 | **7** | 1.675 | 817 | — | 66 km | 90 km |
| CubAmerica | 43 | **15** | 2.540 | 1.453 | 666 | 69 km | 140 km |

### 2.3 Encuestas (35 personas) — resumen por tipo

| Tipo | Personas | Precio prom. (USD) | Autonomía nueva prom. (km) | Autonomía actual prom. (km) | Pérdida prom. |
| --- | --- | --- | --- | --- | --- |
| Moto eléctrica | 21 | 1.405 | 77 | 62 | 20,2 % |
| Bicicleta eléctrica | 11 | 1.050 | 71 | 62 | 15,1 % |
| Patinete eléctrico | 3 | 273 | 26 | 21 | 19,4 % |

### 2.4 Calidad según sus dueños

| Calidad | Personas | Porcentaje |
| --- | --- | --- |
| Buena | 28 | 80,0 % |
| Regular | 7 | 20,0 % |
| Mala | 0 | 0,0 % |

### 2.5 Autonomía anunciada vs. real

| Tipo | Personas | Nueva real (km) | Actual real (km) | Publicada Internet (km) | Publicada Mercado (km) |
| --- | --- | --- | --- | --- | --- |
| Moto eléctrica | 21 | 77 | 62 | 106 | 106 |
| Bicicleta eléctrica | 11 | 71 | 62 | 63 | 80 |
| Patinete eléctrico | 3 | 26 | 21 | 49 | 56 |

## 3. Conclusiones

Los resultados muestran que el precio de un vehículo eléctrico en Cuba lo ordena, en primer lugar, el **tipo** (moto > bicicleta > patinete, de forma consistente en las tres fuentes), seguido de la **autonomía y la batería** y del **canal de venta**: Internet, con vehículos usados, resulta más barato que el Mercado de importación, y la **marca** explica menos que el tipo. En cuanto a la problemática planteada —medir la calidad con la información disponible—, se confirma que **Internet y el Mercado no permiten estimarla**, porque publican sobre todo precio y autonomía; solo las **encuestas**, a partir del uso real, ofrecen una medida (aunque subjetiva) de la calidad, que resulta **aceptable**: 80 % bueno, 20 % regular y ninguna opinión mala, con la **batería y la autonomía** como puntos débiles. Además, los anuncios tienden a **exagerar la autonomía** (sobre todo en motos y patinetes) y la autonomía real **se degrada con el uso**, más en motos y patinetes que en bicicletas. Con 1.500 USD, la mejor relación precio-autonomía se concentra en **bicicletas y patinetes**, especialmente en CubAmerica, mientras que VEDCA ofrece las entradas más baratas.
