from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from app.routers import metrics




app = FastAPI(title="API Gateway for Blockchain Metrics")

@app.get("/metrics", response_class=PlainTextResponse)
async def get_metrics():
    return await metrics.get_metrics()