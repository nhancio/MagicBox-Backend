FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Copy application code
COPY src/ ./src/
COPY migrations/ ./migrations/

# Set Python path
ENV PYTHONPATH=/app/src

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
