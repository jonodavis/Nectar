import database
from logzero import logger
import pandas as pd 
import plotly.offline as py
import plotly.graph_objs as go
import numpy as np
import random

def gen_candles(asset, start, end, candle_size):
    raw_data = database.db_slice(asset, start, end)
    start_candle = int(start + ((start / 60000) % candle_size) * 60000)
    stop_candle = int(end - ((start / 60000) % candle_size) * 60000 + candle_size * 60000)

    for i in range(0, int((start / 60000) % candle_size)):
        raw_data.pop(0)

    # total_candles = int(((stop_candle - start_candle) / 60000) / candle_size - 1) OLD FORMULA
    total_candles = int(len(raw_data) / candle_size)

    candle_data = []
    for i in range(0, total_candles):
        candle_time = raw_data[0][0]
        dic = {"open": raw_data[0][1], "high": 0, "low": 9999999999, "close": raw_data[candle_size - 1][4], "volume": 0}
        for j in range(0, candle_size):
            if raw_data[0][2] > dic["high"]:
                dic["high"] = raw_data[0][2]
            if raw_data[0][3] < dic["low"]:
                dic["low"] = raw_data[0][3]
            dic["volume"] += raw_data[0][5]
            raw_data.pop(0)
        candle_data.append([candle_time,dic])
    
    candle_data_pd = []
    for i in candle_data:
        candle_data_pd.append([i[0], i[1]["open"], i[1]["high"], i[1]["low"], i[1]["close"], i[1]["volume"]])
    df = pd.DataFrame(candle_data_pd, columns=["timestamp", "open", "high", "low", "close", "volume"])

    return df

def simple(sma_long_size=20, sma_short_size=5, candle_size=5):
    t_start = 1543795200000
    t_end = 1544572800000

    t_back = 604800000 # ms in a week
    candles = gen_candles("BTCUSDT", t_start - t_back, t_end, candle_size)
    pips_profit = 0
    flag = True

    for index, row in candles.iterrows():
        if row.timestamp < t_start:
            continue

        sma_long = sma(candles[index - (sma_long_size - 1):index + 1].close)
        sma_short = sma(candles[index - (sma_short_size - 1):index + 1].close)

        if row.timestamp >= t_start and flag == True:
            if sma_long > sma_short:
                position = "short"
            else:
                position = "long"
            prev_close = row.close
            flag = False
            continue

        if sma_long > sma_short and position != "short":
            pips_profit += (row.close - prev_close)
            position = "short"
            prev_close = row.close
        elif sma_long < sma_short and position != "long":
            pips_profit += (prev_close - row.close)
            position = "long"
            prev_close = row.close

    # print(f"Pip Profit = {pips_profit} :: SMA Long = {sma_long_size}, SMA Short {sma_short_size}, Candle Size = {candle_size}")

    return [pips_profit, sma_long_size, sma_short_size, candle_size]


def sma(data):
    return np.mean(data)


if __name__ == "__main__":
    best = [0, 0, 0, 0]
    while True:
        result = simple(random.randint(10, 30), random.randint(4, 9), random.randint(1, 20))
        if result[0] > best[0]:
            # we have a better result
            best = [result[0], result[1], result[2], result[3]]
            print(f"Pip Profit = {result[0]} :: SMA Long = {result[1]}, SMA Short {result[2]}, Candle Size = {result[3]}")


    # df = gen_candles("ETHUSDT", 1546300800000, 1546308000000, 10)
    # trace = go.Candlestick(x=df.timestamp, open=df.open, high=df.high, low=df.low, close=df.close)
    # data = [trace]

    # py.plot(data)