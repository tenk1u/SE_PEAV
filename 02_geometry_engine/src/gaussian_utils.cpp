/**
 * gaussian_utils.cpp
 * ------------------
 * Utilidades C++ para operaciones básicas sobre gaussianas 3D:
 *   - Carga/guardado de nubes de puntos en formato PLY.
 *   - Cálculo de matrices de covarianza 3D a partir de cuaterniones y escalas.
 *
 * Compilar con CMake (ver CMakeLists.txt en el directorio raíz).
 */

#include "gaussian_utils.h"

#include <Eigen/Dense>
#include <cmath>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>

namespace geometry {

// ─── Conversión cuaternión → matriz de rotación ──────────────────────────────

Eigen::Matrix3f quaternion_to_rotation(float qw, float qx, float qy, float qz) {
    // Normalizar
    float norm = std::sqrt(qw * qw + qx * qx + qy * qy + qz * qz);
    if (norm < 1e-8f) {
        throw std::invalid_argument("Cuaternión con norma casi cero.");
    }
    qw /= norm; qx /= norm; qy /= norm; qz /= norm;

    Eigen::Matrix3f R;
    R << 1 - 2*(qy*qy + qz*qz),     2*(qx*qy - qz*qw),     2*(qx*qz + qy*qw),
             2*(qx*qy + qz*qw), 1 - 2*(qx*qx + qz*qz),     2*(qy*qz - qx*qw),
             2*(qx*qz - qy*qw),     2*(qy*qz + qx*qw), 1 - 2*(qx*qx + qy*qy);
    return R;
}

// ─── Matriz de covarianza 3D a partir de escala y cuaternión ─────────────────

Eigen::Matrix3f compute_covariance(
    float sx, float sy, float sz,
    float qw, float qx, float qy, float qz)
{
    Eigen::Matrix3f R = quaternion_to_rotation(qw, qx, qy, qz);
    Eigen::DiagonalMatrix<float, 3> S(sx * sx, sy * sy, sz * sz);
    return R * S * R.transpose();
}

// ─── Escritura de nube de puntos en formato PLY (binario little-endian) ──────

void save_ply(const std::string& filepath,
              const std::vector<Eigen::Vector3f>& positions)
{
    std::ofstream ofs(filepath, std::ios::binary);
    if (!ofs.is_open()) {
        throw std::runtime_error("No se pudo abrir para escritura: " + filepath);
    }

    ofs << "ply\n"
        << "format binary_little_endian 1.0\n"
        << "element vertex " << positions.size() << "\n"
        << "property float x\n"
        << "property float y\n"
        << "property float z\n"
        << "end_header\n";

    for (const auto& p : positions) {
        ofs.write(reinterpret_cast<const char*>(p.data()), 3 * sizeof(float));
    }

    std::cout << "[OK] PLY guardado en '" << filepath
              << "' (" << positions.size() << " puntos)\n";
}

}  // namespace geometry
