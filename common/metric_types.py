import asyncio
import logging
import time
from abc import abstractmethod
from typing import Any, Optional

import aiohttp
import websockets

from common.base_metric import BaseMetric
from common.metric_config import MetricConfig, MetricLabelKey, MetricLabels

MAX_LATENCY_SEC = 30


class WebSocketMetric(BaseMetric):
    """
    WebSocket-based metric for collecting data from a WebSocket connection.
    """

    def __init__(
        self,
        metric_name: str,
        labels: MetricLabels,
        config: MetricConfig,
        ws_endpoint: Optional[str] = None,
        http_endpoint: Optional[str] = None,
    ) -> None:
        super().__init__(metric_name, labels, config, ws_endpoint, http_endpoint)
        self.last_block_hash: Optional[str] = None
        self.subscription_id: Optional[int] = None
        self.last_value_timestamp = None

    @abstractmethod
    async def subscribe(self, websocket: Any) -> None:
        """Subscribes to WebSocket messages."""
        pass

    @abstractmethod
    async def unsubscribe(self, websocket: Any) -> None:
        """Unsubscribe from WebSocket subscription."""
        pass

    @abstractmethod
    async def listen_for_data(self, websocket: Any) -> Optional[Any]:
        """Listens for data on the WebSocket connection."""
        pass

    async def connect(self) -> Any:
        """
        Establish WebSocket connection.
        """
        try:
            websocket = await websockets.connect(
                self.ws_endpoint,
                ping_timeout=self.config.timeout,
                close_timeout=self.config.timeout,
            )
            logging.debug(
                f"Connected to {self.ws_endpoint} for {self.labels.get_label(MetricLabelKey.BLOCKCHAIN)}"
            )
            return websocket

        except Exception as e:
            logging.error(f"Error connecting to WebSocket: {str(e)}")
            raise

    async def collect_metric(self) -> None:
        """Collect one websocket message per interval."""
        while True:
            websocket = None
            try:
                websocket = await self.connect()
                await self.subscribe(websocket)

                # Wait for single message
                data = await self.listen_for_data(websocket)
                if data:
                    latency = self.process_data(data)
                    if latency > MAX_LATENCY_SEC:
                        raise ValueError(
                            f"Latency {latency}s exceeds maximum allowed {MAX_LATENCY_SEC}s"
                        )
                    await self.update_metric_value(latency)

            except Exception as e:
                await self.handle_error(e)

            finally:
                if websocket:
                    try:
                        await self.unsubscribe(websocket)
                        await websocket.close()
                    except Exception as e:
                        logging.error(f"Error closing websocket: {str(e)}")

                await asyncio.sleep(self.config.interval)


class HttpMetric(BaseMetric):
    """
    HTTP-based metric for collecting data via HTTP requests.
    """

    @abstractmethod
    async def fetch_data(self) -> Optional[Any]:
        """Fetches data from the HTTP endpoint."""
        pass

    async def collect_metric(self) -> None:
        """Collects HTTP metrics at fixed intervals."""
        while True:
            try:
                if data := await self.fetch_data():
                    latency = self.process_data(data)
                    if latency > MAX_LATENCY_SEC:
                        raise ValueError(
                            f"Latency {latency}s exceeds maximum allowed {MAX_LATENCY_SEC}s"
                        )
                    await self.update_metric_value(latency)
            except Exception as e:
                await self.handle_error(e)
            finally:
                await asyncio.sleep(self.config.interval)


class HttpCallLatencyMetricBase(HttpMetric):
    """
    Base class for HTTP-based Ethereum endpoint latency metrics.
    Subclasses will specify the JSON-RPC method and its parameters.
    """

    def __init__(
        self,
        metric_name: str,
        labels: MetricLabels,
        config: MetricConfig,
        method: str,
        method_params: dict = None,
        **kwargs,
    ):
        """
        Initialize the base class with the necessary configuration.

        :param method_params: Additional parameters to pass to the JSON-RPC method (optional).
        """
        http_endpoint = kwargs.get("http_endpoint")
        super().__init__(
            metric_name=metric_name,
            labels=labels,
            config=config,
            http_endpoint=http_endpoint,
        )
        self.method = method
        self.method_params = method_params or None
        self.labels.update_label(MetricLabelKey.API_METHOD, method)

    async def fetch_data(self):
        """
        Perform the HTTP request and return the response time for the specified method.
        """
        async with aiohttp.ClientSession() as session:
            start_time = time.monotonic()

            request_data = {
                "id": 1,
                "jsonrpc": "2.0",
                "method": self.method,
            }
            if self.method_params:
                request_data["params"] = self.method_params

            async with session.post(
                self.http_endpoint,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                json=request_data,
                timeout=self.config.timeout,
            ) as response:
                if response.status == 200:
                    await response.json()
                    latency = time.monotonic() - start_time
                    return latency

                else:
                    raise ValueError(f"Unexpected status code: {response.status}.")

    def process_data(self, value):
        return value
