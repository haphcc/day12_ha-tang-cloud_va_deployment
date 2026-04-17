#!/bin/bash
# Railway start script

# Determine port (Railway sets PORT env var)
PORT=${PORT:-8000}

# Start the application
exec uvicorn app:app --host 0.0.0.0 --port $PORT
