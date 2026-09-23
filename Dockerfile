# LeadForge Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY leadforge.py leadforge_report.py ./

# Default entrypoint
ENTRYPOINT ["python3", "leadforge.py"]
CMD ["--help"]