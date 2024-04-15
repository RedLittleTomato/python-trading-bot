import pandas as pd

from pyrobot.robot import Robot
from pyrobot.indicators import Indicators
from pyrobot.strategies import Strategies

# import yfinance as yf
# data = yf.download(tickers="GC=F", period="5d", interval="15m")
# print(data.tail())

symbol_list = [
  'USDCAD',	'EURJPY',
  'EURUSD',	'EURCHF',
  'USDCHF',	'EURGBP',
  'GBPUSD',	'AUDCAD',
  'NZDUSD',	'GBPCHF',
  'AUDUSD',	'GBPJPY',
  'USDJPY',	'CHFJPY',
  'EURCAD',	'AUDJPY',
  'EURAUD',	'AUDNZD',
  'GOLD',
]

trading_robot = Robot(trade=False,twilio_whatsapp=None)

instruments_ids = []

# instruments_ids = trading_robot.get_instruments_ids_by_list(symbol_list=symbol_list)
instruments_ids = trading_robot.get_instruments_ids_by_type(instrument_type='currencies')

# unwanted_instruments_ids = []
# additional_instruments_ids = [4, 7, 10, 42, 47, 55, 57, 66, 18]

# instruments_ids = [ele for ele in instruments_ids if ele not in unwanted_instruments_ids]
# instruments_ids.extend(additional_instruments_ids)

# historical_candles = trading_robot.grab_historical_candles(instrument_ids=instruments_ids, period='15M')
# historical_candles = trading_robot.grab_historical_candles(instrument_ids=[1, 2, 3, 4, 5], period='30M')
historical_candles = trading_robot.grab_historical_candles(instrument_ids=[18], period='15M')

stock_frame = trading_robot.create_stock_frame(data=historical_candles)

indicator_client = Indicators(price_data_frame=stock_frame)

strategies = Strategies(price_data_frame=stock_frame, indicator_client=indicator_client)
strategies.supertrend_psar_indicators()

# indicator_client.refresh()

# print(stock_frame.frame)

# strategies.new_backtest_strategy(
#   trading_budget=1000,
#   # leverage=20,
#   multiple_trade=True
# )

strategies.new_backtest_strategy(
  trading_budget=10000,
  # leverage=20,
  multiple_trade=False
)