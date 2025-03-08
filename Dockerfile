FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY my_proof/ ./my_proof/

# Create input and output directories
RUN mkdir -p /input /output

# Run as non-root user for security
RUN useradd -m appuser
USER appuser

ENTRYPOINT ["python", "-m", "my_proof"] 