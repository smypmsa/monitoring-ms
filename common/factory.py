from typing import List, Type, Optional
from common.metric_base import BaseMetric, MetricConfig, MetricLabels




class MetricFactory:
    """
    Factory class to dynamically create metric instances based on blockchain name.
    Manages the registration and creation of metric classes.
    """

    _registry: dict[str, List[Type[BaseMetric]]] = {}

    @classmethod
    def register(cls, blockchain_name: str, metric_class: Type[BaseMetric], metric_name: Optional[str] = None):
        if blockchain_name not in cls._registry:
            cls._registry[blockchain_name] = []
        
        metric_name = metric_name or metric_class.__name__  # Default to the class name if not provided
        metric_class.metric_name = metric_name
        
        cls._registry[blockchain_name].append(metric_class)

    @classmethod
    def create_metrics(cls, blockchain_name: str, config: MetricConfig, **kwargs) -> List[BaseMetric]:
        if blockchain_name not in cls._registry:
            raise ValueError(f"No metric classes registered for blockchain '{blockchain_name}'. Available blockchains: {list(cls._registry.keys())}")

        source_region = kwargs.get("region", "default")
        target_region = kwargs.get("region", "default")
        provider = kwargs.get("provider", "default")
        api_method = kwargs.get("api_method", "default")

        labels = MetricLabels(
            source_region=source_region,
            target_region=target_region,
            blockchain=blockchain_name, 
            provider=provider, 
            api_method=api_method
        )

        metrics = []
        for metric_class in cls._registry[blockchain_name]:          
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