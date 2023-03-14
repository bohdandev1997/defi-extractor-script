import csv
import json
import os
import requests

from web3 import Web3


api_key = os.environ.get('ALCHEMY_API_KEY')
alchemy_url = f"https://eth-mainnet.g.alchemy.com/v2/{api_key}"
w3 = Web3(Web3.HTTPProvider(alchemy_url))


# read abi from file
with open('abi.json') as f:
    ABI = json.load(f)


def get_token_to_usdc_rate(symbol):
    coins = requests.get("https://api.coingecko.com/api/v3/coins/list").json()
    coin_id = ''
    for coin in coins:
        if symbol.lower() == coin['symbol']:
            coin_id = coin['id']
            break
    if coin_id:
        coin_info = requests.get(
            f"https://api.coingecko.com/api/v3/coins/{coin_id}"
        ).json()
        coin_to_usd = coin_info["market_data"]["current_price"]["usd"]
        usdc_info = requests.get(
            f"https://api.coingecko.com/api/v3/coins/usd-coin"
        ).json()
        usdc_to_usd = usdc_info["market_data"]["current_price"]["usd"]
        return coin_to_usd / usdc_to_usd
    else:
        print("Coin not found")
        return


def get_lp_transactions(block_number, address):
    ''' Get transactions from block filtered by contract address '''
    if not w3.isConnected():
        print('Blockchain is not connected')
        return
    block = w3.eth.get_block(block_identifier=block_number)
    lp_txs = []
    for tx in block.transactions:
        tx_receipt = w3.eth.get_transaction_receipt(tx)
        if tx_receipt.to == w3.toChecksumAddress(address):
            lp_txs.append(tx)
    return lp_txs


def get_lp_providers_info(block, address):
    ''' Find balance for LP liquidity providers '''
    txs = get_lp_transactions(block_number=block, address=address)
    members = {}
    contract_instance = w3.eth.contract(
        address=w3.toChecksumAddress(address), abi=ABI
    )
    symbol = contract_instance.functions.symbol().call()
    decimals = contract_instance.functions.decimals().call()
    exchange_rate = get_token_to_usdc_rate(symbol)
    for tx in txs:
        tx_info = w3.eth.get_transaction(tx)
        provider = tx_info.get('from')
        wei_balance = contract_instance.functions.balanceOf(provider).call()
        balance = wei_balance / 10 ** decimals
        if provider in members:
            members[provider] += balance
        else:
            members[provider] = balance

    with open(f"{symbol}-{block}.csv", "w") as csv_file:
        writer = csv.writer(csv_file)
        for key, value in members.items():
            writer.writerow([key, str(value * exchange_rate)])


get_lp_providers_info(
    block=16787114, 
    address='0xd533a949740bb3306d119cc777fa900ba034cd52'
)
