FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (cached layer)
COPY api/requirements.txt /app/api/requirements.txt
RUN pip install --no-cache-dir \
    -r api/requirements.txt \
    rich \
    pyfiglet

# Cache bust - change this to force rebuild
ARG CACHEBUST=3
# Copy source code
COPY . .

# Railway sets PORT dynamically
CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
