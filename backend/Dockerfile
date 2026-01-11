FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir fastapi uvicorn sqlalchemy psycopg2-binary celery rabbitmq-client python-dotenv

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
