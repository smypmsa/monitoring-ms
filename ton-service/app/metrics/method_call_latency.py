from common.metric_base import MetricLabels, MetricConfig
from common.http_call_base import HttpCallLatencyMetricBase




class HttpGetConsensusBlockLatency(HttpCallLatencyMetricBase):
    def __init__(self, metric_name: str, labels: MetricLabels, config: MetricConfig, **kwargs):
        super().__init__(
            metric_name=metric_name,
            labels=labels,
            config=config,
            method="getConsensusBlock",
            **kwargs
        )


class HttpGetBlockHeaderLatency(HttpCallLatencyMetricBase):
    def __init__(self, metric_name: str, labels: MetricLabels, config: MetricConfig, **kwargs):
        super().__init__(
            metric_name=metric_name,
            labels=labels,
            config=config,
            method="getBlockHeader",
            method_params={
                "workchain": -1,
                "shard": "-9223372036854775808",
                "seqno": 39064874
            },
            **kwargs
        )


class HttpRunGetMethodLatency(HttpCallLatencyMetricBase):
    def __init__(self, metric_name: str, labels: MetricLabels, config: MetricConfig, **kwargs):
        super().__init__(
            metric_name=metric_name,
            labels=labels,
            config=config,
            method="runGetMethod",
            method_params={
                "address": "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs",
                "method": "get_wallet_address",
                "stack": [
                    [
                    "tvm.Slice",
                    "te6cckEBAQEAJAAAQ4AbUzrTQYTUv8s/I9ds2TSZgRjyrgl2S2LKcZMEFcxj6PARy3rF"
                    ]
                ]
            },
            **kwargs
        )