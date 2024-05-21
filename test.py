import pandas as pd

from pyrobot.robot import Robot
from pyrobot.indicators import Indicators
from pyrobot.strategies import Strategies

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

# instruments_ids = trading_robot.get_instruments_ids_by_list(symbol_list=symbol_list)
# instruments_ids = trading_robot.get_instruments_ids_by_type(instrument_type='currencies')

# historical_candles = trading_robot.grab_historical_candles(instrument_ids=instruments_ids, period='4H')
historical_candles = trading_robot.grab_historical_candles(instrument_ids=[18], period='4H')

stock_frame = trading_robot.create_stock_frame(data=historical_candles)

# indicator_client = Indicators(price_data_frame=stock_frame)

# strategies = Strategies(price_data_frame=stock_frame, indicator_client=indicator_client)
# strategies.xiang_strategy_indicators()

# indicator_client.refresh()

# trading_robot.print_latest_stock_frame()

print(stock_frame.frame)

# last_rows: pd.Series = stock_frame.frame['signal'].where(lambda x: x == 'buy').dropna()

# print(stock_frame.frame)

# stock_frame.frame.drop(stock_frame.frame.head(1).index, inplace=True)

# print(stock_frame.frame)

# stock_frame.frame['signal'] = stock_frame.frame['signal'].shift(1)
# last_rows: pd.Series = stock_frame.frame['signal'].where(lambda x: x == 'buy').dropna()

# print(stock_frame.frame)

# trading_robot = Robot(trade = False)

# instruments_id = trading_robot.get_instruments_ids_by_list(symbol_list=currency_pairs)
# print(instruments_id)

# etoro = EtoroPrototype(
#   email = 'tankaixian0327@gmail.com', 
#   password = 'X!@Nk21', 
#   mode = 'virtual',
#   multiple_trade = True,
#   allocate_amount = 1000,
#   trading_size = 20,
#   risk_ratio = '2:12'
# )

# etoro.open_position(
#   symbol='eurusd',
#   buy_or_sell='buy',
#   atr=0.000299
# )

# etoro.close_positions(symbols=['1 - eurusd'])

# etoro.print_statistics()

# total_allocated_amount = etoro.get_total_allocated_amount()
# print(total_allocated_amount)

# etoro.print_statistics()

# etoro.get_today_earns()

# etoro.open_position(
#   mode='virtual',
#   market_type='',
#   symbol='usdzar',
#   buy_or_sell='buy',
# )

# etoro.open_position(
#   mode='virtual',
#   market_type='',
#   symbol='usdron',
#   buy_or_sell='buy',
# )

# etoro.open_position(
#   mode='virtual',
#   market_type='',
#   symbol='eurusd',
#   buy_or_sell='buy',
# )

# etoro.close_browser()