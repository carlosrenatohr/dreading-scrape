FROM python:3.11-slim

WORKDIR /app

# Install dependencies first so they are cached across code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Batch job: fetch, parse and persist the readings, then exit.
CMD ["python", "lectura.py"]
