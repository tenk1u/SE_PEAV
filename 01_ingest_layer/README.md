# 01 – Ingest Layer

**Tecnología:** Python / C++  
**Propósito:** Extracción de frames a partir de vídeos de obra e ingesta de metadatos EXIF para alimentar la capa de geometría.

## Estructura

```
01_ingest_layer/
├── extract_frames.py      # Extrae frames de un vídeo con FFmpeg/OpenCV
├── extract_exif.py        # Lee metadatos EXIF/GPS de imágenes
├── requirements.txt       # Dependencias Python
└── output/                # Carpeta de salida (ignorada en Git)
```

## Dependencias

```bash
pip install -r requirements.txt
```

| Paquete        | Uso                              |
|----------------|----------------------------------|
| opencv-python  | Captura y decodificación de vídeo |
| Pillow         | Lectura de metadatos EXIF        |
| piexif         | Escritura/lectura avanzada EXIF  |
| tqdm           | Barra de progreso                |

## Uso rápido

```bash
# Extraer frames (1 frame cada 2 segundos)
python extract_frames.py --input ../workspace/raw_data/video.mp4 \
                         --output output/frames/ \
                         --fps 0.5

# Leer EXIF de todas las imágenes de un directorio
python extract_exif.py --input output/frames/ \
                       --output output/exif_metadata.json
```

## Salidas esperadas

- `output/frames/` – imágenes PNG numeradas (`frame_0001.png`, …)
- `output/exif_metadata.json` – objeto JSON con metadatos por imagen
