# Journal — Análisis del mercado de vehículos eléctricos en La Habana

**Proyecto:** ¿Se puede construir una comparación objetiva entre precio, marca y calidad a partir de la información que los vendedores publican en sus anuncios?

**Autora:** Adriana Amador Verdecia
**Carrera:** Ciencia de Datos — Primer año
**Institución:** Universidad de La Habana · Facultad de Matemática y Computación (MATCOM)

---

Este archivo es la bitácora del proyecto: aquí se registra día a día lo que se hace,
con qué decisiones se toma y qué problemas aparecen. La idea es que alguien que no
conozca el proyecto pueda leerlo y entender cómo se llegó al resultado final.

---

## 2026-10-04 — Día 1

**Qué se hizo**

1. **Definición del problema de investigación.** Se busca una forma de comparar
   precio, marca y calidad de los vehículos eléctricos anunciados en La Habana,
   usando únicamente la información que los vendedores publican en sus anuncios.

2. **Elección de la fuente de datos.** Revolico, por ser el mercado informal
   digital donde se publican estas ventas en Cuba.

3. **Scraper (`scraper_revolico.py`).** La web entrega sus datos estructurados
   dentro del propio HTML (bloque `__NEXT_DATA__`), lo que permite leerlos
   directamente sin navegador ni Selenium. De cada anuncio se extraen: título,
   precio, moneda, provincia, descripción y URL.

4. **Depuración de los datos.** De los anuncios revisados se descartaron:
   - los que no son de la provincia de La Habana,
   - los que no dicen marca, precio ni autonomía,
   - los precios irreales (anzuelos de 1 USD, precios inflados),
   - los anuncios de tiendas con varios productos,
   - los duplicados y los anuncios mal descritos.

5. **Dataset final (`data/anuncios_revolico.json`).** 224 anuncios de La Habana:
   75 motos eléctricas, 75 bicicletas eléctricas y 74 patinetes eléctricos.
   156 de los 224 (70 %) mencionan el tipo de batería.

6. **Documentación y publicación.** Se escribieron `README.md` y `HANDS_OFF.md`,
   y se creó el repositorio público
   `AdrianaAmadorVerdecia/analisis-del-mercado-de-motos-bicicletas-patinetes`
   con el script, los datos y la documentación.

7. **Historia y problemática** del proyecto. Se escribió la introducción del
   notebook: el caso de Lucy, estudiante de MATCOM de 20 años con un presupuesto
   de 1.500 dólares, y el planteamiento del problema y el objetivo general.

8. **El precio de cada categoría.** Tabla con el promedio, el precio más frecuente
   (mediana), los valores extremos y la autonomía más común, más una comprobación de
   que ningún precio extremo deforma el promedio, y un gráfico de barras verticales.

9. **La disponibilidad dentro del presupuesto.** Cuántos anuncios de cada categoría
   quedan dentro de los 1.500 dólares, con su rango de precio y de autonomía, en un
   gráfico de barras horizontales, más el detalle de las seis motos accesibles.

10. **La autonomía disponible dentro del presupuesto.** Rango de autonomía y valor
    más frecuente por categoría, en un gráfico de barras horizontales con rango.

11. **Reestructuración del proyecto.** Todo el código pasó a un único archivo
    (`analisis.py`), organizado por fuente de datos. El notebook quedó sin código:
    solo texto, tablas e imágenes, para que se pueda leer directamente en GitHub.

**Decisiones**

- Se exigieron **marca, precio y autonomía** como datos obligatorios, pero el
  **tipo de batería quedó opcional**: aunque lo publica el 70 % de los anuncios
  (156 de 224), exigirlo habría dejado fuera los 68 restantes.
- Los precios se guardaron convertidos a **USD** (745 CUP = 1 USD) para que las
  tres categorías sean comparables entre sí.
- Se corrigió una marca que se detectaba mal ("Volt", que en realidad estaba
  leyendo el voltaje de la batería) y se eliminó un anuncio que estaba repetido
  en dos categorías.
- **El proyecto se hará fuente por fuente.** Antes de analizar cada fuente se
  pregunta qué análisis tiene sentido, y **ninguna gráfica se hace hasta que la
  autora indique cuál y cómo**.
- Como en Revolico no se conoce la calidad real del producto, el primer análisis
  se centró en el precio y no en la autonomía, que es el dato que más se publica.
- **El notebook no lleva código.** Todo vive en un único archivo, `analisis.py`,
  dividido por secciones: configuración, utilidades, fuente 1 (Revolico) y un
  espacio reservado para las demás fuentes. Así se puede leer el proyecto entero
  en GitHub sin ejecutar nada, que era el problema del notebook anterior.
- Cada análisis lleva su explicación, después la tabla, después la explicación del
  gráfico, después el gráfico y una descripción de lo que el gráfico muestra.
- Se descartó el gráfico de dispersión con los 224 puntos: era ilegible. En su lugar
  cada análisis tiene un gráfico distinto y con pocos elementos, pensado para que
  cualquier persona pueda leerlo sin conocimientos previos.
- El lenguaje del notebook es formal y está dirigido a un público general.

**Problemas**

- La web falla la conexión con frecuencia: se añadieron reintentos y guardado
  parcial para no perder el trabajo ya hecho.
- El script inicial no encontraba la autonomía cuando el anuncio usaba tildes
  ("Autonomía") y detectaba marcas falsos a partir del voltaje.
- **No hay salida a PyPI desde la conexión actual**, así que `pandas` no se pudo
  instalar. Todo quedó escrito con la biblioteca estándar (`json`, `statistics`)
  y `matplotlib`, que ya estaba instalado.
- El primer push a GitHub falló porque el sistema usó la cuenta equivocada. Se
  fijó la cuenta de la autora solo para este repositorio, sin tocar la
  configuración global de Git.
- **La autonomía alta es poco común dentro del presupuesto:** de los 154 anuncios
  alcanzables, solo 3 llegan a 80 km o más. A eso se suma que el 30 % no declara
  el tipo de batería y que ningún anuncio indica fecha. Con esta fuente no se puede
  afirmar cuál vehículo le conviene más a Lucy; la pregunta queda abierta hasta
  contar con datos de calidad de las demás fuentes.

**Pendiente**

- Completar la lista de fuentes (Telegram, encuestas, mercados).
- Repetir los análisis en cada fuente nueva y comparar resultados.
- Escribir las conclusiones generales del estudio.
- Actualizar `HANDS_OFF.md` con los resultados.

---

## 2026-10-04 — Primera fuente concluida

**Qué se hizo**

1. **Cierre de la fuente Revolico.** Se terminaron los tres análisis previstos
   (precio por categoría, disponibilidad dentro de los 1.500 USD y autonomía
   alcanzable) y se redactó el bloque **"Conclusiones de la fuente Revolico"**
   en el notebook, que responde por primera vez a la pregunta de investigación.

2. **Lo que se concluyó con esta fuente.** La categoría del vehículo es la
   variable que explica el precio: la moto cuesta 3,2 veces la bicicleta, pero
   dentro de cada categoría los precios son regulares y el precio por sí solo no
   distingue calidad. Con 1.500 USD se accede a cualquier categoría (75 de 75
   bicicletas y 73 de 74 patinetes) pero a solo 6 de 75 motos, y pagar más no
   garantiza más autonomía: dentro del presupuesto las motos alcanzan una mediana
   de 60 km frente a 50 km de bicicletas y patinetes.

3. **Límite de esta primera fuente.** La calidad solo se puede medir a medias:
   el 30 % de los anuncios no declara la batería, no hay fechas y los precios son
   los solicitados por el vendedor, no los de venta. Por eso las conclusiones
   generales del estudio siguen reservadas hasta analizar el resto de fuentes.

**Decisiones**

- Se adoptó el formato de **conclusiones por fuente**: cada fuente cierra con su
  propio bloque de conclusiones, y al final se escribirán las conclusiones
  generales que comparen todas las fuentes.
