import time
import aiohttp
import logging

from common.metric_base import HttpMetric, MetricLabels, MetricConfig, MetricLabelKey





logging.basicConfig(level=logging.INFO)

class HttpCallLatencyMetric(HttpMetric):
    """
    Collects call latency for HTTP-based Ethereum endpoints.
    Inherits from HttpMetric for common behavior and handling.
    """

    def __init__(self, metric_name: str, labels: MetricLabels, config: MetricConfig, **kwargs):
        http_endpoint = kwargs.get("http_endpoint")

        super().__init__(
            metric_name=metric_name,
            labels=labels,
            config=config,
            http_endpoint=http_endpoint
        )

        self.labels.update_label(MetricLabelKey.API_METHOD, "eth_blockNumber")

    async def fetch_data(self):
        """
        Perform the HTTP request and return the response time.
        """
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.monotonic()
                async with session.post(
                    self.http_endpoint,
                    headers={"Accept": "application/json", "Content-Type": "application/json"},
                    json={
                        "id": 1,
                        "jsonrpc": "2.0",
                        "method": "eth_blockNumber"
                    },
                    timeout=self.config.timeout  # Use the config timeout
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