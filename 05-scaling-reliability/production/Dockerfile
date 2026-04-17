FROM python:3.11-slim

WORKDIR /app

# Install only runtime deps needed by the stateless demo app.
RUN pip install --no-cache-dir fastapi uvicorn redis

COPY 05-scaling-reliability/production/app.py /app/app.py
COPY 05-scaling-reliability/production/utils /app/utils

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
