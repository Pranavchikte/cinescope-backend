FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user (production security)
RUN useradd -m -u 1000 appuser

# Copy requirements
COPY requirements.txt .



# Install CPU-only PyTorch first (prevents CUDA install)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install all dependencies EXCEPT sentence-transformers
RUN grep -v "sentence-transformers" requirements.txt > req.txt \
    && pip install --no-cache-dir -r req.txt

# Install sentence-transformers WITHOUT heavy dependencies
RUN pip install --no-cache-dir sentence-transformers==3.3.1 --no-deps



# Copy application
COPY . .

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

EXPOSE 8000

# Command will be overridden by docker-compose
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]