from common.metric_config import MetricConfig, MetricLabels
from common.metric_types import HttpCallLatencyMetricBase


class HttpGetRecentBlockhashLatencyMetric(HttpCallLatencyMetricBase):
    def __init__(
        self, metric_name: str, labels: MetricLabels, config: MetricConfig, **kwargs
    ):
        super().__init__(
            metric_name=metric_name,
            labels=labels,
            config=config,
            method="getLatestBlockhash",
            **kwargs
        )


class HttpGetRecentSlotLatencyMetric(HttpCallLatencyMetricBase):
    def __init__(
        self, metric_name: str, labels: MetricLabels, config: MetricConfig, **kwargs
    ):
        super().__init__(
            metric_name=metric_name,
            labels=labels,
            config=config,
            method="getSlot",
            **kwargs
        )


class HttpSimulateTransactionLatencyMetric(HttpCallLatencyMetricBase):
    def __init__(
        self, metric_name: str, labels: MetricLabels, config: MetricConfig, **kwargs
    ):
        super().__init__(
            metric_name=metric_name,
            labels=labels,
            config=config,
            method="simulateTransaction",
            method_params=[
                "AQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAEDArczbMia1tLmq7zz4DinMNN0pJ1JtLdqIJPUw3YrGCzYAMHBsgN27lcgB6H2WQvFgyZuJYHa46puOQo9yQ8CVQbd9uHXZaGT2cvhRs7reawctIXtX1s3kTqM9YV+/wCp20C7Wj2aiuk5TReAXo+VTVg8QTHjs0UjNMMKCvpzZ+ABAgEBARU=",
                {"encoding": "base64"},
            ],
            **kwargs
        )
