from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from app.services.ethereum_service import EthereumService




router = APIRouter()

@router.get("/", response_class=PlainTextResponse)
async def get_metrics():
    """
    Fetch metrics from the Ethereum service and return them as plain text.
    """
    try:
        service = EthereumService()
        metrics = await service.fetch_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))