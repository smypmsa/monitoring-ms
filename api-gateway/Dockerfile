FROM python:3.9-slim

WORKDIR /app

COPY api-gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api-gateway/app ./app
COPY common ./common

ENV PYTHONPATH="/app"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--ssl-keyfile", "/etc/letsencrypt/live/intelautoconsult.com/privkey.pem", "--ssl-certfile", "/etc/letsencrypt/live/intelautoconsult.com/fullchain.pem"]