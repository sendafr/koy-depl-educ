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
#COPY --from=node_builder /app/frontend/dist ./frontend_dist

# Copy and chmod start.sh
COPY src_api/start.sh /start.sh
RUN chmod +x /start.sh

# Create directories
RUN mkdir -p /app/staticfiles /app/media /app/tmp

EXPOSE 8000

# Use the startup script
CMD ["/start.sh"]