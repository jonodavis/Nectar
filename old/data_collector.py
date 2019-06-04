import json
import sched
import time
import requests

url = "https://api.bitfinex.com/v1/pubticker/ethusd"
tick_size = 10

f = open("eth_usd.json", "a")

try:
    s = sched.scheduler(time.time, time.sleep)
    
    def fetch_data(sc): 
        """
        fetches data from URL and appends to JSON file
        """
        response = requests.request("GET", url)
        print(response.text)
        f.write(response.text)
        # run function every x seconds
        s.enter(tick_size, 1, fetch_data, (sc,))
        print("hello")

    # run function immediately
    s.enter(0, 1, fetch_data, (s,))
    s.run()
except KeyboardInterrupt:
    f.close()
    print("\n==== ENDING ====")
