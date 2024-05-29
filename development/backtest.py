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
  'GOLD', 
  # 'SILVER'
]

trading_robot = Robot()
instruments_ids = trading_robot.get_instrument_ids_by_list(symbol_list=symbol_list)
# instruments_ids = trading_robot.get_instrument_ids_by_type(instrument_type='currencies')
historical_candles = trading_robot.grab_historical_candles(period='4H', data_count=2000)
stock_frame = trading_robot.create_stock_frame()

indicator_client = Indicators(price_data_frame=stock_frame)

strategies = Strategies(price_data_frame=stock_frame, indicator_client=indicator_client)
# strategies.ema_strategy()
strategies.dl_strategy()
strategies.backtest_strategy(position_pct=10, leverage=1)

# indicator_client.refresh()

# trading_robot.print_latest_stock_frame()

# print all rows and only 6 decimal points
pd.set_option('display.max_rows', None)
pd.set_option('display.precision', 6)
# print(stock_frame.frame.replace(0, '-'))
