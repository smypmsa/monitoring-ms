import asyncio
import logging

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from contextlib import asynccontextmanager

from common.config_loader import ConfigLoader
from common.factory import MetricFactory
import app.metrics.block_latency
#import app.metrics.http_call_latency




logging.basicConfig(level=logging.DEBUG)

CONFIG_PATH = "app/config/endpoints.json"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application lifespan:
    - Starts metrics collection tasks on startup
    - Cancels tasks on shutdown
    """
    logging.debug("Starting metrics collection tasks...")
    task = asyncio.create_task(main())
    yield  # Execution pauses here until app shutdown
    task.cancel()  # Ensure graceful shutdown of background tasks

app = FastAPI(lifespan=lifespan)

# Store live metrics in a coroutine-safe list for dynamic exposure
metrics_output = []

@app.get("/metrics", response_class=PlainTextResponse)
async def get_metrics():
    """
    Expose Prometheus-compatible metrics dynamically.
    """
    logging.debug(f"Metrics endpoint called. Current metrics: {metrics_output}")
    return "\n".join(metrics_output)

async def collect_metrics(provider):
    """
    Continuously collect metrics for a single provider.
    Append the latest metrics to the global metrics_output.
    """
    metric = MetricFactory.create(
        blockchain_name=provider["blockchain"],
        websocket_endpoint=provider.get("websocket_endpoint"),
        http_endpoint=provider.get("http_endpoint"),
        provider=provider["name"],
        timeout=provider.get("timeout", 15),
        interval=provider.get("interval", 60)
    )

    while True:
        try:
            result = await metric.collect_metric()
            # Replace existing metric for the same provider
            metrics_output[:] = [m for m in metrics_output if provider["name"] not in m]
            metrics_output.append(result)

        except Exception as e:
            logging.error(f"Error collecting metrics for {provider['name']}: {e}")

        await asyncio.sleep(provider.get("interval", 60))

async def main():
    """
    Launch metric collection tasks for all configured providers.
    """
    config = ConfigLoader.load_config(CONFIG_PATH)

    tasks = [
        collect_metrics(provider)
        for provider in config["providers"]
    ]

    await asyncio.gather(*tasks)