from app.metrics.method_call_latency import (
    HttpGetBlockHeaderLatency,
    HttpGetConsensusBlockLatency,
    HttpRunGetMethodLatency,
)

from common.main_core import create_app

registered_metrics = {
    "TON": [
        (HttpGetConsensusBlockLatency, "response_latency_seconds"),
        (HttpGetBlockHeaderLatency, "response_latency_seconds"),
        (HttpRunGetMethodLatency, "response_latency_seconds"),
    ]
}

CONFIG_PATH = "endpoints.json"

app = create_app(CONFIG_PATH, registered_metrics)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
