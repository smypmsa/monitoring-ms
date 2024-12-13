import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from dotenv import load_dotenv

from app.routers import metrics




load_dotenv()

API_USERNAME = os.getenv("API_USERNAME")
API_PASSWORD = os.getenv("API_PASSWORD")

app = FastAPI(title="API Gateway for Blockchain Metrics")
security = HTTPBasic()

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != API_USERNAME or credentials.password != API_PASSWORD:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
        )

    return credentials.username

@app.get("/metrics", response_class=PlainTextResponse)
async def get_metrics(username: str = Depends(verify_credentials)):
    return await metrics.get_metrics()