from abc import ABC, abstractmethod
import logging

import asyncio




class BaseMetric(ABC):
    """
    Abstract base class for all metrics, defining common properties and methods.
    """
    
    _instances = []

    def __init__(self, metric_name: str, blockchain_name: str, provider: str, http_endpoint: str, ws_endpoint: str, timeout: int, interval: int, extra_params: dict = None):
        self.metric_name = metric_name
        self.blockchain_name = blockchain_name
        self.provider = provider
        self.http_endpoint = http_endpoint
        self.ws_endpoint = ws_endpoint
        self.timeout = timeout
        self.interval = interval
        self.retry_interval = interval
        self.extra_params = extra_params or {}

        self.latest_values = {}
        self.status = "success"

        self.__class__._instances.append(self)

    @classmethod
    def get_all_instances(cls):
        """
        Get all instances of the metric classes.
        """
        return cls._instances

    @classmethod
    def get_all_latest_values(cls):
        """
        Retrieve the latest values from all registered metric instances.
        """
        all_latest_values = []
        for metric_instance in cls._instances:
            for metric_id, value in metric_instance.latest_values.items():
                all_latest_values.append(f"{metric_instance.metric_name}_{metric_id}{{provider=\"{metric_instance.provider}\", blockchain=\"{metric_instance.blockchain_name}\", status=\"{metric_instance.status}\"}} {value}")
        return all_latest_values

    @abstractmethod
    async def collect_metric(self):
        """
        Abstract method for collecting the metric.
        """
        pass

    @abstractmethod
    def process_data(self, data):
        """
        Abstract method for processing data received from an endpoint.
        """
        pass

    def get_prometheus_format(self):
        """
        Return the metric in Prometheus format, including status.
        """
        if self.latest_value is None:
            raise ValueError("Metric value is not set yet.")
        
        return f'{self.metric_name}{{blockchain="{self.blockchain_name}", provider="{self.provider}", status="{self.status}"}} {self.latest_value}'

    async def update_metric(self, value, metric_id="default"):
        """
        Update the metric with the latest value and status.
        Supports multiple metric types for the same instance (e.g., latency, success rate).
        """
        self.status = "success"
        self.latest_values[metric_id] = value
        logging.info(f"Updated metric {self.metric_name}_{metric_id} for {self.provider} with value {value} and status {self.status}")
    
    async def handle_error(self, e: Exception):
        """
        Handle errors gracefully with retry logic and logging.
        """
        self.status = "failed"
        logging.error(f"Error in {self.blockchain_name} ({self.provider}): {str(e)}")
        logging.debug(f"Retrying in {self.retry_interval} seconds...")
        await asyncio.sleep(self.retry_interval)


class WebSocketMetric(BaseMetric):
    """
    Base class for WebSocket-based metrics with reconnection logic.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @abstractmethod
    async def connect(self):
        """
        Establish a WebSocket connection.
        """
        pass

    @abstractmethod
    async def subscribe(self):
        """
        Subscribe to WebSocket messages.
        """
        pass

    @abstractmethod
    async def listen_for_data(self):
        """
        Listen for WebSocket messages.
        """
        pass

    async def collect_metric(self):
        """
        Continuously collect data from WebSocket with reconnection logic.
        """
        while True:
            try:
                websocket = await self.connect()  # Await the coroutine directly
                await self.subscribe(websocket)

                while True:
                    data = await self.listen_for_data(websocket)

                    if data:
                        metric_values = self.process_data(data)
                        for metric_value in metric_values:
                            await self.update_metric(value=metric_value["value"], metric_id=metric_value["key"])

            except Exception as e:
                await self.handle_error(e)


class HttpMetric(BaseMetric):
    """
    Base class for HTTP-based metrics.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @abstractmethod
    async def fetch_data(self):
        """
        Fetch data via an HTTP request.
        """
        pass

    async def collect_metric(self):
        """
        Collect metric by making an HTTP request.
        """
        while True:
            try:
                data = await self.fetch_data()
                
                if data:
                    metric_values = self.process_data(data)
                    for metric_value in metric_values:
                        await self.update_metric(value=metric_value["value"], metric_id=metric_value["key"])

            except Exception as e:
                await self.handle_error(e)

            await asyncio.sleep(self.interval)
