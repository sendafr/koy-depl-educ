# --- Stage 0: Frontend build ---
FROM node:20-alpine AS node_builder
WORKDIR /app/frontend
COPY fed-frontend/package*.json ./
RUN npm ci --legacy-peer-deps || npm ci
COPY fed-frontend/ .
RUN npm run build

# --- Stage 1: Python Builder ---
FROM python:3.11-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY src_api/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# --- Stage 2: Runtime ---
FROM python:3.11-slim
WORKDIR /app

# Install runtime deps
RUN apt-get update && apt-get install -y postgresql-client bash && rm -rf /var/lib/apt/lists/*

# Copy Python packages
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy Backend Code
COPY src_api/ .

# Copy Frontend Build
COPY --from=node_builder /app/frontend/dist ./frontend_dist

# Create directories
RUN mkdir -p /app/staticfiles /app/media /app/tmp

EXPOSE 8000

# Run the application directly (assuming src_api contains the entry point)
# Adjust 'python -m src_api' or 'gunicorn' based on your actual entry point
CMD ["python", "-m", "src_api"]