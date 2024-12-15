from common.main_core import create_app
from app.metrics.block_latency import WsBlockLatencyMetric
from app.metrics.eth_call_latency import EthCallLatencyMetric
from app.metrics.method_call_latency import HttpBlockNumberLatencyMetric, HttpGasPriceLatencyMetric




registered_metrics = {
    "Ethereum": [
        (WsBlockLatencyMetric, "response_latency_seconds"),
        (EthCallLatencyMetric, "response_latency_seconds"),
        (HttpBlockNumberLatencyMetric, "response_latency_seconds"),
        (HttpGasPriceLatencyMetric, "response_latency_seconds"),
    ],
    "Base": [
        (WsBlockLatencyMetric, "response_latency_seconds"),
        (EthCallLatencyMetric, "response_latency_seconds"),
        (HttpBlockNumberLatencyMetric, "response_latency_seconds"),
        (HttpGasPriceLatencyMetric, "response_latency_seconds"),
    ]
}

CONFIG_PATH = "app/config/endpoints.json"

app = create_app(CONFIG_PATH, registered_metrics)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)