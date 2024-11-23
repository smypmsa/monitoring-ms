import time
import aiohttp

from common.metric_base import BaseMetric
from common.factory import MetricFactory

import logging




logging.basicConfig(level=logging.ERROR)

class HttpCallLatencyMetric(BaseMetric):
    """
    Collects call latency for HTTP-based Ethereum endpoints.
    """

    async def collect_metric(self):
        """
        Measure call latency for HTTP endpoints.
        """
        logging.debug("Collecting HTTP call latency")
        
        while self.should_run:
            start_time = time.monotonic()

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.endpoint,
                        headers={"Accept": "application/json", "Content-Type": "application/json"},
                        json={
                            "id": 1,
                            "jsonrpc": "2.0",
                            "method": "eth_blockNumber"
                        },
                        timeout=self.timeout
                    ) as response:
                        
                        if response.status == 200:
                            await response.json()  # Ensure response body is read
                            latency = time.monotonic() - start_time
                            logging.debug(f"Calculated latency: {latency}")
                            return self.format_prometheus_metric(latency)
                        
                        else:
                            raise ValueError(f"Unexpected status code: {response.status}")
                        
            except Exception as e:
                logging.error(f"Error collecting HTTP call latency: {e}")
                return self.format_prometheus_metric(-1)

    def format_prometheus_metric(self, latency):
        """
        Format the metric as a Prometheus-compatible string with labels.
        """
        return (
            f'call_latency_seconds{{blockchain="{self.blockchain_name}", '
            f'provider="{self.provider}"}} {latency}'
        )


# Register the metric with the factory
MetricFactory.register("Ethereum", HttpCallLatencyMetric)
