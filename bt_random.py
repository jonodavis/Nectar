import database
import random
from logzero import logger
import pandas as pd
import statistics

def sim(stoploss, takeprofit, runs, raw_data):
    # skip = random.randint(1, 60)
    profits = []

    for i in range(0, runs):
        position = 0 # 0 = none, 1 = long, 2 = short
        position_text = ''
        n_transactions = 0
        pips = 0

        for index, row in raw_data.iterrows():
            # if skip > 0:
            #     skip = skip - 1
            #     continue
            if position == 0:
                # Have no position, choose random one.
                position = random.randint(1, 2)
                if position == 1:
                    position_text == 'Long'
                else:
                    position_text == 'Short'
                position_price = row.close
                # logger.debug(f"Entered {position_text} at {position_price}")
                n_transactions += 1
                continue

            # Long, taking stoploss
            if position == 1 and (position_price - stoploss) >= row.close:
                pips = pips - stoploss
                position = 0
                skip = random.randint(1, 60)
                # logger.debug(f"{index} TAKING LONG LOSS - {pips} total pips earned. Closed at {row.close}")
                continue

            # Long, taking profit
            if position == 1 and (position_price + takeprofit) <= row.close:
                pips = pips + takeprofit
                position = 0
                skip = random.randint(1, 60)
                # logger.debug(f"{index} TAKING LONG PROFIT - {pips} total pips earned. Closed at {row.close}")
                continue

            # Short, taking stoploss
            if position == 2 and (position_price + stoploss) <= row.close:
                pips = pips - stoploss
                position = 0
                skip = random.randint(1, 60)
                # logger.debug(f"{index} TAKING SHORT LOSS - {pips} total pips earned. Closed at {row.close}")
                continue

            # Short, taking profit
            if position == 2 and (position_price - takeprofit) >= row.close:
                pips = pips + takeprofit
                position = 0
                skip = random.randint(1, 60)
                # logger.debug(f"{index} TAKING SHORT PROFIT - {pips} total pips earned. Closed at {row.close}")
                continue
        profit = pips - (n_transactions * 0.00015)
        # print(pips, n_transactions, profit)
        profits.append(profit)
    return statistics.median(profits)

if __name__=="__main__":

    t_start = 1541030400
    t_end = 1546300800

    asset = "EUR_USD"

    raw_data = database.db_slice(asset, t_start, t_end)
    # Convert data from database to pandas dataframe - USE ONLY FOR NEW GEN_CANLDES
    labels = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    raw_data = pd.DataFrame.from_records(raw_data, columns=labels)
    raw_data.timestamp = pd.to_datetime(raw_data.timestamp, unit='s')
    raw_data.index = raw_data.timestamp

    profits = []
    pip_range = [5, 51]
    n_sims = 100

    for pips in range(pip_range[0], pip_range[1]):
        logger.debug(f"Running for stoploss: {pips}")
        stoploss = pips / 10000
        takeprofit = stoploss * 2
        profits.append(sim(stoploss, takeprofit, n_sims, raw_data))
    df = pd.DataFrame({"pips": range(pip_range[0], pip_range[1]), "profits": profits})
    print(df.sort_values(by="profits", ascending=False))

    