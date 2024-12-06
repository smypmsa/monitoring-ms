import asyncio
import logging
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from contextlib import asynccontextmanager

from common.config_loader import ConfigLoader
from common.factory import MetricFactory
from common.metric_base import BaseMetric, MetricConfig

from app.metrics.block_latency import EthereumBlockLatencyMetric
from app.metrics.eth_call_latency import EthCallLatencyMetric
from app.metrics.http_call_latency import HttpCallLatencyMetric




logging.basicConfig(level=logging.INFO)

CONFIG_PATH = "app/config/endpoints.json"
SECRETS_PATH = "app/secrets/secrets.json"

MetricFactory.register(
    {
        "Ethereum": [
            (EthereumBlockLatencyMetric, "ws_block_reception_latency_seconds"),
            (EthCallLatencyMetric, "http_request_latency_seconds"),
            (HttpCallLatencyMetric, "http_request_latency_seconds"),
        ]
    }
)

async def collect_metrics(provider, source_region, timeout, interval, extra_params: dict):
    """Collect metrics for both WebSocket and HTTP endpoints."""
    logging.debug(f"Starting metrics collection for provider: {provider['name']}")

    try:
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

        logging.debug(f"Created metrics: {metrics}")

        tasks = [asyncio.create_task(metric.collect_metric()) for metric in metrics]
        await asyncio.gather(*tasks)

    except Exception as e:
        logging.error(f"Error collecting metrics for {provider['name']}: {e}")


async def main():
    """Launch metric collection tasks for all providers."""
    config = ConfigLoader.load_config(CONFIG_PATH)
    secrets = ConfigLoader.load_secrets(SECRETS_PATH)

    tasks = [
        collect_metrics(
            provider,
            config.get("source_region", "default"),
            config.get("timeout", 50),
            config.get("interval", 60),
            extra_params={
                'tx_data': provider.get('data'),
                'private_key': secrets.get(provider.get('data', {}).get('secret_index'))
            })
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