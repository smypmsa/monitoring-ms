import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from common.base_metric import BaseMetric
from common.config_loader import ConfigLoader
from common.factory import MetricFactory
from common.metric_config import MetricConfig

logging.basicConfig(level=logging.INFO, stream=sys.stdout)


async def collect_metrics(
    provider: dict,
    source_region: str,
    timeout: int,
    interval: int,
    extra_params: dict,
):
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
            extra_params=extra_params,
        )

        logging.debug(f"Created metrics: {metrics}")

        tasks = [asyncio.create_task(metric.collect_metric()) for metric in metrics]
        await asyncio.gather(*tasks)

    except Exception as e:
        logging.error(f"Error collecting metrics for {provider['name']}: {e}")


async def main(config_path: str, registered_metrics: dict):
    config = ConfigLoader.load_config(config_path)
    MetricFactory.register(registered_metrics)

    tasks = [
        collect_metrics(
            provider,
            config.get("source_region", "default"),
            config.get("timeout", 50),
            config.get("interval", 60),
            extra_params={"tx_data": provider.get("data")},
        )
        for provider in config["providers"]
    ]

    await asyncio.gather(*tasks)


@asynccontextmanager
async def lifespan(app: FastAPI, config_path: str, registered_metrics: dict):
    """Manage app lifecycle: start and stop tasks."""
    task = asyncio.create_task(main(config_path, registered_metrics))
    yield
    task.cancel()


def create_app(config_path: str, registered_metrics: dict) -> FastAPI:
    app = FastAPI(lifespan=lambda app: lifespan(app, config_path, registered_metrics))

    @app.get("/metrics", response_class=PlainTextResponse)
    async def get_metrics():
        """Expose metrics in Prometheus-compatible format."""
        all_metrics = BaseMetric.get_all_latest_values()
        return "\n".join(all_metrics)

    return app
