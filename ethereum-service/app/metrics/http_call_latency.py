import time
import aiohttp

from common.metric_base import HttpMetric
from common.factory import MetricFactory

import logging




logging.basicConfig(level=logging.INFO)

class HttpCallLatencyMetric(HttpMetric):
    """
    Collects call latency for HTTP-based Ethereum endpoints.
    Inherits from HttpMetric for common behavior and handling.
    """

    def __init__(self, blockchain_name, http_endpoint, ws_endpoint, provider, timeout, interval, extra_params):
        super().__init__(
            metric_name="eth_block_number_latency_seconds",
            blockchain_name=blockchain_name,
            provider=provider,
            http_endpoint=http_endpoint,
            ws_endpoint=ws_endpoint,
            timeout=timeout,
            interval=interval,
            extra_params=None
        )

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
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        await response.json()
                        latency = time.monotonic() - start_time
                        return latency
                    
                    else:
                        raise ValueError(f"Unexpected status code: {response.status}")
                    
        except Exception as e:
            logging.error(f"Error collecting HTTP call latency for {self.provider}: {e}")
            return None

    async def update_metric(self, value):
        """
        Update the metric with the latest collected value.
        """
        await super().update_metric(value)
        logging.info(f"Updated metric {self.metric_name} for {self.provider} with value {value}")

    def process_data(self, value):
        return value


MetricFactory.register("Ethereum", HttpCallLatencyMetric)