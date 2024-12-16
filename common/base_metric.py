import logging
import uuid
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Union

from common.metric_config import MetricConfig, MetricLabelKey, MetricLabels


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

    def __init__(
        self,
        metric_name: str,
        labels: MetricLabels,
        config: MetricConfig,
        ws_endpoint: Optional[str] = None,
        http_endpoint: Optional[str] = None,
    ) -> None:
        self.metric_id = str(
            uuid.uuid4()
        )  # Generate a unique ID for each metric instance
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
            instance.get_influx_format()
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
        return f"{self.metric_name}{{{self.labels.get_prometheus_labels()}}} {self.latest_value}"

    def get_influx_format(self) -> str:
        """Formats the metric in Influx line protocol."""
        if self.latest_value is None:
            raise ValueError("Metric value is not set")

        # Construct tags from labels
        # Example: metric_name,tag1=val1,tag2=val2 value=<latest_value>
        tag_str = ",".join(
            [f"{label.key.value}={label.value}" for label in self.labels.labels]
        )

        if tag_str:
            return f"{self.metric_name},{tag_str} value={self.latest_value}"
        else:
            return f"{self.metric_name} value={self.latest_value}"

    async def update_metric_value(self, value: Union[int, float]) -> None:
        """Updates the latest value of the metric."""
        self.latest_value = value
        self.labels.update_label(MetricLabelKey.RESPONSE_STATUS, "success")
        logging.debug(self.get_prometheus_format())

    async def handle_error(self, error: Exception) -> None:
        """Handles errors by updating the status and retrying after a delay."""
        self.labels.update_label(MetricLabelKey.RESPONSE_STATUS, "failed")
        logging.error(f"Error in {self.labels.get_prometheus_labels()}: {str(error)}")
