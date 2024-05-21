import sys
import json
import pytz
import time as time_true
import requests
import pandas as pd

from os import system

from datetime import datetime
from datetime import timezone
from datetime import timedelta

from typing import List
from typing import Dict
from typing import Union

from pyrobot.stock_frame import StockFrame

class Robot():

  def __init__(
    self, 
    mode: str = None,
  ) -> None:

    self.mode = mode
    self.instrument_ids = []
    self.period = None
    self.period_words = None
    self.stock_frame: StockFrame = None
    self.instruments_metadata = self._instruments_metadata()

  def forex_market_open(self) -> bool:

    # Open  - Sunday, 10pm
    # Close - Friday, 9pm
    
    london_timezone = pytz.timezone('Europe/London')
    london_current_datetime = datetime.now(london_timezone)
    
    # If Monday to Thrusday, return True
    if london_current_datetime.isoweekday() in range(1, 5):
      return True

    if london_current_datetime.strftime("%a") == 'Sat':
      return False

    if london_current_datetime.strftime("%a") == 'Sun':

      open_time = datetime.now(london_timezone).replace(
        hour=22,
        minute=00,
        second=00
      )

      if london_current_datetime >= open_time:
        return True
      else:
        return False

    if london_current_datetime.strftime("%a") == 'Fri':

      close_time = datetime.now(london_timezone).replace(
        hour=21,
        minute=00,
        second=00
      )

      if close_time >= london_current_datetime:
        return True
      else:
        return False
  
  @property
  def pre_market_open(self) -> bool:

    pre_market_start_time = datetime.utcnow().replace(
      hour=8,
      minute=00,
      second=00
    ).timestamp()

    market_start_time = datetime.utcnow().replace(
      hour=13,
      minute=30,
      second=00
    ).timestamp()

    right_now = datetime.utcnow().timestamp()

    if market_start_time >= right_now >= pre_market_start_time:
      return True
    else:
      return False

  @property
  def post_market_open(self):

    post_market_end_time = datetime.utcnow().replace(
      hour=00,
      minute=00,
      second=00
    ).timestamp()

    market_end_time = datetime.utcnow().replace(
      hour=20,
      minute=00,
      second=00
    ).timestamp()

    right_now = datetime.utcnow().timestamp()

    if post_market_end_time >= right_now >= market_end_time:
      return True
    else:
      return False

  @property
  def regular_market_open(self):

    market_start_time = datetime.utcnow().replace(
      hour=13,
      minute=30,
      second=00
    ).timestamp()

    market_end_time = datetime.utcnow().replace(
      hour=20,
      minute=00,
      second=00
    ).timestamp()

    right_now = datetime.utcnow().timestamp()

    if market_end_time >= right_now >= market_start_time:
      return True
    else:
      return False

  def create_stock_frame(self, data: List[dict]) -> StockFrame:

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

  def get_instruments_ids_by_type(self, instrument_type: str) -> List[int]:

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

    instruments_ids = []

    for instrument in self.instruments_metadata:
      if instrument['instrumenttypeid'] == instrument_type_id and instrument['exchangeid'] == instrument_type_id:
        instruments_ids.append(int(instrument['instrumentid']))

    return instruments_ids

  def get_instruments_ids_by_list(self, symbol_list: List[str]) -> List[int]:

    instruments_ids = []
    # symbol_list = [symbol.lower() for symbol in symbol_list]

    for instrument in self.instruments_metadata:
      if any(instrument['symbolfull'] == symbol.lower() for symbol in symbol_list):
        instruments_ids.append(int(instrument['instrumentid']))
    
    return instruments_ids

  def grab_historical_candles(self, instrument_ids: List[int], period: str) -> List[dict]:

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

    self.instrument_ids = instrument_ids
    self.period = period
    self.period_words = period_list.get(period)

    historical_candles = []

    print('Grabing historical candles...')
    for instrument_id in instrument_ids:

      # fetch the candles data from etoro api
      url = "https://candle.etoro.com/candles/asc.json/{period}/1000/{instrument_id}".format(
        period = self.period_words,
        instrument_id = instrument_id
      )
      res = requests.get(url)

      # get the candles data from response
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

        historical_candles.extend(candles)
      
    return historical_candles
  
  def get_latest_bar(self):
    print('Getting latest candles ...')
    latest_candles = []

    for instrument_id in self.instrument_ids:

      url = "https://candle.etoro.com/candles/asc.json/{period}/2/{instrument_id}".format(
        period = self.period_words,
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

    # london_timezone = pytz.timezone('Europe/London')

    # duration = [minute, hour, day, week]
    duration = [0, 0, 0, 0]
    interval = self.period[-1].lower()
    period = int(self.period[:-1]) * 2

    if interval == 'm':
      duration[0] = period
    elif interval == 'h':
      duration[1] = period
    elif interval == 'd':
      duration[2] = period
    elif interval == 'w':
      duration == period
    else:
      raise Exception("Wrong interval provided!")

    last_bar_time = datetime.strptime(last_bar_time, '%Y-%m-%dt%H:%M:%Sz')
    
    # 1 second added is for waiting the candles updated
    if self.forex_market_open():
      next_bar_time = last_bar_time + timedelta(
        seconds=10,
        minutes=duration[0],
        hours=duration[1],
        days=duration[2],
        weeks=duration[3]
      )
    else:
      next_bar_time = last_bar_time + timedelta(
        seconds=10,
        hours=1,
        days=2,
      )
    curr_bar_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') # string
    curr_bar_time = datetime.strptime(curr_bar_time, '%Y-%m-%d %H:%M:%S')       # datetime

    last_bar_timestamp = int(last_bar_time.timestamp())
    next_bar_timestamp = int(next_bar_time.timestamp())
    curr_bar_timestamp = int(curr_bar_time.timestamp())

    time_to_wait_now = next_bar_timestamp - curr_bar_timestamp

    if time_to_wait_now < 0:
        time_to_wait_now = 0

    print("=" * 50)
    print("Paused and waiting for the next bar")
    print("-" * 50)
    print("Current Time: {time_curr}".format(
      time_curr=curr_bar_time.strftime("%Y-%m-%d %H:%M:%S")
    ))
    print("Next Time   : {time_next}".format(
      time_next=next_bar_time.strftime("%Y-%m-%d %H:%M:%S")
    ))
    print("Sleep Time  : {seconds} secs".format(seconds=time_to_wait_now))
    print("-" * 50)
    print("")

    time_true.sleep(time_to_wait_now)
    