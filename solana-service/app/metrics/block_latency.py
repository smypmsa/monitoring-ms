import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from websockets.client import WebSocketClientProtocol

from common.metric_base import WebSocketMetric, MetricConfig, MetricLabels, MetricLabelKey




logging.basicConfig(level=logging.INFO)

class WsBlockLatencyMetric(WebSocketMetric):
    """
    Collects block latency for providers with a persistent WebSocket connection.
    Inherits from WebSocketMetric to handle reconnection, retries, and infinite loop.
    """
    def __init__(self, metric_name: str, labels: MetricLabels, config: MetricConfig, **kwargs: Dict[str, Any]):
        ws_endpoint: str = kwargs.get("ws_endpoint", "")
        super().__init__(
            metric_name=metric_name,
            labels=labels,
            config=config,
            ws_endpoint=ws_endpoint
        )
        self.labels.update_label(MetricLabelKey.API_METHOD, "blockSubscribe")

    async def subscribe(self, websocket: WebSocketClientProtocol) -> None:
        """
        Subscribe to the newHeads event on the WebSocket endpoint.
        """
        try:
            subscription_msg: str = json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "blockSubscribe",
                "params": [
                    "all",
                    {
                        "commitment": "confirmed",
                        "transactionDetails": "none",
                        "showRewards": False
                    }
                ]
            })
            await websocket.send(subscription_msg)
            response: str = await websocket.recv()
            subscription_data: Dict[str, Any] = json.loads(response)
            
            if subscription_data.get("result") is None:
                raise ValueError("Subscription to new blocks failed")
            
            self.subscription_id = subscription_data.get("result")

        except Exception as e:
            logging.error(f"Error subscribing to new blocks: {str(e)}")
            raise

    async def unsubscribe(self, websocket: Any) -> None:
        await websocket.send(json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "blockUnsubscribe",
            "params": [self.subscription_id]
        }))

        response = await websocket.recv()
        response_data = json.loads(response)

        if not response_data.get("result", False):
            logging.warning("Unsubscribe call failed or returned false")

        else:
            logging.debug("Successfully unsubscribed from block subscription")

    async def listen_for_data(self, websocket: WebSocketClientProtocol) -> Optional[Dict[str, Any]]:
        """
        Listen for data from the WebSocket and process the block latency.
        """
        try:
            response: str = await websocket.recv()
            response_data: Dict[str, Any] = json.loads(response)

            if response_data.get("method") == "blockNotification" and "params" in response_data:
                block: Dict[str, Any] = response_data["params"]["result"]["value"]["block"]
                block_hash: str = block.get("blockhash")
                
                if block_hash != self.last_block_hash:
                    self.last_block_hash = block_hash
                    return block
                
                else:
                    logging.warning(f"Duplicate block detected: {block_hash}, skipping...")
                    return None
            
            return None
        
        except Exception as e:
            logging.error(f"Error receiving data: {str(e)}")
            raise

    def process_data(self, block_info: Dict[str, Any]) -> float:
        """
        Calculate block latency in seconds.
        """
        try:
            block_time: Optional[int] = block_info.get("blockTime")

            if block_time is None:
                raise ValueError("Block time missing in block data")
            
            block_datetime: datetime = datetime.fromtimestamp(block_time, timezone.utc)
            current_time: datetime = datetime.now(timezone.utc)
            latency: float = (current_time - block_datetime).total_seconds()
            return latency
        
        except Exception as e:
            logging.error(f"Error processing block data: {e}")
            raise