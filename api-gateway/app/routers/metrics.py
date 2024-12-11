from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from app.services.evm_service import EVMService




router = APIRouter()

@router.get("/", response_class=PlainTextResponse)
async def get_metrics():
    """
    Fetch metrics from the EVM service and return them as plain text.
    """
    try:
        service = EVMService()
        metrics = await service.fetch_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))