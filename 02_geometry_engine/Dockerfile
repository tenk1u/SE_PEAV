FROM nvidia/cuda:12.1.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

# Dependencias de sistema: COLMAP, CMake, Python
RUN apt-get update && apt-get install -y --no-install-recommends \
        colmap \
        cmake \
        build-essential \
        libeigen3-dev \
        python3.11 \
        python3-pip \
        git \
    && rm -rf /var/lib/apt/lists/*

# Alias cómodo
RUN ln -sf /usr/bin/python3.11 /usr/bin/python && \
    ln -sf /usr/bin/pip3       /usr/bin/pip

WORKDIR /app
COPY . .

# Construir la librería C++
RUN cmake -B build -DCMAKE_BUILD_TYPE=Release && \
    cmake --build build --parallel "$(nproc)"

ENTRYPOINT ["python", "colmap_runner.py"]
