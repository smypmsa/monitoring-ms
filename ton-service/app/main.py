import asyncio
import logging
import sys

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from contextlib import asynccontextmanager

from common.config_loader import ConfigLoader
from common.factory import MetricFactory
from common.metric_base import BaseMetric, MetricConfig

from app.metrics.method_call_latency import HttpGetConsensusBlockLatency
from app.metrics.method_call_latency import HttpGetBlockHeaderLatency
from app.metrics.method_call_latency import HttpRunGetMethodLatency




logging.basicConfig(level=logging.INFO, stream=sys.stdout) 

CONFIG_PATH = "app/config/endpoints.json"

MetricFactory.register(
    {
        "TON": [
            (HttpGetConsensusBlockLatency, "response_latency_seconds"),
            (HttpGetBlockHeaderLatency, "response_latency_seconds"),
            (HttpRunGetMethodLatency, "response_latency_seconds")
        ]
    }
)

async def collect_metrics(provider, source_region, timeout, interval, extra_params):
    metrics = MetricFactory.create_metrics(
        blockchain_name=provider["blockchain"],
        config=MetricConfig(timeout=timeout, interval=interval),
        provider=provider["name"],
        source_region=source_region,
        target_region=provider["region"],
        ws_endpoint=provider["websocket_endpoint"],
        http_endpoint=provider["http_endpoint"],
        extra_params=extra_params
    )
    tasks = [asyncio.create_task(metric.collect_metric()) for metric in metrics]
    await asyncio.gather(*tasks)

async def main():
    config = ConfigLoader.load_config(CONFIG_PATH)
    tasks = [
        collect_metrics(
            provider,
            config.get("source_region", "default"),
            config.get("timeout"),
            config.get("interval"),
            extra_params=provider.get("data", {})
        ) for provider in config["providers"]
    ]
    await asyncio.gather(*tasks)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifecycle: start and stop tasks."""
    task = asyncio.create_task(main())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)

@app.get("/metrics", response_class=PlainTextResponse)
async def get_metrics():
    """Expose metrics in Prometheus-compatible format."""
    all_metrics = BaseMetric.get_all_latest_values()
    return "\n".join(all_metrics)