# El precio de la autonomía

Proyecto de Ciencia de Datos (Universidad de La Habana, MATCOM) sobre **qué se puede
aprender de los anuncios de vehículos eléctricos** en La Habana: se comparan **precio,
marca y calidad** usando solo la información que los vendedores publican.

**El caso de referencia es Lucy**, estudiante de 20 años con un presupuesto de
**1.500 dólares**, que no puede decidir qué vehículo comprar porque los anuncios no
dicen con claridad cuánto rinde cada uno.

## Qué hay aquí

| Archivo | Qué es |
|---|---|
| `proyecto.ipynb` | La historia, la problemática y los resultados con sus tablas y gráficos. **No tiene código**: solo texto, tablas e imágenes. |
| `analisis.py` | **Todo el código del proyecto.** Aquí van los cálculos, las tablas y los gráficos, organizados por fuente de datos. |
| `data/anuncios_revolico.json` | 224 anuncios de La Habana (75 motos, 75 bicicletas, 74 patinetes) |
| `scraper_revolico.py` | Script que recopila y depura los anuncios |
| `graficos/` | Los gráficos que genera `analisis.py` |
| `JOURNAL.md` | Bitácora diaria: qué se hizo cada día, sin hora |
| `HANDS_OFF.md` | Guía de traspaso: cómo reproducir el proyecto |

## Cómo ejecutarlo

```
pip install -r requirements.txt
python analisis.py             # genera los gráficos de la carpeta graficos/
jupyter lab                     # para abrir el notebook
```

El dataset ya está incluido, así que para ver el análisis no hace falta volver a
scrapear (que además es lento y falla a menudo por la conexión).

Para reconstruir los datos desde cero:

```
python scraper_revolico.py
```

## La estructura

El proyecto se analiza **fuente por fuente**: Revolico, los sitios de venta informal,
las encuestas a personas y los mercados de vehículos eléctricos. En `analisis.py` cada
fuente tiene su propia sección, y los gráficos que produce se van incorporando al
notebook en el orden en que se analizan.

## Autora

Adriana Amador Verdecia — Ciencia de Datos, primer año — Universidad de La Habana.