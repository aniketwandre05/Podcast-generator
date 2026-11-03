# ==========================================
# Stage 1: Build Frontend
# ==========================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci || npm install

COPY frontend/ ./
RUN npm run build

# ==========================================
# Stage 2: Backend & Production Runtime
# ==========================================
FROM python:3.11-slim

# Silence pip root user warning & enable real-time unbuffered logging
ENV PIP_ROOT_USER_ACTION=ignore
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000

# Install system dependencies including ffmpeg for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy python requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application and assets
COPY app/ ./app/
COPY assets/ ./assets/

# Copy built frontend assets from stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create runtime data directories
RUN mkdir -p data/storage data/tts_cache data/uploads samples assets/music

EXPOSE 8000

# Dynamically bind to the PORT assigned by Render / Cloud, defaulting to 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
