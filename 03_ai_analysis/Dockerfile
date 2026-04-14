FROM pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p output models/weights

ENTRYPOINT ["python", "detect_elements.py"]
