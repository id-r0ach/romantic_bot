#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."

until python -c "import os, socket; socket.create_connection((os.getenv('POSTGRES_HOST', 'localhost'), int(os.getenv('POSTGRES_PORT', '5432'))), timeout=2).close()"; do
  echo "PostgreSQL is not ready yet, waiting 2 seconds..."
  sleep 2
done

echo "PostgreSQL is available."

echo "Applying Alembic migrations..."
alembic upgrade head

echo "Starting bot..."
exec python main.py