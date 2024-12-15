import logging

from enum import Enum
from typing import Any, Dict, Optional




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