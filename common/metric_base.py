import logging
import asyncio
import uuid

from enum import Enum
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union




class MetricLabelKey(Enum):
    SOURCE_REGION = "source_region"
    TARGET_REGION = "target_region"
    BLOCKCHAIN = "blockchain"
    PROVIDER = "provider"
    API_METHOD = "api_method"
    RESPONSE_STATUS = "response_status"


class MetricConfig:
    """
    Configuration for the metric, including timeout, interval, etc.

    Attributes:
        timeout (int): The timeout for the metric.
        interval (int): The interval for collecting the metric.
        retry_interval (int): The retry interval in case of failure.
        extra_params (Dict[str, Any]): Extra parameters for the metric.
    """

    def __init__(self, timeout: int, interval: int, retry_interval: int = 30, extra_params: Optional[Dict[str, Any]] = None) -> None:
        self.timeout = timeout
        self.interval = interval
        self.retry_interval = retry_interval
        self.extra_params = extra_params or {}


class MetricLabel:
    """
    Holds a single label for a metric.

    Attributes:
        key (MetricLabelKey): The key for the metric label.
        value (str): The value for the metric label.
    """

    def __init__(self, key: MetricLabelKey, value: str) -> None:
        if not isinstance(key, MetricLabelKey):
            raise ValueError(f"Invalid key, must be an instance of MetricLabelKey Enum: {key}")
        self.key = key
        self.value = value


class MetricLabels:
    """
    Holds a collection of MetricLabel instances for a metric.

    Attributes:
        labels (List[MetricLabel]): A list of MetricLabel instances.
    """

    def __init__(self, source_region: str, target_region: str, blockchain: str, provider: str, api_method: str = "default", response_status: str = "success") -> None:
        self.labels = [
            MetricLabel(MetricLabelKey.SOURCE_REGION, source_region),
            MetricLabel(MetricLabelKey.TARGET_REGION, target_region),
            MetricLabel(MetricLabelKey.BLOCKCHAIN, blockchain),
            MetricLabel(MetricLabelKey.PROVIDER, provider),
            MetricLabel(MetricLabelKey.API_METHOD, api_method),
            MetricLabel(MetricLabelKey.RESPONSE_STATUS, response_status)
        ]

    def get_prometheus_labels(self) -> str:
        """
        Returns a string of Prometheus-style labels.

        Returns:
            str: A string formatted for Prometheus.
        """
        return ",".join(f'{label.key.value}="{label.value}"' for label in self.labels)

    def update_label(self, label_name: MetricLabelKey, new_value: str) -> None:
        """
        Update the value of a label based on the label name.

        Args:
            label_name (MetricLabelKey): The name of the label to update.
            new_value (str): The new value for the label.
        """
        for label in self.labels:
            if label.key == label_name:
                label.value = new_value
                logging.debug(f"Updated label '{label_name.value}' to '{new_value}'")
                return
            
        logging.warning(f"Label '{label_name.value}' not found!")

    def add_label(self, label_name: MetricLabelKey, label_value: str) -> None:
        """
        Adds a new label to the collection.

        Args:
            label_name (MetricLabelKey): The name of the label to add.
            label_value (str): The value of the label to add.
        """
        for label in self.labels:
            if label.key == label_name:
                logging.info(f"Label '{label_name.value}' already exists, updating its value.")
                self.update_label(label_name, label_value)
                return

        self.labels.append(MetricLabel(label_name, label_value))
        logging.info(f"Added new label '{label_name.value}' with value '{label_value}'")

    def get_label(self, label_name: MetricLabelKey) -> Optional[str]:
        """
        Retrieves the value of a label by its key.

        Args:
            label_name (MetricLabelKey): The key of the label to retrieve.

        Returns:
            Optional[str]: The value of the label if found, None otherwise.
        """
        for label in self.labels:
            if label.key == label_name:
                return label.value
            
        return None


class BaseMetric(ABC):
    """
    Abstract base class for metrics that manages collection and Prometheus formatting.

    Attributes:
        metric_name (str): The name of the metric.
        labels (MetricLabels): The labels associated with the metric.
        config (MetricConfig): The configuration for the metric.
        latest_value (Optional[Union[int, float]]): The latest value of the metric.
        endpoint (str): The endpoint (either HTTP or WebSocket) for collecting the metric.
    """
    _instances: List["BaseMetric"] = []

    def __init__(self, metric_name: str, labels: MetricLabels, config: MetricConfig, 
                 ws_endpoint: Optional[str] = None, http_endpoint: Optional[str] = None) -> None:
        self.metric_id = str(uuid.uuid4())  # Generate a unique ID for each metric instance
        self.metric_name = metric_name
        self.labels = labels
        self.config = config
        self.ws_endpoint = ws_endpoint
        self.http_endpoint = http_endpoint
        self.latest_value = None
        self.__class__._instances.append(self)

    @classmethod
    def get_all_instances(cls) -> List["BaseMetric"]:
        """Returns all instances of the metric classes."""
        return cls._instances

    @classmethod
    def get_all_latest_values(cls) -> List[str]:
        """Returns all latest values in Prometheus format."""
        return [
            instance.get_prometheus_format() 
            for instance in cls._instances 
            if instance.latest_value is not None
        ]

    @abstractmethod
    async def collect_metric(self) -> None:
        """Method to collect metrics, must be implemented in subclasses."""
        pass

    @abstractmethod
    def process_data(self, data: Any) -> Union[int, float]:
        """Process data to extract the metric value, to be implemented in subclasses."""
        pass

    def get_prometheus_format(self) -> str:
        """Formats the metric for Prometheus."""
        if self.latest_value is None:
            raise ValueError("Metric value is not set")
        return f'{self.metric_name}{{{self.labels.get_prometheus_labels()}}} {self.latest_value}'

    async def update_metric_value(self, value: Union[int, float]) -> None:
        """Updates the latest value of the metric."""
        self.latest_value = value
        logging.debug(self.get_prometheus_format())

    async def handle_error(self, error: Exception) -> None:
        """Handles errors by updating the status and retrying after a delay."""
        self.labels.update_label(MetricLabelKey.RESPONSE_STATUS, "failed")
        logging.error(f"Error in {self.labels.get_prometheus_labels()}: {str(error)}")
        logging.debug(f"Retrying in {self.config.retry_interval} seconds...")
        await asyncio.sleep(self.config.retry_interval)


class WebSocketMetric(BaseMetric):
    """
    WebSocket-based metric for collecting data from a WebSocket connection.
    """

    @abstractmethod
    async def connect(self) -> Any:
        """Connects to the WebSocket."""
        pass

    @abstractmethod
    async def subscribe(self, websocket: Any) -> None:
        """Subscribes to WebSocket messages."""
        pass

    @abstractmethod
    async def listen_for_data(self, websocket: Any) -> Optional[Any]:
        """Listens for data on the WebSocket connection."""
        pass

    async def collect_metric(self) -> None:
        """Continuously collects metrics from the WebSocket connection."""
        while True:
            try:
                websocket = await self.connect()
                await self.subscribe(websocket)

                while True:
                    if data := await self.listen_for_data(websocket):
                        value = self.process_data(data)
                        await self.update_metric_value(value)

            except Exception as e:
                await self.handle_error(e)


class HttpMetric(BaseMetric):
    """
    HTTP-based metric for collecting data via HTTP requests.
    """

    @abstractmethod
    async def fetch_data(self) -> Optional[Any]:
        """Fetches data from the HTTP endpoint."""
        pass

    async def collect_metric(self) -> None:
        """Collects metrics by making an HTTP request."""
        while True:
            try:
                if data := await self.fetch_data():
                    value = self.process_data(data)
                    await self.update_metric_value(value)

            except Exception as e:
                await self.handle_error(e)

            await asyncio.sleep(self.config.interval)