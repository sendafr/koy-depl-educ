# --- Stage 0: Frontend build (Vite) ---
FROM node:20-alpine AS node_builder

WORKDIR /app/frontend

# Install frontend dependencies and build
COPY fed-frontend/package.json fed-frontend/package-lock.json* ./
RUN npm ci --legacy-peer-deps || npm ci
COPY fed-frontend/ .
RUN npm run build

# --- Stage 1: Builder (Install dependencies) ---
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies (needed for compiling C extensions like psycopg2)
RUN apt-get update && apt-get install -y \
  gcc \
  libpq-dev \
  && rm -rf /var/lib/apt/lists/*

COPY src_api/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# --- Stage 2: Runtime (Lean production image) ---
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only (no gcc needed here)
RUN apt-get update && apt-get install -y \
    postgresql-client \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY src_api/ .

# Copy built frontend static assets into the image
COPY --from=node_builder /app/frontend/dist ./frontend_dist

# Create required directories
RUN mkdir -p /app/tmp /app/logs /app/media /app/staticfiles

# Copy startup script with DB wait logic
COPY src_api/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 8000

CMD ["/start.sh"]