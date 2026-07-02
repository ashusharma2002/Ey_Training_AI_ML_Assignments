# infra/Dockerfile — Credit Risk Intelligence Platform
# ============================================================
# Production-ready container for the Streamlit application.
#
# BUILD:  docker build -f infra/Dockerfile -t credit-risk-platform .
# RUN:    docker run -p 8501:8501 --env-file .env credit-risk-platform
# ACCESS: http://localhost:8501
# ============================================================
FROM python:3.11-slim

ARG DEBIAN_FRONTEND=noninteractive

# System dependencies required for PyMuPDF, cryptography (bcrypt), etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    libffi-dev \
    libssl-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first — better Docker layer caching.
# If requirements.txt hasn't changed, this layer is reused on rebuild.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy all application code
COPY . .

# Create runtime directories that the app expects to exist
RUN mkdir -p data/uploads \
             data/vectorstore/faiss_index \
             data/auth_db \
             data/cities \
             logs

# Streamlit configuration — headless mode, dark theme
RUN mkdir -p /root/.streamlit
COPY infra/streamlit_config.toml /root/.streamlit/config.toml

# Expose Streamlit port
EXPOSE 8501

# Health check — Azure App Service and other platforms use this
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Start the app
CMD ["streamlit", "run", "app.py", \
     "--server.address=0.0.0.0", \
     "--server.port=8501", \
     "--server.headless=true"]
