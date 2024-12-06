import time
import json
from web3 import Web3
import asyncio
import logging

from common.metric_base import HttpMetric, MetricConfig, MetricLabels, MetricLabelKey





logging.basicConfig(level=logging.INFO)

class EthCallLatencyMetric(HttpMetric):
    """
    Collects the transaction latency for Ethereum-based endpoints using eth_call to simulate a transaction.
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
        self.contract_address = Web3.to_checksum_address(self.tx_data['contract_address'])

        self.labels.update_label(MetricLabelKey.API_METHOD, "eth_call")

    def load_abi(self):
        """Load ABI from the specified file path."""
        try:
            with open(self.tx_data['contract_abi'], 'r') as abi_file:
                return json.load(abi_file)
            
        except Exception as e:
            logging.error(f"Error loading ABI: {e}")
            raise

    def get_web3_instance(self):
        """Return a Web3 instance for the HTTP endpoint."""
        web3 = Web3(Web3.HTTPProvider(self.http_endpoint, {"timeout": self.config.timeout}))
        if not web3.is_connected():
            raise ValueError(f"Failed to connect to {self.labels.provider} Ethereum node")
        
        return web3

    async def encode_transaction_data(self, web3: Web3):
        """Dynamically encode the transaction data using ABI encoding."""
        contract = web3.eth.contract(address=self.contract_address, abi=self.load_abi())
        transaction_data = contract.functions[self.tx_data['function_name']](*self.tx_data['arguments']).build_transaction(
            {'from': '0x0000000000000000000000000000000000000000'})['data']  # No sender required for eth_call
        return transaction_data

    async def fetch_data(self):
        """Perform the eth_call request to simulate a transaction and track its processing time."""
        try:
            web3 = self.get_web3_instance()

            transaction_data = await self.encode_transaction_data(web3)

            start_time = time.monotonic()
            response = await self.simulate_transaction(web3, transaction_data)
            end_time = time.monotonic()

            if response is None:
                raise ValueError("Response is empty")

            latency = end_time - start_time
            return latency

        except Exception as e:
            logging.error(f"Error collecting eth_call latency for {self.labels.get_label(MetricLabelKey.PROVIDER)}: {e}")
            raise

    async def simulate_transaction(self, web3: Web3, transaction_data):
        """Simulate the transaction using eth_call and return the result."""
        try:
            result = await asyncio.to_thread(web3.eth.call, {
                'to': self.contract_address,
                'data': transaction_data
            })
            return result
        
        except Exception as e:
            logging.error(f"Error simulating transaction with eth_call: {e}")
            raise

    def process_data(self, value):
        return value