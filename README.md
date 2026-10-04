# Análisis del mercado de motos, bicicletas y patinetes eléctricos en La Habana

Proyecto de Ciencia de Datos (Universidad de La Habana, MATCOM) sobre **qué se puede
aprender de los anuncios de vehículos eléctricos**: se comparan **precio, marca y
calidad** usando solo la información que los vendedores publican en Revolico.

## Qué hay aquí

| Archivo | Qué es |
|---|---|
| `data/anuncios_revolico.json` | 224 anuncios de La Habana (motos, bicicletas y patinetes eléctricos) |
| `scraper_revolico.py` | Script que recopila y depura los anuncios |
| `proyecto.ipynb` | La historia del proyecto y el análisis |
| `JOURNAL.md` | Bitácora diaria: qué se hizo cada día |
| `HANDS_OFF.md` | Guía de traspaso: cómo reproducir el proyecto |

## Cómo ejecutarlo

```
pip install -r requirements.txt
python scraper_revolico.py     # vuelve a construir los datos (tarda bastante)
jupyter lab                     # para abrir el notebook
```

El dataset ya está incluido, así que para ver el análisis solo hace falta abrir
`proyecto.ipynb`.

## Autora

Adriana Amador Verdecia — Ciencia de Datos, primer año — Universidad de La Habana.