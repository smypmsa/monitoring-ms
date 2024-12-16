FROM python:3.9-slim

WORKDIR /app

COPY evm-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY evm-service/app ./app
COPY evm-service/endpoints.json .
COPY common ./common
COPY .env /app/.env

ENV PYTHONPATH="/app"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]