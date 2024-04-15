import time
import pprint
import operator
import threading
import winsound

from configparser import ConfigParser
from threading import Thread

from pyrobot.indicators import Indicators
from pyrobot.strategies import Strategies
from pyrobot.robot import Robot

# Grab configuration values.
config = ConfigParser()
config.read("config/config.ini")

email = config.get("etoro", "email")
password = config.get("etoro", "password")

account_sid = config.get("twilio_whastapp", "account_sid")
auth_token = config.get("twilio_whastapp", "auth_token")
to_whatsapp_number = config.get("twilio_whastapp", "to_whatsapp_number")

trade = False
signal_notification = True
orders_notification = True
instrument_type = 'currencies'
period = '15M'

twilio_whatsapp = {
  "account_sid": account_sid,
  "auth_token": auth_token,
  "to_whatsapp_numbers": [to_whatsapp_number]
}

trading_robot = Robot(
  trade = trade,
  twilio_whatsapp = twilio_whatsapp,
  email = email,
  password = password,
  mode = 'virtual',
  multiple_trade = False,
  allocate_amount = 10000,
  trading_size = 1
)

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

# instruments_ids = trading_robot.get_instruments_ids_by_list(symbol_list=symbol_list)
# instruments_ids = trading_robot.get_instruments_ids_by_type(instrument_type=instrument_type)

# unwanted_instruments_ids = [8,9,13,46,48,53,54,56,59,61,62,68,83]
# additional_instruments_ids = [18]

historical_candles = trading_robot.grab_historical_candles(instrument_ids=[18], period=period)
# historical_candles = trading_robot.grab_historical_candles(instrument_ids=[1, 2], period=period)
# historical_candles = trading_robot.grab_historical_candles(instrument_ids=instruments_ids[:10], period=period)
# historical_candles = trading_robot.grab_historical_candles(instrument_ids=instruments_ids, period=period)

stock_frame = trading_robot.create_stock_frame(data=historical_candles)

indicator_client = Indicators(price_data_frame=stock_frame)

strategies = Strategies(price_data_frame=stock_frame, indicator_client=indicator_client)
strategies.fractals_alligator()

while True:

  # Grab the latest bar.
  latest_bars = trading_robot.get_latest_bar()

  # Add latest bar to the Stock Frame.
  stock_frame.add_rows(data=latest_bars)

  # Refresh the Indicators.
  indicator_client.refresh()

  # print(stock_frame.frame)

  # print latest/added stock frame
  trading_robot.print_latest_stock_frame()

  # Get signals.
  signals = strategies.get_strategy_signals()

  # Print out the signals
  # print(signals['buys'])
  # print(signals['sells'])
  # print(signals['close'])
  # print(signals['atr'])

  # Send notification to WhatsApp
  if signal_notification: 

    # Notification of got signals
    if not signals['buys'].empty or not signals['sells'].empty or not signals['close'].empty:
      winsound.PlaySound("SystemExit", winsound.SND_ALIAS)

    # Processing the signals into messages
    trading_robot.send_signals_to_whatsapp(signals=signals)

    # Send messages to WhatsApp

  # Execute Trades.
  if trade:

    # Put signal and atr value into a dict for passing into the thread
    args = {
      'signals': signals
    }

    # Run the function in a thread
    thread = Thread(
      target = trading_robot.execute_signals, 
      args = (args, )
    )
    thread.start()

  # Grab the last bar time.
  last_bar_time = stock_frame.frame.tail(n=1).index.get_level_values(1).values[0]

  # Wait till the next bar.
  trading_robot.wait_till_next_bar(last_bar_time=last_bar_time)