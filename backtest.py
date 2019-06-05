import database
from logzero import logger
import pandas as pd 
import plotly.offline as py
import plotly.graph_objs as go

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

if __name__ == "__main__":
    df = gen_candles("ETHUSDT", 1546300800000, 1546308000000, 2)
    trace = go.Candlestick(x=df.timestamp, open=df.open, high=df.high, low=df.low, close=df.close)
    data = [trace]

    py.plot(data)