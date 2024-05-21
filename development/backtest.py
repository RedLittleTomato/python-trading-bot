import pandas as pd

from robot import Robot
from indicators import Indicators
from strategies import Strategies

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
  'GOLD', 'SILVER'
]

trading_robot = Robot()

instruments_ids = trading_robot.get_instrument_ids_by_list(symbol_list=symbol_list)
# instruments_ids = trading_robot.get_instrument_ids_by_type(instrument_type='currencies')

historical_candles = trading_robot.grab_historical_candles(period='4H')
# historical_candles = trading_robot.grab_historical_candles(instrument_ids=[18], period='4H')

stock_frame = trading_robot.create_stock_frame(data=historical_candles)
indicator_client = Indicators(price_data_frame=stock_frame)

strategies = Strategies(price_data_frame=stock_frame, indicator_client=indicator_client)
strategies.dl_strategy()

# indicator_client.refresh()

trading_robot.print_latest_stock_frame()

# print(stock_frame.frame)

