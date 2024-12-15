from typing import List, Type, Tuple, Dict
from common.metric_base import BaseMetric, MetricConfig, MetricLabels




class MetricFactory:
    """
    Factory class to dynamically create metric instances based on blockchain name.
    Manages the registration and creation of metric classes.
    """
    
    _registry: dict[str, List[Type[BaseMetric]]] = {}

    @classmethod
    def register(cls, blockchain_metrics: Dict[str, List[Tuple[Type[BaseMetric], str]]]):
        """
        Registers multiple metric classes for multiple blockchains.

        Args:
            blockchain_metrics (Dict[str, List[Tuple[Type[BaseMetric], str]]]): 
                A dictionary where keys are blockchain names (str), and values are lists of tuples.
                Each tuple contains a metric class (Type[BaseMetric]) and an optional custom metric name (str).
        """
        for blockchain_name, metrics in blockchain_metrics.items():
            if blockchain_name not in cls._registry:
                cls._registry[blockchain_name] = []

            for metric in metrics:
                if isinstance(metric, tuple) and len(metric) == 2:
                    metric_class, metric_name = metric
                    metric_class.metric_name = metric_name
                    cls._registry[blockchain_name].append(metric_class)
                else:
                    raise ValueError("Each metric must be a tuple (metric_class, metric_name)")

    @classmethod
    def create_metrics(cls, blockchain_name: str, config: MetricConfig, **kwargs) -> List[BaseMetric]:
        if blockchain_name not in cls._registry:
            raise ValueError(f"No metric classes registered for blockchain '{blockchain_name}'. Available blockchains: {list(cls._registry.keys())}")

        source_region = kwargs.get("source_region", "default")
        target_region = kwargs.get("target_region", "default")
        provider = kwargs.get("provider", "default")

        metrics = []
        for metric_class in cls._registry[blockchain_name]:
            labels = MetricLabels(
                source_region=source_region,
                target_region=target_region,
                blockchain=blockchain_name, 
                provider=provider
            )

            metric_kwargs = kwargs.copy()
            
            metrics.append(metric_class(
                metric_name=metric_class.metric_name,
                labels=labels,
                config=config,
                **metric_kwargs
            ))

        return metrics

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