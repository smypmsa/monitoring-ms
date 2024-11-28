import json
import logging
import asyncio
from web3 import Web3

from app.metrics.transaction_latency import TransactionLatencyMetric




logging.basicConfig(level=logging.INFO)

with open('app/config/endpoints.json') as f:
    config = json.load(f)

with open('app/secrets/secrets.json') as f:
    secrets = json.load(f)

with open('app/config/contract_abi.json', 'r') as f:
    contract_abi = json.load(f)

web3 = Web3(Web3.HTTPProvider(config['providers'][0]['http_endpoint'],
                              {"timeout": config['timeout']}))

if not web3.is_connected():
    print("Failed to connect to Ethereum node.")
    exit()

contract = web3.eth.contract(address=Web3.to_checksum_address(config['tx_data']['contract_address']),
                             abi=contract_abi)

metric = TransactionLatencyMetric(
    blockchain_name="Ethereum",
    http_endpoint=config['providers'][0]['http_endpoint'],
    ws_endpoint=config['providers'][0]['websocket_endpoint'],
    provider=config['providers'][0]['name'],
    timeout=config['timeout'],
    interval=config['interval'],
    tx_data=config['tx_data'],
    private_key=secrets['private_key']
)

async def run_transaction_latency_metric():
    try:
        result = await metric.fetch_data()
        print(f"Transaction Latency: {result} seconds")
        
    except Exception as e:
        logging.error(f"Error during transaction latency metric execution: {e}")




asyncio.run(run_transaction_latency_metric())