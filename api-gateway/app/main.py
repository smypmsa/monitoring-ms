from fastapi import FastAPI
from app.routers import metrics




app = FastAPI(title="API Gateway for Blockchain Metrics")
app.include_router(metrics.router, prefix="/metrics", tags=["Metrics"])