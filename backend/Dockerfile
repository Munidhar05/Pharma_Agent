FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

WORKDIR /app

# Install system dependencies (including build tools for compiled libraries)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code and scripts
COPY backend/ /app/backend/
COPY scripts/ /app/scripts/

# Create volume directories
RUN mkdir -p /app/uploads /app/generated_resumes

EXPOSE 8000

CMD ["sh", "-c", "python scripts/init_db.py && python scripts/seed_data.py && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"]

