FROM python:3.9-slim

WORKDIR /app

COPY evm-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY evm-service/app ./app
COPY common ./common

ENV PYTHONPATH="/app"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]