import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager

import aiohttp
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from common.base_metric import BaseMetric
from common.config_loader import ConfigLoader
from common.factory import MetricFactory
from common.metric_config import MetricConfig

logging.basicConfig(level=logging.INFO, stream=sys.stdout)


load_dotenv()

GRAFANA_URL = os.environ.get("GRAFANA_URL")
GRAFANA_USER = os.environ.get("GRAFANA_USER")
GRAFANA_API_KEY = os.environ.get("GRAFANA_API_KEY")
print(GRAFANA_URL)

PUSH_INTERVAL = int(os.environ.get("PUSH_INTERVAL", "60"))
MAX_RETRIES = int(os.environ.get("PUSH_MAX_RETRIES", "3"))
RETRY_DELAY = int(os.environ.get("PUSH_RETRY_DELAY", "10"))


async def collect_metrics(
    provider: dict, source_region: str, timeout: int, interval: int, extra_params: dict
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


async def push_metrics_to_grafana():
    async with aiohttp.ClientSession() as session:
        while True:
            metrics_text = "\n".join(BaseMetric.get_all_latest_values())
            logging.info(f"Pushing {len(BaseMetric.get_all_latest_values())} metrics")
            if metrics_text:
                # content_length = len(metrics_text.encode('utf-8'))
                for attempt in range(1, MAX_RETRIES + 1):
                    try:
                        async with session.post(
                            GRAFANA_URL,
                            headers={
                                "Content-Type": "text/plain"
                                # "Content-Length": str(content_length)
                            },
                            data=metrics_text,
                            auth=aiohttp.BasicAuth(GRAFANA_USER, GRAFANA_API_KEY),
                            timeout=10,
                        ) as response:
                            if response.status in (200, 204):
                                logging.debug("Metrics successfully sent to Grafana.")
                                break
                            else:
                                logging.error(
                                    f"Failed to push metrics (Attempt {attempt}/{MAX_RETRIES}): {response.status}"
                                )
                    except Exception as e:
                        logging.error(
                            f"Error pushing metrics to Grafana (Attempt {attempt}/{MAX_RETRIES}): {e}"
                        )

                    if attempt < MAX_RETRIES:
                        await asyncio.sleep(RETRY_DELAY)
            await asyncio.sleep(PUSH_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI, config_path: str, registered_metrics: dict):
    main_task = asyncio.create_task(main(config_path, registered_metrics))
    push_task = None
    if GRAFANA_URL and GRAFANA_USER and GRAFANA_API_KEY:
        push_task = asyncio.create_task(push_metrics_to_grafana())
    yield
    main_task.cancel()
    if push_task:
        push_task.cancel()


def create_app(config_path: str, registered_metrics: dict) -> FastAPI:
    app = FastAPI(lifespan=lambda a: lifespan(a, config_path, registered_metrics))

    @app.get("/metrics", response_class=PlainTextResponse)
    async def get_metrics():
        """Expose metrics in Prometheus-compatible format."""
        all_metrics = BaseMetric.get_all_latest_values()
        return "\n".join(all_metrics)

    return app
