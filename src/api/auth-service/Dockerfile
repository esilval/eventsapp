FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias primero para aprovechar la caché de capas.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# DATABASE_URL debe apuntar a PostgreSQL en producción, p.ej.:
#   postgresql+psycopg2://user:pass@host:5432/eventsapp
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]
