#!/bin/sh
set -e # Exit immediately if a command exits with a non-zero status.

echo "Waiting for database to be ready at postgres:5432..."
# Use a loop with pg_isready or netcat
# This assumes postgresql-client is installed in your Docker image (it is, from your Dockerfile)
while ! pg_isready -h postgres -p 5432 -q -U "$POSTGRES_USER"; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done
>&2 echo "Postgres is up - continuing..."

echo "Running database migrations..."
alembic -c /app/alembic.ini upgrade head # Use the path to alembic.ini inside the container

echo "Starting application..."
exec "$@" # This will execute the CMD from docker-compose.yml (uvicorn ...)