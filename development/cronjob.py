import time
import pprint
import operator
import threading
import winsound

from configparser import ConfigParser
from threading import Thread

from indicators import Indicators
from strategies import Strategies
from robot import Robot

# Grab configuration values.
config = ConfigParser()
config.read("config/config.ini")

symbol_list = [
  # 'USDCAD',	'EURJPY',
  # 'EURUSD',	'EURCHF',
  # 'USDCHF',	'EURGBP',
  # 'GBPUSD',	'AUDCAD',
  # 'NZDUSD',	'GBPCHF',
  # 'AUDUSD',	'GBPJPY',
  # 'USDJPY',	'CHFJPY',
  # 'EURCAD',	'AUDJPY',
  # 'EURAUD',	'AUDNZD',
  'GOLD',
]

trading_robot = Robot()

instruments_ids = trading_robot.get_instrument_ids_by_list(symbol_list=symbol_list)

historical_candles = trading_robot.grab_historical_candles(instrument_ids=instruments_ids, period='4H')

stock_frame = trading_robot.create_stock_frame(data=historical_candles)

indicator_client = Indicators(price_data_frame=stock_frame)

strategies = Strategies(price_data_frame=stock_frame, indicator_client=indicator_client)
# strategies.fractals_alligator()

while True:

  # Grab the latest bar.
  latest_bars = trading_robot.get_latest_candles()

  # Add latest bar to the Stock Frame.
  stock_frame.add_rows(data=latest_bars)

  # Refresh the Indicators.
  indicator_client.refresh()

  # print(stock_frame.frame)

  # print latest/added stock frame
  trading_robot.print_latest_stock_frame()

  # Get signals.
  # signals = strategies.get_strategy_signals()

  # Grab the last bar time.
  last_bar_time = stock_frame.frame.tail(n=1).index.get_level_values(1).values[0]

  # Wait till the next bar.
  trading_robot.wait_till_next_bar(last_bar_time=last_bar_time)