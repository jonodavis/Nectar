import threading
import requests
import sys
import time
import os
from termcolor import colored

prices = { 'BTCUSDT': { 'price': 0.00, 'delta': 0.00},
           'ETHUSDT': { 'price': 0.00, 'delta': 0.00},
           'LTCUSDT': { 'price': 0.00, 'delta': 0.00},
           'XRPUSDT': { 'price': 0.00, 'delta': 0.00},
           'BNBUSDT': { 'price': 0.00, 'delta': 0.00},
           'ETHBTC': { 'price': 0.00, 'delta': 0.00}}

def update_price(sym):
    while True:
        template = "https://api.binance.com/api/v3/ticker/price"

        pricing = requests.get(template, params={'symbol': sym}).json()
        prices[sym]['delta'] = float(pricing['price']) - prices[sym]['price']
        prices[sym]['price'] = float(pricing['price'])

        time.sleep(3)

for sym, price in prices.items():
    t = threading.Thread(target=update_price, args=(sym,))
    t.start()


while True:
    os.system('cls' if os.name == 'nt' else 'clear')
    to_print = ''

    for sym, _ in prices.items():
        sym_formatted = sym.ljust(8)
        btc_price = prices[sym]['price']
        usd_price = prices['BTCUSDT']['price'] * btc_price

        if 'USDT' in sym:
            if prices[sym]['delta'] > 0:
                to_print += f'{sym_formatted} -> ' + colored(' ${:.2f}\n'.format(btc_price), 'green')
            else:
                to_print += f'{sym_formatted} -> ' + colored(' ${:.2f}\n'.format(btc_price), 'red')
        else:
            if prices[sym]['delta'] > 0:
                to_print += f'{sym_formatted} -> ' + colored(' {:.8f} BTC'.format(btc_price), 'green') + ' (${:.2f})\n'.format(usd_price)
            else:
                to_print += f'{sym_formatted} -> ' + colored(' {:.8f} BTC'.format(btc_price), 'red') + ' (${:.2f})\n'.format(usd_price)

    print(to_print)
    time.sleep(.5)