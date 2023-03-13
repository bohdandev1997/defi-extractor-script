import csv
import os

from multiprocessing import Pool

from web3 import Web3


api_key = os.environ.get('ALCHEMY_API_KEY')
alchemy_url = f"https://eth-mainnet.g.alchemy.com/v2/{api_key}"
w3 = Web3(Web3.HTTPProvider(alchemy_url))

members = {}


def get_tx_info(tx):
    tx_receipt = w3.eth.get_transaction_receipt(tx)
    transaction = w3.eth.get_transaction(tx)
    tx_value = transaction.get('value')
    if tx_receipt.status == 1 and tx_value:
        tx_from = str(tx_receipt.get('from'))
        tx_to = str(tx_receipt.get('to'))
        return tx_from, tx_to, tx_value


def parse_liquidity_providers(block_number, address):
    if not w3.isConnected():
        print('Blockchain is not connected')
        return
    
    # while block_number <= w3.eth.block_number:
    end_block = 16812520
    tx_pool = []
    while block_number < end_block:
        block = w3.eth.get_block(block_number)
        block_number += 1
        for tx in block.transactions:
            tx_pool.append(tx)
        with Pool(10) as p:
            txs = p.map(get_tx_info, tx_pool)
        for tx in txs:
            if tx and tx[1] == address:
                if tx[1] in members:
                    members[tx[0]] += tx[2]
                else:
                    members[tx[0]] = tx[2]

    with open('dict.csv', 'w') as csv_file:  
        writer = csv.writer(csv_file)
        for key, value in members.items():
            writer.writerow([key, value])

parse_liquidity_providers(
    block_number=16812510, 
    address='0x6dfc34609a05bC22319fA4Cce1d1E2929548c0D7'
)
