import time
import logging

import asyncio
from web3 import Web3

from common.metric_types import HttpMetric
from common.metric_config import MetricConfig, MetricLabels, MetricLabelKey




logging.basicConfig(level=logging.INFO)

class EthCallLatencyMetric(HttpMetric):
    """
    Collects the transaction latency for endpoints using eth_call to simulate a transaction.
    This metric tracks the time taken for a simulated transaction (eth_call) to be processed by the RPC node.
    """

    def __init__(self, metric_name: str, labels: MetricLabels, config: MetricConfig, **kwargs):
        http_endpoint = kwargs.get("http_endpoint")

        super().__init__(
            metric_name=metric_name,
            labels=labels,
            config=config,
            http_endpoint=http_endpoint
        )

        self.tx_data = kwargs.get('extra_params', {}).get('tx_data')

        self.to_address = Web3.to_checksum_address(self.tx_data['to'])
        self.data = self.tx_data['data']
        self.from_address = self.tx_data.get('from', '0x0000000000000000000000000000000000000000')

        self.labels.update_label(MetricLabelKey.API_METHOD, "eth_call")

    def get_web3_instance(self):
        """Return a Web3 instance for the HTTP endpoint."""
        web3 = Web3(Web3.HTTPProvider(self.http_endpoint, {"timeout": self.config.timeout}))
        if not web3.is_connected():
            raise ValueError(f"Failed to connect to {self.labels.get_label(MetricLabelKey.PROVIDER)} {self.labels.get_label(MetricLabelKey.BLOCKCHAIN)} node")
        
        return web3

    async def fetch_data(self):
        """Perform the eth_call request to simulate a transaction and track its processing time."""
        try:
            web3 = self.get_web3_instance()

            start_time = time.monotonic()
            response = await self.simulate_transaction(web3, self.data)
            end_time = time.monotonic()

            if response is None:
                raise ValueError("Response is empty")

            latency = end_time - start_time
            return latency

        except Exception as e:
            logging.error(f"Error collecting eth_call latency for {self.labels.get_label(MetricLabelKey.PROVIDER)} {self.labels.get_label(MetricLabelKey.BLOCKCHAIN)}: {e}")
            raise

    async def simulate_transaction(self, web3: Web3, transaction_data):
        """Simulate the transaction using eth_call and return the result."""
        try:
            call_params = {
                'from': self.from_address,
                'to': self.to_address,
                'data': transaction_data
            }

            result = await asyncio.to_thread(web3.eth.call, call_params, 'latest')
            return result
        
        except Exception as e:
            logging.error(f"Error simulating transaction with eth_call: {e}")
            raise

    def process_data(self, value):
        return value