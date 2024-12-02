import json
from datetime import datetime, timezone
import websockets

from common.metric_base import WebSocketMetric
from common.factory import MetricFactory

import logging




logging.basicConfig(level=logging.INFO)

class EthereumBlockLatencyMetric(WebSocketMetric):
    """
    Collects block latency for Ethereum providers with a persistent WebSocket connection.
    Inherits from WebSocketMetric to handle reconnection, retries, and infinite loop.
    """

    def __init__(self, blockchain_name, http_endpoint, ws_endpoint, provider, timeout, interval, extra_params):
        super().__init__(
            metric_name="block_latency",
            blockchain_name=blockchain_name,
            provider=provider,
            http_endpoint=http_endpoint,
            ws_endpoint=ws_endpoint,
            timeout=timeout,
            interval=interval
        )

        self.last_block_hash = None

    async def connect(self):
        """
        Establish WebSocket connection and handle subscription to the newHeads event.
        """
        try:
            websocket = await websockets.connect(
                self.ws_endpoint,
                ping_timeout=self.timeout,
                close_timeout=self.timeout
            )
            await self.subscribe(websocket)
            logging.debug(f"Connected to {self.ws_endpoint} for {self.blockchain_name}")
            return websocket
        
        except Exception as e:
            logging.error(f"Error connecting to WebSocket: {str(e)}")
            raise

    async def subscribe(self, websocket):
        """
        Subscribe to the newHeads event on the Ethereum WebSocket endpoint.
        """
        try:
            subscription_msg = json.dumps({
                "id": 1,
                "jsonrpc": "2.0",
                "method": "eth_subscribe",
                "params": ["newHeads"]
            })
            await websocket.send(subscription_msg)
            response = await websocket.recv()
            subscription_data = json.loads(response)

            if subscription_data.get("result") is None:
                raise ValueError("Subscription to newHeads failed")
            
            logging.debug("Successfully subscribed to 'newHeads' event.")

        except Exception as e:
            logging.error(f"Error subscribing to newHeads: {str(e)}")
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
            return [
                {"key": "seconds", "value": latency}
            ]
        
        except ValueError as e:
            logging.error(f"Invalid timestamp received: {str(e)}")
            raise

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
                    logging.debug(f"Duplicate block detected: {block_hash}, skipping...")
                    return None
            
            return None
        
        except Exception as e:
            logging.error(f"Error receiving or processing data: {str(e)}")
            raise


MetricFactory.register("Ethereum", EthereumBlockLatencyMetric)