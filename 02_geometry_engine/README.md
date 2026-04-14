# 02 – Geometry Engine

**Tecnología:** C++ / CUDA  
**Propósito:** Reconstrucción 3-D mediante COLMAP (SfM + MVS) y representación con 3D Gaussian Splatting (3DGS).

## Estructura

```
02_geometry_engine/
├── CMakeLists.txt          # Sistema de build CMake
├── colmap_runner.py        # Wrapper Python para ejecutar el pipeline COLMAP
├── train_3dgs.py           # Lanza el entrenamiento 3DGS sobre la escena COLMAP
├── src/
│   └── gaussian_utils.cpp  # Utilidades C++ para manejo de gaussianas
└── build/                  # Directorio de compilación (ignorado en Git)
```

## Requisitos previos

- **COLMAP** ≥ 3.8 (instalado en el contenedor `geometry_engine`)
- **CUDA** ≥ 11.8
- **CMake** ≥ 3.20
- **Python** ≥ 3.10 + `torch`, `plyfile`, `tqdm`

## Build (C++)

```bash
cd 02_geometry_engine
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel $(nproc)
```

## Uso rápido

```bash
# 1. Ejecutar COLMAP sobre los frames extraídos
python colmap_runner.py \
    --images ../01_ingest_layer/output/frames/ \
    --workspace ../workspace/processed_data/colmap_output/

# 2. Entrenar 3DGS sobre la escena COLMAP reconstruida
python train_3dgs.py \
    --source_path ../workspace/processed_data/colmap_output/ \
    --model_path  ../workspace/processed_data/3dgs_model/
```

## Salidas esperadas

- `processed_data/colmap_output/` – cámaras, puntos dispersos y densos
- `processed_data/3dgs_model/` – gaussianas entrenadas (`point_cloud.ply`)
