FROM python:3.11-slim

# Create a non-root user and group
RUN groupadd -r apiuser && useradd -r -g apiuser apiuser

WORKDIR /app

# Install runtime dependencies (libpq5 instead of dev package)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Change ownership of the app directory to the non-root user
RUN chown -R apiuser:apiuser /app

# Switch to the non-root user
USER apiuser

EXPOSE 8000

# Use 4 workers for production concurrency, bound to all interfaces
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
