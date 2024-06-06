import os
import sys
import json
import pytz
import time as time
import requests
import pandas as pd

from os import system

from datetime import datetime
from datetime import timezone
from datetime import timedelta

from typing import List
from typing import Dict
from typing import Union
from typing import Optional

from stock_frame import StockFrame

class Robot():

  def __init__(self) -> None:

    self.stock_frame: StockFrame = None
    self.period = None
    self.period_text = None
    self.instrument_type = None
    self.instrument_ids = []
    self.historical_candles = []
    self.instruments_metadata = self._instruments_metadata()

  def create_stock_frame(self, data: Optional[List[dict]] = None) -> StockFrame:

    # Use self.historical_candles if no data is provided.
    if data is None:
       data = self.historical_candles

    # Create the Frame.
    self.stock_frame = StockFrame(data=data, period=self.period)

    return self.stock_frame

  def print_latest_stock_frame(self):

    print("="*100)
    print("Latest StockFrame")
    print("-"*100)
    print(self.stock_frame.symbol_groups.tail(n=1))
    print("-"*100)
    print("")

  def _instruments_metadata(self) -> List[Dict]:

    url = "https://api.etorostatic.com/sapi/instrumentsmetadata/V1.1/instruments"
    res = requests.get(url)
    instruments_metadata = json.loads(res.text.lower())["instrumentdisplaydatas"]

    for instrument in instruments_metadata:
      # remove images
      instrument.pop("images")

    return instruments_metadata

  def get_instrument_ids_by_type(self, instrument_type: str) -> List[int]:

    instrument_types = {
      1: 'currencies',
      2: 'commodities',
      4: 'indices',
      5: 'stock',
      6: 'etf',
      10: 'cryptocurrencies'
    }

    # list out keys and values separately
    key_list = list(instrument_types.keys())
    val_list = list(instrument_types.values())

    # get the instrument_type_id
    index = val_list.index(instrument_type)
    instrument_type_id = key_list[index]

    instrument_ids = []

    for instrument in self.instruments_metadata:
      if instrument['instrumenttypeid'] == instrument_type_id and instrument['exchangeid'] == instrument_type_id:
        instrument_ids.append(int(instrument['instrumentid']))

    # update self instrument_ids
    self.instrument_ids = instrument_ids

    return instrument_ids

  def get_instrument_ids_by_list(self, symbol_list: List[str]) -> List[int]:

    instrument_ids = []

    # find all the instrument ids from metadata
    for instrument in self.instruments_metadata:
      if any(instrument['symbolfull'] == symbol.lower() for symbol in symbol_list):
        instrument_ids.append(int(instrument['instrumentid']))
    
    # update self instrument_ids
    self.instrument_ids = instrument_ids

    return instrument_ids
  
  def fetch_candles_from_etoro(self, instrument_id: str, data_count: int) -> dict:
    # fetch the candles data from etoro api
    url = "https://candle.etoro.com/candles/asc.json/{period}/{data_count}/{instrument_id}".format(
      period = self.period_text,
      data_count = data_count,
      instrument_id = instrument_id
    )
    print('Fetching ==> ' + url)
    res = requests.get(url)

    # get the candles data from response
    candles = json.loads(res.text.lower())["candles"][0]["candles"]

    # check got candles anot
    if candles:

      # delete the latest candle because it is live
      del candles[-1]

      # get symbol by the instrument id
      symbol = next((item for item in self.instruments_metadata if item["instrumentid"] == instrument_id), None)["symbolfull"]

      # replace the instrument ID with symbol
      # format the datetime
      for candle in candles:
        candle["instrumentid"] = str(candle["instrumentid"]) + ' - ' + symbol
        parsed_date_time = datetime.strptime(candle["fromdate"], '%Y-%m-%dT%H:%M:%SZ')
        candle["fromdate"] = parsed_date_time.strftime('%Y-%m-%d %H:%M:%S')
        del candle["volume"] 

      return candles

  def grab_historical_candles(self, instrument_ids: List[int] = None, period: str = "1D", data_count: int = 1000) -> List[dict]:

    # Use self.historical_candles if no data is provided.
    if instrument_ids is None:
       instrument_ids = self.instrument_ids

    period_list = {
      '1M': 'oneminute',
      '5M': 'fiveminutes',
      '10M': 'tenminutes',
      '15M': 'fifteenminutes',
      '30M': 'thirtyminutes',
      '1H': 'onehour',
      '4H': 'fourhours',
      '1D': 'oneday',
      '1W': 'oneweek',
    }

    if period not in period_list:
      raise Exception("Period allowed: 1M, 5M, 10M, 15M, 30M, 1H, 4H, 1D, 1W")

    self.period = period
    self.period_text = period_list.get(period)

    historical_candles = []

    print('\nFetching historical candles (' + period + ') ...')
    for instrument_id in instrument_ids:

        candles = self.fetch_candles_from_etoro(instrument_id=instrument_id, data_count=data_count)

        historical_candles.extend(candles)

    # update self historical_candles
    self.historical_candles = historical_candles
      
    return historical_candles
  
  def get_latest_candles(self):
    print('Getting latest candles ...')
    latest_candles = []

    for instrument_id in self.instrument_ids:

      url = "https://candle.etoro.com/candles/asc.json/{period}/2/{instrument_id}".format(
        period = self.period_text,
        instrument_id = instrument_id
      )
      res = requests.get(url)

      candles = json.loads(res.text.lower())["candles"][0]["candles"]

      # check got candles anot
      if candles:

        # delete the latest candle because it is live
        del candles[-1]

        # get symbol by the instrument id
        symbol = next((item for item in self.instruments_metadata if item["instrumentid"] == instrument_id), None)["symbolfull"]

        # replace the instrument ID to symbol
        for candle in candles:
          candle["instrumentid"] = str(candle["instrumentid"]) + ' - ' + symbol

        latest_candles.extend(candles)
      
    return latest_candles

  def wait_till_next_bar(self, last_bar_time: pd.DatetimeIndex) -> None:

    # # london_timezone = pytz.timezone('Europe/London')

    # # duration = [minute, hour, day, week]
    # duration = [0, 0, 0, 0]
    # interval = self.period[-1].lower()
    # period = int(self.period[:-1]) * 2

    # if interval == 'm':
    #   duration[0] = period
    # elif interval == 'h':
    #   duration[1] = period
    # elif interval == 'd':
    #   duration[2] = period
    # elif interval == 'w':
    #   duration == period
    # else:
    #   raise Exception("Wrong interval provided!")

    # last_bar_time = datetime.strptime(last_bar_time, '%Y-%m-%dt%H:%M:%Sz')
    
    # # 1 second added is for waiting the candles updated
    # if self.forex_market_open():
    #   next_bar_time = last_bar_time + timedelta(
    #     seconds=10,
    #     minutes=duration[0],
    #     hours=duration[1],
    #     days=duration[2],
    #     weeks=duration[3]
    #   )
    # else:
    #   next_bar_time = last_bar_time + timedelta(
    #     seconds=10,
    #     hours=1,
    #     days=2,
    #   )
    # curr_bar_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') # string
    # curr_bar_time = datetime.strptime(curr_bar_time, '%Y-%m-%d %H:%M:%S')       # datetime

    # last_bar_timestamp = int(last_bar_time.timestamp())
    # next_bar_timestamp = int(next_bar_time.timestamp())
    # curr_bar_timestamp = int(curr_bar_time.timestamp())

    # time_to_wait_now = next_bar_timestamp - curr_bar_timestamp

    # if time_to_wait_now < 0:
    #     time_to_wait_now = 0

    # print("=" * 50)
    # print("Paused and waiting for the next bar")
    # print("-" * 50)
    # print("Current Time: {time_curr}".format(
    #   time_curr=curr_bar_time.strftime("%Y-%m-%d %H:%M:%S")
    # ))
    # print("Next Time   : {time_next}".format(
    #   time_next=next_bar_time.strftime("%Y-%m-%d %H:%M:%S")
    # ))
    # print("Sleep Time  : {seconds} secs".format(seconds=time_to_wait_now))
    # print("-" * 50)
    # print("")

    time.sleep(10)

  def convert_data_to_csv(self):

    # Specify folder path
    folder_path = 'historical_candles'

    # Create folder if it doesn't exist
    os.makedirs(folder_path, exist_ok=True)

    # Define file path
    timestamp = int(time.time())
    file_name = f"{self.period_text}-data-{timestamp}.csv"
    file_path = os.path.join(folder_path, file_name)

    # Save DataFrame to CSV file
    self.stock_frame.frame.to_csv(file_path)
    