import json
from web3 import Web3




provider_url = "..."
web3 = Web3(Web3.HTTPProvider(provider_url))

if not web3.is_connected():
    print("Failed to connect to the Ethereum node.")
    exit()

with open("contract_abi.json") as f:
    contract_abi = json.load(f)

contract_address = Web3.to_checksum_address("0x67d69beb39d25b6415ebf513e4a3812389e1d1b8")
contract = web3.eth.contract(address=contract_address, abi=contract_abi)

current_count = contract.functions.getCount().call()
print(f"Current Count: {current_count}")

private_key = "..."
account = web3.eth.account.from_key(private_key)

transaction = contract.functions.increment().build_transaction({
    'chainId': 11155111,
    'gas': 2000000,
    'gasPrice': web3.to_wei('20', 'gwei'),
    'nonce': web3.eth.get_transaction_count(account.address),
})

signed_transaction = web3.eth.account.sign_transaction(transaction, private_key)
txn_hash = web3.eth.send_raw_transaction(signed_transaction.raw_transaction)
print(f"Transaction sent. Hash: {txn_hash.hex()}")

receipt = web3.eth.wait_for_transaction_receipt(txn_hash)
print(f"Transaction confirmed: {receipt}")

current_count = contract.functions.getCount().call()
print(f"Current Count: {current_count}")