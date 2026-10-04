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

## 2026-10-04 — Día 1 · 3:17 p. m. (hora de Cuba)

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

**Decisiones**

- Se exigieron **marca, precio y autonomía** como datos obligatorios, pero el
  **tipo de batería quedó opcional**: solo 1 de cada 4 anuncios lo publica, y
  exigirlo habría dejado fuera más de la mitad del mercado.
- Los precios se guardaron convertidos a **USD** (745 CUP = 1 USD) para que las
  tres categorías sean comparables entre sí.
- Se corrigió una marca que se detectaba mal ("Volt", que en realidad estaba
  leyendo el voltaje de la batería) y se eliminó un anuncio que estaba repetido
  en dos categorías.

**Problemas**

- La web falla la conexión con frecuencia: se añadieron reintentos y guardado
  parcial para no perder el trabajo ya hecho.
- El script inicial no encontraba la autonomía cuando el anuncio usaba tildes
  ("Autonomía") y detectaba marcas falsos a partir del voltaje.

**Pendiente**

- Escribir la historia del proyecto (introducción del notebook).
- Conseguir una segunda fuente de datos para contrastar.
- Análisis descriptivo y visualizaciones.
- Documentación del proyecto (`README.md` y `HANDS_OFF.md`).