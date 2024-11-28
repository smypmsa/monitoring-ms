import time
import json

from web3 import Web3
import asyncio

from common.metric_base import HttpMetric
from common.factory import MetricFactory

import logging




logging.basicConfig(level=logging.INFO)

class TransactionLatencyMetric(HttpMetric):
    """
    Collects the transaction latency for Ethereum-based endpoints.
    This metric tracks the time taken from submitting a transaction to it being confirmed on the blockchain.
    """

    def __init__(self, blockchain_name, http_endpoint, ws_endpoint, provider, timeout, interval, extra_params: dict):
        super().__init__(
            metric_name="transaction_latency_seconds",
            blockchain_name=blockchain_name,
            provider=provider,
            http_endpoint=http_endpoint,
            ws_endpoint=ws_endpoint,
            timeout=timeout,
            interval=interval,
            extra_params=extra_params
        )
        self.tx_data = extra_params.get('tx_data')
        self.private_key = extra_params.get('private_key')
        self.contract_address = Web3.to_checksum_address(self.tx_data['contract_address'])

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
        web3 = Web3(Web3.HTTPProvider(self.http_endpoint, {"timeout": self.timeout}))
        if not web3.is_connected():
            raise ValueError(f"Failed to connect to {self.provider} Ethereum node")
        return web3

    async def encode_transaction_data(self, web3: Web3, sender_account):
        """Dynamically encode the transaction data using ABI encoding."""
        contract = web3.eth.contract(address=self.contract_address, abi=self.load_abi())
        transaction_data = contract.functions[self.tx_data['function_name']](*self.tx_data['arguments']).build_transaction(
            {'from': sender_account.address})['data']
        return transaction_data

    async def estimate_gas(self, web3: Web3, transaction_data):
        """Estimate gas for the transaction asynchronously."""
        try:
            return await asyncio.to_thread(web3.eth.estimate_gas, {
                'to': self.contract_address,
                'data': transaction_data
            })
        except Exception as e:
            logging.error(f"Error estimating gas: {e}")
            raise

    async def get_gas_price(self, web3: Web3):
        """Fetch the current gas price asynchronously."""
        try:
            return await asyncio.to_thread(lambda: web3.eth.gas_price)  # Access as an attribute, not a callable
        except Exception as e:
            logging.error(f"Error fetching gas price: {e}")
            raise


    async def fetch_data(self):
        """Perform the HTTP request to send a transaction and track its confirmation."""
        try:
            web3 = self.get_web3_instance()
            sender_account = web3.eth.account.from_key(self.private_key)
            transaction_data = await self.encode_transaction_data(web3, sender_account)

            gas_price = await self.get_gas_price(web3)
            gas_estimate = await self.estimate_gas(web3, transaction_data)

            start_time = time.monotonic()
            transaction_hash = await self.send_transaction(web3, sender_account, transaction_data, gas_estimate, gas_price)

            confirmation_time = await self.wait_for_confirmation(web3, transaction_hash)

            if confirmation_time is None:
                return -1

            latency = confirmation_time - start_time
            return latency

        except Exception as e:
            logging.error(f"Error collecting transaction latency for {self.provider}: {e}")
            return None

    async def send_transaction(self, web3: Web3, sender_account, transaction_data, gas_estimate, gas_price):
        """Send a transaction to the Ethereum network and return the transaction hash."""
        transaction = {
            'to': self.contract_address,
            'data': transaction_data,
            'gas': gas_estimate,
            'gasPrice': gas_price,
            'nonce': web3.eth.get_transaction_count(sender_account.address),
            'chainId': 11155111  # Sepolia network ID
        }

        try:
            signed_txn = web3.eth.account.sign_transaction(transaction, self.private_key)
            transaction_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
            logging.info(f"Transaction sent: {transaction_hash.hex()}")
            return transaction_hash
        
        except Exception as e:
            logging.error(f"Error sending transaction: {e}")
            raise

    async def wait_for_confirmation(self, web3: Web3, transaction_hash):
        """Wait for the transaction to be confirmed asynchronously."""
        try:
            receipt = await asyncio.to_thread(web3.eth.wait_for_transaction_receipt, transaction_hash, timeout=self.timeout)

            if receipt['status'] == 1:
                confirmation_time = time.monotonic()
                logging.debug(f"Transaction confirmed: {transaction_hash}")
                return confirmation_time

            else:
                logging.error(f"Transaction failed: {transaction_hash}")
                return None

        except Exception as e:
            logging.error(f"Error while waiting for confirmation: {str(e)}")
            return None

    async def update_metric(self, value):
        """Update the metric with the latest collected value."""
        await super().update_metric(value)
        logging.info(f"Updated metric {self.metric_name} for {self.provider} with value {value}")

    def process_data(self, value):
        return value


MetricFactory.register("Ethereum", TransactionLatencyMetric)