import pprint

from configparser import ConfigParser
from pyrobot.etoro_prototype import EtoroPrototype

# Grab configuration values.
config = ConfigParser()
config.read("config/config.ini")

etoro_login_email = config.get("etoro", "email")
etoro_login_password = config.get("etoro", "password")

# Setup etoro client
etoro = EtoroPrototype(
  email = etoro_login_email,
  password = etoro_login_password,
  mode = 'virtual'
)

# Switch etoro profile mode
etoro.switch_to_x_portfolio(mode='virtual')

# Open position
etoro.open_position(
  symbol='gold',
  buy_or_sell='buy',
  amount=50,
  leverage=20,
  stop_loss=None,
  take_profit=None,
)

# Print history records
etoro.print_history_records()

# Close browser
# etoro.close_browser()

# avaliable_equity = etoro.get_avaliable_equity()
# print(avaliable_equity)

# etoro.open_position(
#   mode='virtual',
#   market_type='cryptocurrencies/coins',
#   symbol='xrp',
#   buy_or_sell='buy',
#   amount=50
# )

# etoro.open_positions(
#   mode='virtual',
#   market_type='currencies',
#   symbols=['1 - eur/usd'],
#   buy_or_sell='sell',
#   amount=50,
#   leverage='X100'
# )

# etoro.open_positions(
#   mode='virtual',
#   market_type='currencies',
#   symbols=['2 - gbp/usd'],
#   buy_or_sell='sell',
#   amount=50,
#   leverage='X100'
# )

# avaliable_equity = etoro.get_avaliable_equity()
# print("Remain avaliable equity: ${}".format(avaliable_equity))

# etoro.close_positions(symbols=['3 - nzd/usd', '1 - eur/usd', '4 - usd/cad'])

# etoro.close_browser()

# from etoro import Etoro

# etoro = Etoro()
# metadata = etoro.get_metadata()

# pprint.pprint(metadata)
