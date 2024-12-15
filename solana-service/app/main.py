from app.metrics.block_latency import WsBlockLatencyMetric
from app.metrics.method_call_latency import (
    HttpGetRecentBlockhashLatencyMetric,
    HttpGetRecentSlotLatencyMetric,
    HttpSimulateTransactionLatencyMetric,
)

from common.main_core import create_app

registered_metrics = {
    "Solana": [
        #(WsBlockLatencyMetric, "response_latency_seconds"),
        (HttpGetRecentBlockhashLatencyMetric, "response_latency_seconds"),
        (HttpGetRecentSlotLatencyMetric, "response_latency_seconds"),
        (HttpSimulateTransactionLatencyMetric, "response_latency_seconds"),
    ]
}

CONFIG_PATH = "endpoints.json"

app = create_app(CONFIG_PATH, registered_metrics)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
