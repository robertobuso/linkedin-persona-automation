FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN ls -la /app 
# DEBUG 1: Check if requirements.txt is here
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
RUN ls -la /app 
# DEBUG 2: Check if app/ is here
RUN ls -la /app/app 
# DEBUG 3: Check contents of /app/app

COPY alembic.ini .
RUN ls -la /app 
# DEBUG 4: Check if alembic.ini is here
COPY alembic ./alembic
RUN ls -la /app 
# DEBUG 5: Check if alembic/ is here
RUN ls -la /app/alembic 
# DEBUG 6: Check contents of /app/alembic

COPY backend/entrypoint.sh .
RUN ls -la /app 
# DEBUG 7: Check if entrypoint.sh is here and its permissions

RUN chmod +x /app/entrypoint.sh 
# This is the failing line

ENV PYTHONPATH=/app

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]