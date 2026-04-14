"""
train_3dgs.py
-------------
Lanza el entrenamiento de 3D Gaussian Splatting (3DGS) usando la escena
reconstruida por COLMAP.

Este script asume que el repositorio oficial de 3DGS está disponible como
submódulo o instalado en el entorno. Actúa como punto de entrada parametrizado
para integrarlo en el pipeline de este proyecto.

Dependencias Python: torch, plyfile, tqdm, Pillow

Uso:
    python train_3dgs.py --source_path <colmap_workspace> \
                         --model_path  <directorio_modelo>
"""

import argparse
import subprocess
import sys
from pathlib import Path


def train_3dgs(source_path: str, model_path: str, iterations: int = 30_000) -> None:
    source = Path(source_path).resolve()
    model = Path(model_path).resolve()
    model.mkdir(parents=True, exist_ok=True)

    # Buscar el script de entrenamiento 3DGS (submódulo o instalación local)
    candidates = [
        Path("gaussian-splatting") / "train.py",
        Path("third_party") / "gaussian-splatting" / "train.py",
    ]
    train_script: Path | None = next(
        (c for c in candidates if c.exists()), None
    )

    if train_script is None:
        print(
            "[ERROR] No se encontró train.py de 3DGS.\n"
            "        Clona el repositorio oficial en 'gaussian-splatting/' o\n"
            "        en 'third_party/gaussian-splatting/'.",
            file=sys.stderr,
        )
        sys.exit(1)

    cmd = [
        sys.executable, str(train_script),
        "-s", str(source),
        "-m", str(model),
        "--iterations", str(iterations),
    ]
    print(f"[3DGS] Iniciando entrenamiento ({iterations} iteraciones)…")
    print(f"[3DGS] $ {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        print(f"[ERROR] Entrenamiento fallido con código {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)

    print(f"\n[OK] Modelo 3DGS guardado en '{model}'")


def main() -> None:
    parser = argparse.ArgumentParser(description="Entrena un modelo 3D Gaussian Splatting.")
    parser.add_argument(
        "--source_path", required=True,
        help="Ruta a la escena COLMAP (debe contener sparse/0/ e images/)",
    )
    parser.add_argument(
        "--model_path", required=True,
        help="Directorio de salida del modelo 3DGS",
    )
    parser.add_argument(
        "--iterations", type=int, default=30_000,
        help="Número de iteraciones de entrenamiento (default: 30000)",
    )
    args = parser.parse_args()
    train_3dgs(args.source_path, args.model_path, args.iterations)


if __name__ == "__main__":
    main()
