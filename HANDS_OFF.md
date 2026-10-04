# Hands-Off — Guía de traspaso del proyecto

**Proyecto:** Análisis del precio, la marca y la calidad de los vehículos eléctricos
anunciados en La Habana a partir de los anuncios de Revolico.

**Autora:** Adriana Amador Verdecia
**Institución:** Universidad de La Habana · Facultad de Matemática y Computación (MATCOM)
**Última actualización:** 4 de octubre de 2026

---

Este documento sirve para que otra persona pueda retomar el proyecto, ejecutarlo y
entenderlo sin tener que preguntar. Se completa al final del proyecto, cuando los
resultados estén listos; las secciones marcadas como *pendiente* se van rellenando
según avanza el trabajo.

---

## 1. Descripción del proyecto

**Pendiente de completar.** Qué pregunta responde el proyecto, cuál es su alcance y
cuáles son sus límites.

## 2. Estructura del repositorio

| Archivo o carpeta | Contenido |
|---|---|
| `data/anuncios_revolico.json` | Dataset de 224 anuncios de La Habana (9 campos) |
| `scraper_revolico.py` | Script que recopila y depura los anuncios de Revolico |
| `proyecto.ipynb` | Notebook con la historia del proyecto y el análisis |
| `JOURNAL.md` | Bitácora diaria del proyecto |
| `HANDS_OFF.md` | Este documento |
| `requirements.txt` | Librerías necesarias para reproducir el proyecto |

## 3. Requisitos e instalación

- Python 3
- Librerías: `requests`, `pandas`, `numpy`, `matplotlib`, `jupyter`, `nbformat`

```
pip install -r requirements.txt
```

## 4. Cómo reproducir los datos

```
python scraper_revolico.py              # corrida completa
python scraper_revolico.py --piloto 3   # prueba rápida con 3 anuncios por tipo
```

**Pendiente de completar:** tiempo aproximado de ejecución, comportamiento del
script si se interrumpe, y advertencia de que la web limita las peticiones.

## 5. Cómo ejecutar el análisis

**Pendiente de completar:** en qué orden se corren las celdas del notebook y qué
librerías usa cada parte.

## 6. Los datos

- **Fuente:** anuncios de vehículos eléctricos publicados en Revolico, provincia de
  La Habana (incluye sus municipios).
- **Cobertura:** 224 anuncios — 75 motos eléctricas, 75 bicicletas eléctricas y
  74 patinetes eléctricos.
- **Campos:** `id`, `tipo_vehiculo`, `titulo`, `url`, `marca`, `precio`, `moneda`,
  `autonomia_km`, `tipo_bateria`.
- **Precio:** almacenado en USD para poder comparar las tres categorías. Se usó la
  tasa de 745 CUP = 1 USD.
- **Tipo de batería:** viene vacío en 68 de los 224 anuncios (70 % lo mencionan),
  porque la mayoría de los vendedores no lo escribe.
- **Fecha:** el sitio no expone la fecha de publicación de forma fiable, por lo que
  el dataset no incluye ese campo.

## 7. Metodología de limpieza

Un anuncio se conserva solo si cumple **todas** estas reglas:

1. Es de la provincia de La Habana.
2. El título corresponde al vehículo de su categoría.
3. El precio está dentro de un rango realista para su categoría (moto 400–15 000
   USD, bicicleta 150–4 000, patinete 60–2 500).
4. El anuncio dice **marca**, **precio** y **autonomía**.
5. No es un anuncio de tienda ni de varios productos.
6. El texto no contradice el precio publicado.
7. Título y descripción tienen longitud suficiente.
8. No es duplicado de otro anuncio ya recopilado.

## 8. Resultados principales

**Pendiente de completar** cuando el análisis esté terminado.

## 9. Limitaciones y trabajo futuro

- El tipo de batería no lo publica la mayoría de los vendedores, así que no puede
  usarse como variable obligatoria.
- El dataset solo cubre La Habana; no se puede generalizar a toda Cuba.
- Los anuncios no dicen antigüedad del vehículo ni estado real, así que no se puede
  medir la depreciación.

**Pendiente de completar.**

## 10. Autoría

Adriana Amador Verdecia — Ciencia de Datos, primer año — Universidad de La Habana.