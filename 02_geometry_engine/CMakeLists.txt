cmake_minimum_required(VERSION 3.20)
project(geometry_engine LANGUAGES CXX CUDA)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CUDA_STANDARD 17)

# ─── Dependencias ────────────────────────────────────────────────────────────
find_package(CUDA REQUIRED)
find_package(Eigen3 3.4 REQUIRED NO_MODULE)

# ─── Fuentes ─────────────────────────────────────────────────────────────────
add_library(gaussian_utils SHARED src/gaussian_utils.cpp)
target_include_directories(gaussian_utils PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/src)
target_link_libraries(gaussian_utils PUBLIC Eigen3::Eigen)

# ─── Tests (opcional) ────────────────────────────────────────────────────────
option(BUILD_TESTS "Compilar tests unitarios" OFF)
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()
