from common.metric_base import MetricLabels, MetricConfig
from common.http_call_base import HttpCallLatencyMetricBase




class HttpBlockNumberLatencyMetric(HttpCallLatencyMetricBase):
    """
    Collects call latency for the `eth_blockNumber` method.
    """
    def __init__(self, metric_name: str, labels: MetricLabels, config: MetricConfig, **kwargs):
        super().__init__(
            metric_name=metric_name,
            labels=labels,
            config=config,
            method="eth_blockNumber",
            method_params=None,
            **kwargs
        )


class HttpGasPriceLatencyMetric(HttpCallLatencyMetricBase):
    """
    Collects call latency for the `eth_gasPrice` method.
    """
    def __init__(self, metric_name: str, labels: MetricLabels, config: MetricConfig, **kwargs):
        super().__init__(
            metric_name=metric_name,
            labels=labels,
            config=config,
            method="eth_gasPrice",
            method_params=None,
            **kwargs
        )