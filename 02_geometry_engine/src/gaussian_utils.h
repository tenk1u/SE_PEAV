#pragma once
/**
 * gaussian_utils.h
 * ----------------
 * Declaraciones públicas de las utilidades para gaussianas 3D.
 */

#include <Eigen/Dense>
#include <string>
#include <vector>

namespace geometry {

/**
 * Convierte un cuaternión (qw, qx, qy, qz) a una matriz de rotación 3×3.
 * El cuaternión se normaliza automáticamente.
 */
Eigen::Matrix3f quaternion_to_rotation(float qw, float qx, float qy, float qz);

/**
 * Calcula la matriz de covarianza 3D de una gaussiana a partir de
 * su vector de escala (sx, sy, sz) y su orientación en cuaternión.
 */
Eigen::Matrix3f compute_covariance(
    float sx, float sy, float sz,
    float qw, float qx, float qy, float qz);

/**
 * Guarda una nube de puntos en formato PLY (binario little-endian).
 * @param filepath  Ruta del archivo de salida.
 * @param positions Vector de posiciones 3D.
 */
void save_ply(const std::string& filepath,
              const std::vector<Eigen::Vector3f>& positions);

}  // namespace geometry
