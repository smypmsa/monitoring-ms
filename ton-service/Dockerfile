FROM python:3.9-slim

WORKDIR /app

COPY ton-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ton-service/app ./app
COPY ton-service/endpoints.json .
COPY common ./common
COPY .env /app/.env

ENV PYTHONPATH="/app"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]