FROM python:3.9-slim

WORKDIR /app

COPY solana-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY solana-service/app ./app
COPY solana-service/endpoints.json .
COPY common ./common

ENV PYTHONPATH="/app"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]