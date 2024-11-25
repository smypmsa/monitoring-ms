from abc import ABC, abstractmethod
import logging

import asyncio




class BaseMetric(ABC):
    """
    Abstract base class for all metrics, defining common properties and methods.
    """
    
    _instances = []

    def __init__(self, metric_name: str, blockchain_name: str, provider: str, http_endpoint: str, ws_endpoint: str, timeout: int, interval: int):
        self.metric_name = metric_name
        self.blockchain_name = blockchain_name
        self.provider = provider
        self.http_endpoint = http_endpoint
        self.ws_endpoint = ws_endpoint
        self.timeout = timeout
        self.interval = interval
        self.retry_interval = interval
        self.latest_value = None

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
            if hasattr(metric_instance, 'latest_value'):
                all_latest_values.append(f"{metric_instance.metric_name}{{provider=\"{metric_instance.provider}\", blockchain=\"{metric_instance.blockchain_name}\"}} {metric_instance.latest_value}")
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
        Return the metric in Prometheus format.
        """
        if self.latest_value is None:
            raise ValueError("Metric value is not set yet.")
        
        return f'{self.metric_name}{{blockchain="{self.blockchain_name}", provider="{self.provider}"}} {self.latest_value}'

    @abstractmethod
    async def update_metric(self, value):
        """
        Update the metric with the latest value.
        """
        self.latest_value = value
    
    async def handle_error(self, e: Exception):
        """
        Handle errors gracefully with retry logic and logging.
        """
        logging.error(f"Error in {self.blockchain_name} ({self.provider}): {str(e)}")
        logging.info(f"Retrying in {self.retry_interval} seconds...")
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
                    metric_value = self.process_data(data)
                    await self.update_metric(metric_value)

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
                self.latest_value = self.process_data(data)
                await self.update_metric(self.latest_value)

            except Exception as e:
                await self.handle_error(e)

            await asyncio.sleep(self.interval)
