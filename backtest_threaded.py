import database
from logzero import logger
import pandas as pd 
import plotly.offline as py
import plotly.graph_objs as go
import numpy as np
import random
import configparser
from collections import deque
import time 
import threading
import queue
from multiprocessing import Process, Queue, freeze_support, current_process

def gen_candles(orig_raw_data, start, end, candle_size):
    raw_data = deque(orig_raw_data[:])
    # start_candle = int(start + ((start / 60) % candle_size) * 60)
    # stop_candle = int(end - ((start / 60) % candle_size) * 60 + candle_size * 60)

    for i in range(0, int((start / 60) % candle_size)):
        raw_data.popleft()

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
            raw_data.popleft()
        candle_data.append([candle_time,dic])
    
    candle_data_pd = []
    for i in candle_data:
        candle_data_pd.append([i[0], i[1]["open"], i[1]["high"], i[1]["low"], i[1]["close"], i[1]["volume"]])
    df = pd.DataFrame(candle_data_pd, columns=["unixtimestamp", "open", "high", "low", "close", "volume"])

    return df

# Attempt to optimize generating of candles - ended up slower
def gen_candles_old(raw_data, asset, start, end, candle_size):
    s = time.time()

    candle_range = np.arange(len(raw_data)) // candle_size
    df = pd.DataFrame()

    # Candle Open Prices
    df['open'] = raw_data['open'].iloc[::candle_size]

    # Candle High Prices
    df_high = raw_data['high'].groupby(candle_range).max()
    df_high.index = df.index

    # Candle Low Prices
    df_low = raw_data['low'].groupby(candle_range).min()
    df_low.index = df.index

    # Candle Close Prices
    df_close = pd.DataFrame(raw_data['close'].iloc[candle_size - 1::candle_size])
    df_close.index = df_close.index + pd.Timedelta(minutes=(candle_size - 1) * -1) # fix timestamps

    # Candle Volume
    df_vol = raw_data['volume'].groupby(candle_range).sum()
    df_vol.index = df.index

    # Combine Candle Info
    candles = pd.concat([df, df_high, df_low, df_close, df_vol], axis=1).dropna(axis=0, how='any')
    candles['unixtimestamp'] = candles.index.values.astype(np.int64) // 10 ** 9
    candles = candles.reset_index()

    logger.debug(f"Time to create candles: {time.time() - s} seconds")

    return candles


def exponential_moving_average(df, ema_size):
    ema = df.close.ewm(span = ema_size, min_periods = ema_size - 1, adjust=False).mean()
    return ema

def moving_average(df, ma_size):
    ma = df.close.rolling(ma_size).mean()
    return ma

def macrossover(t_start, t_end, t_back, data, sma_long_size=20, sma_short_size=5, candle_size=5):
    candles = gen_candles(data, t_start - t_back, t_end, candle_size)
    pips_profit = 0
    flag = True
    n_trans = 0

    sma_long_v = exponential_moving_average(candles, sma_long_size)
    sma_short_v = exponential_moving_average(candles, sma_short_size)

    for index, row in candles.iterrows():
        if row.unixtimestamp < t_start:
            continue

        sma_long = sma_long_v[index]
        sma_short = sma_short_v[index]

        if row.unixtimestamp >= t_start and flag == True:
            if sma_long > sma_short:
                position = "short"
            else:
                position = "long"
            prev_close = row.close
            flag = False
            continue

        if sma_long > sma_short and position != "short":
            pips_profit += (row.close - prev_close) - ((prev_close + row.close) / 2) * 0.002 # CRYPTO FEES 0.1% PER TRANSACTION
            position = "short"
            prev_close = row.close
            n_trans += 1
        elif sma_long < sma_short and position != "long":
            pips_profit += (prev_close - row.close) - ((prev_close + row.close) / 2) * 0.002 # CRYPTO FEES 0.1% PER TRANSACTION
            position = "long"
            prev_close = row.close
            n_trans += 1

    # print(f"Pip Profit = {pips_profit} :: SMA Long = {sma_long_size}, SMA Short {sma_short_size}, Candle Size = {candle_size}")

    return [pips_profit - (0 * n_trans), sma_long_size, sma_short_size, candle_size, n_trans] # 0 if for forex fees normally 1.5


def worker(input, output, t_start, t_end, t_back, raw_data):
    for args in iter(input.get, 'STOP'):
        output.put(macrossover(t_start, t_end, t_back, raw_data, args[0], args[1], args[2]))


if __name__ == "__main__":
    freeze_support()
    start_time = time.time()
    config = configparser.ConfigParser()
    config.read("config.ini")
    t_start = int(config["backtest"]["StartTimestamp"])
    t_end = int(config["backtest"]["EndTimestamp"])
    t_back = 604800 # seconds in a week
    asset = "BTCUSDT"

    raw_data = database.db_slice(asset, t_start, t_end)
    # Convert data from database to pandas dataframe - USE ONLY FOR NEW GEN_CANLDES
    # labels = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    # raw_data = pd.DataFrame.from_records(raw_data, columns=labels)
    # raw_data.timestamp = pd.to_datetime(raw_data.timestamp, unit='s')
    # raw_data.index = raw_data.timestamp
    
    if config["backtest"]["Algo"] == "macrossover":
        combs = deque()
        if config["backtest"]["SampleMethod"] == "manual":
            sma_long_size = int(config['bt_crossover']['SMALong'])
            sma_short_size = int(config['bt_crossover']['SMAShort'])
            candle_size = int(config['bt_crossover']['CandleSize'])
        elif config["backtest"]["SampleMethod"] == "complete":
            for i in range(int(config['bt_macrossover']['SMALongRange'].split(",")[0]), int(config['bt_macrossover']['SMALongRange'].split(",")[1]) + 1):
                for j in range(int(config['bt_macrossover']['SMAShortRange'].split(",")[0]), int(config['bt_macrossover']['SMAShortRange'].split(",")[1]) + 1):
                    for k in range(int(config['bt_macrossover']['CandleSizeRange'].split(",")[0]), int(config['bt_macrossover']['CandleSizeRange'].split(",")[1]) + 1):
                        combs.append([i,j,k])
        total_runs = len(combs)
        logger.debug(f"Running {total_runs} simulations...")

        NUMBER_OF_PROCESSES = 4
        task_queue = Queue()
        done_queue = Queue()

        for item in combs:
            task_queue.put(item)

        processes = [Process(target=worker, args=(task_queue, done_queue, t_start, t_end, t_back, raw_data,)) for i in range(NUMBER_OF_PROCESSES)]
        for process in processes:
            process.start()

        results = []
        for i in range(total_runs):
            results.append(done_queue.get())
            if (i + 1) % 500 == 0:
                logger.debug(f"Total runs so far: {i + 1}")

        for i in range(NUMBER_OF_PROCESSES):
            task_queue.put('STOP')
        
        for process in processes:
            process.join()

        result = max(results, key=lambda x: x[0])
        print(result)

        logger.debug(f"Time taken: {time.time() - start_time} s")

        # while True:
            # if config["backtest"]["SampleMethod"] == "random":
            #     sma_long_size = random.randrange(int(config["bt_macrossover"]["SMALongRange"].split(",")[0]),
            #                                      int(config["bt_macrossover"]["SMALongRange"].split(",")[1]) + 1,
            #                                      int(config["bt_macrossover"]["SMALongRange"].split(",")[2]))
            #     sma_short_size = random.randrange(int(config["bt_macrossover"]["SMAShortRange"].split(",")[0]),
            #                                      int(config["bt_macrossover"]["SMAShortRange"].split(",")[1]) + 1,
            #                                      int(config["bt_macrossover"]["SMAShortRange"].split(",")[2]))
            #     candle_size = random.randrange(int(config["bt_macrossover"]["CandleSizeRange"].split(",")[0]),
            #                                    int(config["bt_macrossover"]["CandleSizeRange"].split(",")[1]) + 1,
            #                                    int(config["bt_macrossover"]["CandleSizeRange"].split(",")[2]))

            # if config['backtest']['SampleMethod'] == 'complete' and len(combs) == 0:
            #     break
            # if config['backtest']['SampleMethod'] == 'complete':
            #     sma_long_size = combs[0][0]
            #     sma_short_size = combs[0][1]
            #     candle_size = combs[0][2]
            #     combs.popleft()
            # t = threading.Thread(target=macrossover, args=(t_start, t_end, t_back, raw_data, sma_long_size, sma_short_size, candle_size,), daemon=True)
            # t.start()
            # if (total_runs - len(combs) + 1) % 500 == 0:
            #     logger.debug(f"Total runs so far: {total_runs - len(combs) + 1}")

            # if config["backtest"]["SampleMethod"] == "manual":
            #     best = [result[0], result[1], result[2], result[3], result[4]]
            #     print(f"Pip Profit = {round(result[0], 4)} :: SMA Long = {result[1]}, SMA Short {result[2]}, Candle Size = {result[3]}, Transactions = {result[4]}")
