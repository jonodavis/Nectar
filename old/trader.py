import matplotlib.pyplot as plt
import time 

data = []
with open("btc_usd.csv", "r") as f:
    for line in f:
        if 'NaN' not in line:
            data.append(line.strip().split(','))
    
close = []
timestamp = []
for line in range(1, len(data)):
    if int(data[line][0]) > 1535763600 and int(data[line][0]) < 1535850000:
        close.append(float(data[line][4]))
        timestamp.append(int(data[line][0]))

sma5_close = []
sma5_timestamp = []
count = 0
total = 0
for i in range(len(close)):
    count += 1
    total += close[i]
    if count == 5:
        sma5_close.append(total/5)
        sma5_timestamp.append(timestamp[i])
        count = 0
        total = 0

sma10_close = []
sma10_timestamp = []
count = 0
total = 0
for i in range(len(close)):
    count += 1
    total += close[i]
    if count == 10:
        sma10_close.append(total/10)
        sma10_timestamp.append(timestamp[i])
        count = 0
        total = 0

money = 0
current_position = ""
close_index = 0
for t in sma10_timestamp:
    prev_position = current_position
    sma5_index = sma5_timestamp.index(t)
    sma10_index = sma10_timestamp.index(t)
    close_index = timestamp.index(t)
    if sma5_close[sma5_index] > sma10_close[sma10_index]:
        current_position = "LONG"
        print(str(close[close_index]) + " POSITION: LONG")
    else:
        current_position = "SHORT"
        print(str(close[close_index]) + " POSITION: SHORT")
    if current_position != prev_position:
        if prev_position == "" and current_position == "LONG":
            money -= close[close_index]
        elif prev_position == "" and current_position == "SHORT":
            money += close[close_index]
        elif current_position == "LONG":
            money -= close[close_index]
            money -= close[close_index]
        elif current_position =="SHORT":
            money += close[close_index]
            money += close[close_index]
if current_position == "SHORT":
    money -= close[close_index]
elif current_position == "LONG":
    money += close[close_index]

print("TOTAL PROFIT = " + str(money))

print(len(timestamp))
plt.plot(timestamp, close)
plt.plot(sma5_timestamp, sma5_close)
plt.plot(sma10_timestamp, sma10_close)
plt.axis([min(timestamp), max(timestamp), min(close), max(close)])
plt.show()

# LINE OF DATA
# 0: Timestamp
# 1: Open
# 2: High
# 3: Low
# 4: Close
# 5: Volume_(BTC)
# 6: Volume_(Currency)
# 7: Weighted_Price
