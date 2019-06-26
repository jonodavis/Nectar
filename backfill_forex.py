import configparser
from datetime import datetime, timedelta
import database
from logzero import logger
import numpy as np
import oandapyV20
import oandapyV20.endpoints.instruments as instruments
import re
import time

def backfill_forex(asset, startdate, reset=False):
    config = configparser.ConfigParser()
    config.read('config.ini')
    access_token = config['OANDA']['AccessToken']

    client = oandapyV20.API(access_token=access_token)

    forex_data = []

    while True:
        logger.debug(f"Backfilling {asset} data from {startdate}")
        parameters = {'granularity': 'M1', 'from': startdate.timestamp(), 'count': 5000}
        r = instruments.InstrumentsCandles(instrument=asset, params=parameters)
        data = client.request(r)

        if len(data['candles']) == 0:
            break
        
        for candle in massage_oanda(data):
            forex_data.append(candle)

        startdate = datetime.strptime(data['candles'][-1]['time'].replace("000Z", "+0000"),
                                      "%Y-%m-%dT%H:%M:%S.%f%z") + timedelta(minutes=1)
        if startdate.timestamp() > time.time():
            break
    towrite = np.array(conform_oanda_data(forex_data), dtype=np.float64)
    if reset:
        database.db_create(asset)
        database.db_write(asset, towrite)
    else:
        database.db_write(asset, towrite[1:])


def conform_oanda_data(data):
    output = [data[0]]
    logger.debug("Conforming data, filling missing candles")
    for i in range(1, len(data) - 1):
        displacement = data[i][0] - data[i - 1][0]
        if displacement != 60 and displacement < 3600:
            missing_no = (displacement - 60) / 60
            for j in range(0, int(missing_no)):
                missing_ts = data[i - 1][0] + (j + 1) * 60
                output.append([missing_ts, data[i - 1][4], data[i - 1][4], data[i - 1][4], data[i - 1][4], 0])
        output.append(data[i])
    return output


def parse_oanda_date(oandadate):
    return datetime.strptime(oandadate.replace("000Z", "+0000"), "%Y-%m-%dT%H:%M:%S.%f%z")


def massage_oanda(data):
    candles = data['candles']
    output = []
    for candle in candles:
        output.append(
            [parse_oanda_date(candle['time']).timestamp(),
             candle['mid']['o'],
             candle['mid']['h'],
             candle['mid']['l'],
             candle['mid']['c'],
             candle['volume']])
    return output


def get_start_date(asset):
    timestamp = database.db_get_last_time(asset)
    return datetime.fromtimestamp(timestamp)


def backfill(asset, reset):
    if reset == 'y':
        start_date = datetime.fromtimestamp(1262304000)
        reset = True
    else:
        start_date = get_start_date(asset)
        reset = False
    logger.debug(f"Request: Backfill {asset} date starting on {start_date}")
    backfill_forex(asset, start_date, reset)


if __name__=="__main__":
    assets = ["EUR_USD"]
    reset = 'n'
    for asset in assets:
        logger.debug(f"Backfilling {asset}...")
        backfill(asset, reset)
        logger.debug(f"Completed backfill of {asset}")