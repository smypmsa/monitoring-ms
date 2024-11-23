import json
import asyncio
import websockets
from datetime import datetime, timezone

from common.metric_base import BaseMetric
from common.factory import MetricFactory

import logging




logging.basicConfig(level=logging.ERROR)

class EthereumBlockLatencyMetric(BaseMetric):
    """
    Collects block latency for Ethereum providers with a persistent WebSocket connection.
    """

    def __init__(self, blockchain_name, websocket_endpoint, http_endpoint, provider, timeout, interval):
        super().__init__(blockchain_name, websocket_endpoint, provider, timeout, interval)
        self.http_endpoint = http_endpoint  # HTTP endpoint for potential future use
        self.should_run = True

    async def connect_and_subscribe(self, websocket):
        """
        Subscribe to the newHeads event on the Ethereum WebSocket endpoint.
        """
        await websocket.send(json.dumps({
            "id": 1,
            "jsonrpc": "2.0",
            "method": "eth_subscribe",
            "params": ["newHeads"]
        }))
        response = await websocket.recv()
        subscription_data = json.loads(response)

        if subscription_data.get("result") is None:
            raise ValueError("Subscription to newHeads failed")

    def calculate_latency(self, block_timestamp_hex):
        """
        Calculate block latency in seconds.
        """
        block_timestamp = int(block_timestamp_hex, 16)
        block_time = datetime.fromtimestamp(block_timestamp, timezone.utc)
        current_time = datetime.now(timezone.utc)
        
        return (current_time - block_time).total_seconds()

    async def collect_metric(self):
        """
        Continuously collect block latency with persistent WebSocket connection.
        """
        logging.debug("Collecting block latency")
        
        while self.should_run:
            try:
                async with websockets.connect(
                    self.endpoint,
                    ping_timeout=self.timeout,
                    close_timeout=self.timeout
                ) as websocket:
                    logging.debug("Connected to WebSocket")
                    await self.connect_and_subscribe(websocket)

                    # Listen for new blocks
                    while self.should_run:
                        response = await websocket.recv()
                        response_data = json.loads(response)

                        if "params" in response_data:
                            block = response_data["params"]["result"]
                            latency = self.calculate_latency(block["timestamp"])
                            logging.debug(f"Calculated latency: {latency}")
                            return self.format_prometheus_metric(latency)
                        
            except websockets.ConnectionClosed as e:
                logging.error(f"WebSocket connection closed: {e}")
                await asyncio.sleep(5)

            except Exception as e:
                logging.error(f"Error collecting block latency: {e}")
                return self.format_prometheus_metric(-1)

    def format_prometheus_metric(self, latency):
        """
        Format the metric as a Prometheus-compatible string with labels.
        """
        return (
            f'block_latency_seconds{{blockchain="{self.blockchain_name}", '
            f'provider="{self.provider}"}} {latency}'
        )



# Register the metric with the factory
MetricFactory.register("Ethereum", EthereumBlockLatencyMetric)