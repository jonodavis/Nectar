import sqlite3
from logzero import logger
import os

def db_connect(asset):
    conn = sqlite3.connect(f"data/{asset}.db")
    c = conn.cursor()
    return conn, c

def db_create(asset):
    logger.debug(f"Deleting Database data/{asset}.db if exists.")
    try:
        os.remove(f"data/{asset}.db")
        logger.debug(f"Successfully deleted Database data/{asset}.db.")
    except:
        logger.debug(f"Database data/{asset}.db doesn't exist. Nothing to delete.")

    logger.debug(f"Creating Database data/{asset}.db.")
    conn, c = db_connect(asset)
    c.execute(f'''CREATE TABLE {asset} (timestamp INTEGER, open REAL, high REAL, low REAL, close REAL, volume REAL)''')
    conn.commit()
    logger.debug(f"Database data/{asset}.db created successfully.")
    c.close()
    conn.close()

def db_write(asset, data):
    logger.debug(f"Writing data to data/{asset}.db")
    conn, c = db_connect(asset)
    c.executemany(f'''INSERT INTO {asset} VALUES (?,?,?,?,?,?)''', map(tuple, data))
    conn.commit()
    c.close()
    conn.close()
    
def db_slice(asset, start, end):
    logger.debug(f"Grabbing slice of data form {start} to {end}")
    conn, c = db_connect(asset)
    c.execute(f'''SELECT * FROM {asset} WHERE timestamp >= {start} and timestamp <= {end}''')
    data = c.fetchall()
    c.close()
    conn.close()
    return data

def db_get_last_time(asset):
    logger.debug(f"Grabbing last timestamp.")
    conn, c = db_connect(asset)
    c.execute(f'''SELECT timestamp FROM {asset} ORDER BY timestamp DESC LIMIT 1''')
    timestamp = c.fetchone()
    logger.debug(f"Last timestamp: {timestamp[0]}")
    c.close()
    conn.close()
    return timestamp[0]

if __name__=="__main__":
    pass
