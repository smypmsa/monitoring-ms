import asyncio
import logging

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from contextlib import asynccontextmanager

from common.config_loader import ConfigLoader
from common.factory import MetricFactory
from common.metric_base import BaseMetric

import app.metrics.block_latency
import app.metrics.http_call_latency




logging.basicConfig(level=logging.INFO)

CONFIG_PATH = "app/config/endpoints.json"

async def collect_metrics(provider, timeout, interval):
    """Collect metrics for both WebSocket and HTTP endpoints."""
    logging.debug(f"Starting metrics collection for provider: {provider['name']}")
    
    metrics = MetricFactory.create_metrics(
        blockchain_name=provider["blockchain"],
        provider=provider["name"],
        timeout=timeout,
        interval=interval,
        ws_endpoint=provider.get("websocket_endpoint"),
        http_endpoint=provider.get("http_endpoint")
    )

    logging.debug(f"Created metrics: {metrics}")

    tasks = [asyncio.create_task(metric.collect_metric()) for metric in metrics]

    try:
        await asyncio.gather(*tasks)

    except Exception as e:
        logging.error(f"Error collecting metrics for {provider['name']}: {e}")

async def main():
    """Launch metric collection tasks for all providers."""
    config = ConfigLoader.load_config(CONFIG_PATH)

    tasks = [
        collect_metrics(provider,
                        config.get("timeout", 30),
                        config.get("interval", 60))
        for provider in config["providers"]
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