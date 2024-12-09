import time
import aiohttp
import logging

from common.metric_base import HttpMetric, MetricLabels, MetricConfig, MetricLabelKey




logging.basicConfig(level=logging.INFO)

class HttpCallLatencyMetricBase(HttpMetric):
    """
    Base class for HTTP-based Ethereum endpoint latency metrics.
    Subclasses will specify the JSON-RPC method and its parameters.
    """

    def __init__(self, metric_name: str, labels: MetricLabels, config: MetricConfig, method: str, method_params: dict = None, **kwargs):
        """
        Initialize the base class with the necessary configuration.
        
        :param method_params: Additional parameters to pass to the JSON-RPC method.
        """
        http_endpoint = kwargs.get("http_endpoint")

        super().__init__(
            metric_name=metric_name,
            labels=labels,
            config=config,
            http_endpoint=http_endpoint
        )

        self.method = method
        self.method_params = method_params or {}
        self.labels.update_label(MetricLabelKey.API_METHOD, method)

    async def fetch_data(self):
        """
        Perform the HTTP request and return the response time for the specified method.
        """
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.monotonic()
                request_data = {
                    "id": 1,
                    "jsonrpc": "2.0",
                    "method": self.method,
                    "params": self.method_params
                }
                async with session.post(
                    self.http_endpoint,
                    headers={"Accept": "application/json", "Content-Type": "application/json"},
                    json=request_data,
                    timeout=self.config.timeout
                ) as response:
                    if response.status == 200:
                        await response.json()
                        latency = time.monotonic() - start_time
                        return latency
                    
                    else:
                        raise ValueError(f"Unexpected status code: {response.status}")
                    
        except Exception as e:
            logging.error(f"Error collecting HTTP call latency for {self.labels.get_label(MetricLabelKey.PROVIDER)}: {e}")
            raise

    def process_data(self, value):
        return value