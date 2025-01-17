import pandas as pd

from threading import Thread
from indicators import Indicators
from strategies import Strategies
from robot import Robot

period = '1D'

trading_robot = Robot(trade = False)

symbol_list = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0].Symbol.to_list()

instruments_ids = trading_robot.get_instruments_ids(symbol_list=symbol_list)

historical_candles = trading_robot.grab_historical_candles(instrument_ids=instruments_ids[:1], period=period)

stock_frame = trading_robot.create_stock_frame(data=historical_candles)

indicator_client = Indicators(price_data_frame=stock_frame)

strategies = Strategies(price_data_frame=stock_frame, indicator_client=indicator_client)
strategies.RSI_SMA_strategy_indicators()

while True:

  # Grab the latest bar.
  latest_bars = trading_robot.get_latest_bar()

  # Add latest bar to the Stock Frame.
  stock_frame.add_rows(data=latest_bars)

  # Refresh the Indicators.
  indicator_client.refresh()

  print(stock_frame.frame)

  # print latest/added stock frame
  trading_robot.print_latest_stock_frame()

  # Get signals.
  signals = strategies.get_strategy_signals()

  # Print out the signals
  # print(signals['buys'])
  # print(signals['sells'])
  # print(signals['close'])

  # Grab the last bar time.
  last_bar_time = stock_frame.frame.tail(n=1).index.get_level_values(1).values[0]

  # Wait till the next bar.
  trading_robot.wait_till_next_bar(last_bar_time=last_bar_time)