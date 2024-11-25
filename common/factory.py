from typing import List, Type
from common.metric_base import BaseMetric




class MetricFactory:
    """
    Factory class to dynamically create metric instances based on blockchain name.
    Manages the registration and creation of metric classes.
    """

    _registry: dict[str, List[Type[BaseMetric]]] = {}

    @classmethod
    def register(cls, blockchain_name: str, metric_class: Type[BaseMetric]):
        """
        Register a metric class for a specific blockchain.
        """
        if blockchain_name not in cls._registry:
            cls._registry[blockchain_name] = []
        cls._registry[blockchain_name].append(metric_class)

    @classmethod
    def create_metrics(cls, blockchain_name: str, **kwargs) -> List[BaseMetric]:
        """
        Create instances of the registered metric classes for a given blockchain.
        """
        if blockchain_name not in cls._registry:
            raise ValueError(f"No metric classes registered for blockchain '{blockchain_name}'. Available blockchains: {list(cls._registry.keys())}")
        return [metric_class(blockchain_name=blockchain_name, **kwargs) for metric_class in cls._registry[blockchain_name]]

    @classmethod
    def get_metrics(cls, blockchain_name: str) -> List[Type[BaseMetric]]:
        """
        Return all registered metric classes for a blockchain.
        """
        return cls._registry.get(blockchain_name, [])

    @classmethod
    def get_all_metrics(cls) -> List[Type[BaseMetric]]:
        """
        Get all registered metric classes across all blockchains.
        """
        return [metric_class for metric_classes in cls._registry.values() for metric_class in metric_classes]