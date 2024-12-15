import json
import logging
from datetime import datetime, timezone

from common.metric_config import MetricConfig, MetricLabelKey, MetricLabels
from common.metric_types import WebSocketMetric


class WsBlockLatencyMetric(WebSocketMetric):
    """
    Collects block latency for providers with a persistent WebSocket connection.
    Inherits from WebSocketMetric to handle reconnection, retries, and infinite loop.
    """

    def __init__(
        self, metric_name: str, labels: MetricLabels, config: MetricConfig, **kwargs
    ):
        ws_endpoint = kwargs.pop("ws_endpoint", None)
        super().__init__(
            metric_name=metric_name,
            labels=labels,
            config=config,
            ws_endpoint=ws_endpoint,
        )
        self.labels.update_label(MetricLabelKey.API_METHOD, "eth_subscribe")

    async def subscribe(self, websocket):
        """
        Subscribe to the newHeads event on the WebSocket endpoint.
        """
        try:
            subscription_msg = json.dumps(
                {
                    "id": 1,
                    "jsonrpc": "2.0",
                    "method": "eth_subscribe",
                    "params": ["newHeads"],
                }
            )
            await websocket.send(subscription_msg)
            response = await websocket.recv()
            subscription_data = json.loads(response)

            if subscription_data.get("result") is None:
                raise ValueError("Subscription to newHeads failed")

        except Exception as e:
            logging.error(f"Error subscribing to newHeads: {str(e)}")
            raise

    async def unsubscribe(self, websocket):
        # EVM blockchains have no unsubscribe logic; do nothing.
        pass

    async def listen_for_data(self, websocket):
        """
        Listen for data from the WebSocket and process the block latency.
        """
        try:
            response = await websocket.recv()
            response_data = json.loads(response)

            if "params" in response_data:
                block = response_data["params"]["result"]
                block_hash = block["hash"]

                # Only process the block if it's not a duplicate
                if block_hash != self.last_block_hash:
                    self.last_block_hash = block_hash
                    return block

                else:
                    logging.debug(
                        f"Duplicate block detected: {block_hash}, skipping..."
                    )
                    return None

            return None

        except Exception as e:
            logging.error(f"Error receiving data: {str(e)}")
            raise

    def process_data(self, block):
        """
        Calculate block latency in seconds.
        """
        try:
            block_timestamp = int(block.get("timestamp", "0x0"), 16)
            block_time = datetime.fromtimestamp(block_timestamp, timezone.utc)
            current_time = datetime.now(timezone.utc)
            latency = (current_time - block_time).total_seconds()
            return latency

        except ValueError as e:
            logging.error(f"Invalid timestamp received: {str(e)}")
            raise
