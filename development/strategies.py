import numpy as np
import pandas as pd

from typing import Union

from indicators import Indicators
from stock_frame import StockFrame

class Strategies():

  def __init__(self, price_data_frame: StockFrame, indicator_client: Indicators) -> None:

    self._stock_frame: StockFrame = price_data_frame
    self._indicator_client: Indicators = indicator_client

    self._period = self._stock_frame.period
    self._frame = self._stock_frame.frame

    self._strategy_name = ''
    self._signals = {}

  def all_strategies(self) -> None:

    # Indicators
    self._indicator_client.ema(period=200, column_name='ema_200')
    self._indicator_client.rsi()
    self._indicator_client.macd()
    self._indicator_client.alligator()
    self._indicator_client.heikin_ashi()
    self._indicator_client.parabolic_sar()
    self._indicator_client.donchian_channel()
    self._indicator_client.stochastic_oscillator()
    self._indicator_client.fractal_chaos_oscillator(column_name='fco')
    self._indicator_client.stochastic_momentum_index(k_periods=5, d_periods=5)

    # Strategy
    self._strategy_name = 'all_strategies'
    self._strategy_algo = self.all_strategies_algo()

    self._indicator_client.implement_strategy(column_name=self._strategy_name, strategy=self._strategy_algo)
  def all_strategies_algo(self) -> pd.DataFrame:

    # macd
    self._frame['macd_trend'] = np.where(self._frame['macd'] > self._frame['signal_line'], 1.0, -1.0)

    # parabolic sar
    self._frame['psar_b_trend'] = np.where(self._frame['psarbull'] != '-', 1.0, 0.0)
    self._frame['psar_s_trend'] = np.where(self._frame['psarbear'] != '-', -1.0, 0.0)
    self._frame['psar_trend']   = self._frame['psar_b_trend'] + self._frame['psar_s_trend']

    # stochastic_oscillator
    self._frame['stoch_b_trend'] = np.where((self._frame['%K'] < self._frame['%D']) & (self._frame['%K'] < 30), 1.0, 0.0)
    self._frame['stoch_s_trend'] = np.where((self._frame['%K'] > self._frame['%D']) & (self._frame['%K'] > 70), -1.0, 0.0)
    self._frame['stoch_trend']   = self._frame['stoch_b_trend'] + self._frame['stoch_s_trend']

    # sma / ema
    self._frame['sma_b_trend'] = np.where(self._frame['low'] > self._frame['sma_200'], 1.0, 0.0)
    self._frame['sma_s_trend'] = np.where(self._frame['high'] < self._frame['sma_200'], -1.0, 0.0)
    self._frame['sma_trend'] = self._frame['sma_b_trend'] + self._frame['sma_s_trend']

    # stochastic_momentum_index
    self._frame['smi_trend'] = np.where(self._frame['smi'] > self._frame['smi_signal'], 1.0, -1.0)

    # alligator
    self._frame['alligator_b_trend'] = np.where((self._frame['lips'] > self._frame['teeth']) & (self._frame['teeth'] > self._frame['jaw']), 1.0, 0.0)
    self._frame['alligator_s_trend'] = np.where((self._frame['lips'] < self._frame['teeth']) & (self._frame['teeth'] < self._frame['jaw']), -1.0, 0.0)
    self._frame['alligator_trend']   = self._frame['alligator_b_trend'] + self._frame['alligator_s_trend']

    # Find the biggest and lowest line of alligator
    self._frame['biggest_alligator'] = self._frame[['lips', 'teeth', 'jaw']].max(axis=1)
    self._frame['lowest_alligator']  = self._frame[['lips', 'teeth', 'jaw']].min(axis=1)

    # Determine the candle is above or below the alligator
    self._frame['alligator_b_trend'] = np.where(self._frame['low'] > self._frame['biggest_alligator'], 1.0, 0.0)
    self._frame['alligator_s_trend'] = np.where(self._frame['high'] < self._frame['lowest_alligator'], -1.0, 0.0)
    self._frame['alligator_trend']   = self._frame['alligator_b_trend'] + self._frame['alligator_s_trend']

    # green and red candle
    self._frame['g_c'] = np.where(self._frame['open'] < self._frame['close'], 1.0, 0.0)  # green candle
    self._frame['r_c'] = np.where(self._frame['open'] > self._frame['close'], -1.0, 0.0) # red candle

    # Filter signal
    self._frame['signal'] = np.where(self._frame['macd_trend'] != self._frame['psar_trend'], 0.0, 
                            np.where(self._frame['macd_trend'] != self._frame['stoch_trend'], 0.0, self._frame['macd_trend']))

    # Get signal
    self._frame['signal'] = np.where(self._frame['signal'] == self._frame['signal'].diff(), self._frame['signal'], 0.0)

    # Set stop loss
    self._frame['b_sl'] = np.where(self._frame['signal'] == 1.0, self._frame['low'] - self._frame['atr'], 0.0)   # buy stop loss
    self._frame['s_sl'] = np.where(self._frame['signal'] == -1.0, self._frame['high'] + self._frame['atr'], 0.0) # sell stop loss
    self._frame['sl'] = self._frame['b_sl'] + self._frame['s_sl']                                                # stop loss

    # Set take profit
    self._frame['b_tp'] = np.where(self._frame['signal'] == 1.0,  (self._frame['close'] + 3 * self._frame['atr']), 0.0)  # buy take profit
    self._frame['s_tp'] = np.where(self._frame['signal'] == -1.0, (self._frame['close'] - 3 * self._frame['atr']), 0.0)  # sell take profit
    self._frame['tp'] = self._frame['b_tp'] + self._frame['s_tp']                                                        # take profit

    # Rename
    self._frame['signal'] = np.where(self._frame['signal'] == 1.0, 'buy', 
                            np.where(self._frame['signal'] == -1.0, 'sell', '-'))
    self._frame['stop_signal'] = np.where(self._frame['stop'] == 0.0, '-', 'stop')
    self._frame['stop_loss'] = np.where(self._frame['sl'] != 0.0, self._frame['sl'], '-')
    self._frame['take_profit'] = np.where(self._frame['tp'] != 0.0, self._frame['tp'], '-')

    # Clean up before sending back.
    self._frame.drop(
        labels=['macd', 'signal_line', 'psarbull', 'psarbear', 'sma_200', 
                'macd_trend', 'psar_b_trend', 'psar_s_trend', 'psar_trend', 'stoch_b_trend', 'stoch_s_trend', 'sma_b_trend', 'sma_s_trend', 'sma_trend',
                'b_sl', 's_sl', 'b_tp', 's_tp'],
        axis=1,
        inplace=True
    )

    return self._frame

  def sample_strategy(self) -> None:

    # Indicators
    self._indicator_client.ema(period=10,column_name='ema_10')

    # Strategy
    self._strategy_name = 'sample_strategy'
    self._strategy_algo = self.sample_strategy_algo()

    self._indicator_client.implement_strategy(column_name=self._strategy_name, strategy=self._strategy_algo)
  def sample_strategy_algo(self) -> pd.DataFrame:

    # signals
    self._frame['ent_sig'] = 0
    self._frame['ext_sig'] = 0

    # take profit and stop loss
    self._frame['tp'] = 0
    self._frame['sl'] = 0

    # Rename
    # self._frame['ent_sig'] = np.where(self._frame['ent_sig'] == 1.0, 'buy', 
    #                          np.where(self._frame['ent_sig'] == -1.0, 'sell', '-'))

    # Clean up before sending back.
    self._frame.drop(
      labels=[],
      axis=1,
      inplace=True
    )

    return self._frame

  def ema_strategy(self) -> None:

    # Indicators
    self._indicator_client.ema(period=10,column_name='ema_10')
    self._indicator_client.ema(period=20,column_name='ema_20')

    # Strategy
    self._strategy_name = 'ema_strategy'
    self._strategy_algo = self.ema_strategy_algo()

    self._indicator_client.implement_strategy(column_name=self._strategy_name, strategy=self._strategy_algo)
  def ema_strategy_algo(self) -> pd.DataFrame:

    # check crossover
    self._frame['trend'] = np.where(self._frame['ema_10'] > self._frame['ema_20'], -1, 1)
    self._frame['cross'] = self._frame.groupby('instrumentid')['trend'].diff()

    # signals
    self._frame['ent_sig'] = np.where((~self._frame['cross'].isna()) & (self._frame['cross'] != 0), self._frame['trend'], 0)
    self._frame['ext_sig'] = self._frame.groupby('instrumentid')['trend'].shift().where((~self._frame['cross'].isna()) & (self._frame['cross'] != 0), 0)

    # take profit and stop loss
    self._frame['tp'] = 0
    self._frame['sl'] = 0

    # Clean up before sending back.
    self._frame.drop(
      labels=[],
      axis=1,
      inplace=True
    )

    return self._frame

  def dl_strategy(self) -> None:

    # Indicators
    self._indicator_client.ema(period=10,column_name='ema_10')
    self._indicator_client.ema(period=20,column_name='ema_20')

    # Strategy
    self._strategy_name = 'dl_strategy'
    self._strategy_algo = self.dl_strategy_algo()

    self._indicator_client.implement_strategy(column_name=self._strategy_name, strategy=self._strategy_algo)
  def dl_strategy_algo(self) -> pd.DataFrame:

    # trend
    self._frame['trend'] = np.where(self._frame['ema_10'] > self._frame['ema_20'], 1, -1)

    # dl trend
    self._frame['dl_trend'] = np.where((self._frame['low'] > self._frame['ema_10'])  & (self._frame['low'] > self._frame['ema_20']) & 
                                       (self._frame['high'] > self._frame['ema_10']) & (self._frame['high'] > self._frame['ema_20']), 1,
                              np.where((self._frame['low'] < self._frame['ema_10']) & (self._frame['low'] < self._frame['ema_20']) & 
                                       (self._frame['high'] < self._frame['ema_10']) & (self._frame['high'] < self._frame['ema_20']), -1, 0))

    # calculate slope
    self._frame['slope'] = self._frame['ema_10'].diff()

    # calculate slope standard deviation 
    self._frame['slope_std'] = self._frame['slope'].rolling(window=10).std()

    # calculate standardized slope
    self._frame['standardized_slope'] = self._frame['slope'] / self._frame['slope_std']

    # calculate angle
    self._frame['angle'] = np.degrees(np.arctan(self._frame['standardized_slope']))

    # optimized dl trend
    self._frame['opt_dl_trend'] = np.where((self._frame['dl_trend'] == 1)  & (self._frame['angle'] > 45), 1, 
                                  np.where((self._frame['dl_trend'] == -1) & (self._frame['angle'] < -45), -1, 0))

    # signals
    # ent_sig - get the first signal from the opt_dl_trend
    # ext_sig - get the first signal when trend change
    self._frame['ent_sig'] = np.where(self._frame['opt_dl_trend'] == self._frame['opt_dl_trend'].diff(), self._frame['opt_dl_trend'], 0)
    self._frame['ext_sig'] = np.where((self._frame['dl_trend'] != self._frame['dl_trend'].shift(1)) & (self._frame['dl_trend'] != 0), -self._frame['dl_trend'], 0)

    # take profit and stop loss
    self._frame['tp'] = 0
    self._frame['sl'] = np.where(self._frame['ent_sig'] != 0, self._frame['ema_10'], 0)

    # # Rename
    # self._frame['signal'] = np.where(self._frame['signal'] == 1.0, 'buy', 
    #                         np.where(self._frame['signal'] == -1.0, 'sell', '-'))

    # Clean up before sending back.
    self._frame.drop(
      labels=['slope', 'slope_std', 'standardized_slope'],
      axis=1,
      inplace=True
    )

    return self._frame

  def get_strategy_signals(self) -> Union[pd.DataFrame, None]:

    # Grab the last rows.
    last_rows = self._stock_frame.symbol_groups.tail(1)

    # Define a list of conditions.
    conditions = {}

    # Filter out signals
    buys  = last_rows.where(lambda x: x['signal'] == 'buy').dropna()
    sells = last_rows.where(lambda x: x['signal'] == 'sell').dropna()
    close = last_rows.where(lambda x: x['stop_signal'] != '-').dropna()

    conditions['buys'] = buys
    conditions['sells'] = sells
    conditions['close'] = close

    return conditions

  def backtest_strategy(self, initial_amount: int = 1000, position_pct: int = 5, leverage: int = 1) -> None:

    # Validate position_pct
    if not (1 <= position_pct <= 100):
        raise ValueError("position_pct must be between 1 and 100 inclusive.")
    
    # Convert position_pct to a decimal for calculations
    position_pct = position_pct / 100

    print('\nBacktesting strategy ==> ' + self._strategy_name + ' ...\n')

    # Initialize variables
    cash_available = initial_amount
    total_invested = 0
    trades = []
    pnl_series = []
    positions = {}  # To keep track of positions by instrument
    missed_trades = []

    # Shift the signals to next row within each group
    # self._frame['ent_sig'] = self._frame.groupby('instrumentid')['ent_sig'].shift(1)
    # self._frame['ext_sig'] = self._frame.groupby('instrumentid')['ext_sig'].shift(1)
    # self._frame['tp'] = self._frame.groupby('instrumentid')['tp'].shift(1)
    # self._frame['sl'] = self._frame.groupby('instrumentid')['sl'].shift(1)

    # Initialize positions dict
    for instrumentid in self._frame.index.get_level_values('instrumentid').unique():
      positions[instrumentid] = []
   
    # Sort the DataFrame by datetime to process all instruments row by row in time order
    self._frame = self._frame.sort_values(by=['fromdate', 'instrumentid'])

    # Backtest every rows 
    for index, row in self._frame.iterrows():
      instrumentid = index[0]
      datetime = index[1]

      # Calculate the position size based on total cash and position_pct
      amount = (cash_available + total_invested) * position_pct
      position_size = amount * leverage

      # Check for entry signals
      if row['ent_sig'] == 1 and cash_available >= amount:
        # Buy long
        entry_price = row['close']
        cash_available -= amount
        total_invested += amount
        positions[instrumentid].append({
          'instrumentid': instrumentid,
          'type': 'long',
          'entry_time': datetime,
          'entry_price': entry_price,
          'amount': amount,
          'position_size': position_size,
          'tp': row['tp'],
          'sl': row['sl'],
          'portfolio': cash_available + total_invested,
        })
      elif row['ent_sig'] == -1 and cash_available >= amount:
        # Buy short
        entry_price = row['close']
        cash_available -= amount
        total_invested += amount
        positions[instrumentid].append({
          'instrumentid': instrumentid,
          'type': 'short',
          'entry_time': datetime,
          'entry_price': entry_price,
          'amount': amount,
          'position_size': position_size,
          'tp': row['tp'],
          'sl': row['sl'],
          'portfolio': cash_available + total_invested,
        })
      elif row['ent_sig'] != 0:
        # Record missed trades
        missed_trades.append({
          'instrumentid': instrumentid,
          'datetime': datetime,
          'ent_sig': row['ent_sig']
        })

      # Check for exit signals
      current_positions = positions[instrumentid]
      for position in current_positions[:]:  # Iterate over a copy to allow removal

        # Final out exit condition
        exit_signal_condition = (
          (position['type'] == 'long'  and row['ext_sig'] == 1) or
          (position['type'] == 'short' and row['ext_sig'] == -1)
        )
        exit_tp_condition = (
          (position['type'] == 'long'  and position['tp'] != 0 and row['high'] >= position['tp']) or
          (position['type'] == 'short' and position['tp'] != 0 and row['low'] <= position['tp'])
        )
        exit_sl_condition = (
          (position['type'] == 'long'  and position['sl'] != 0 and row['low'] >= position['sl']) or
          (position['type'] == 'short' and position['sl'] != 0 and row['high'] >= position['sl'])
        )
        if not (exit_signal_condition or exit_tp_condition or exit_sl_condition): continue

        # Set exit price
        if exit_signal_condition:
          exit_price = row['close']
          exit_method = 'exit signal'
        elif exit_tp_condition:
          exit_price = position['tp']
          exit_method = 'hit tp'
        elif exit_sl_condition:
          exit_price = position['sl']
          exit_method = 'hit sl'

        # Quantity = Trade Amount * Leverage / Buy Price
        # PnL = (Sell Price − Buy Price) × Quantity − Total Trading Costs
        pnl = 0
        if position['type'] == 'long':
          pnl = (exit_price - position['entry_price']) * position['position_size'] / position['entry_price']
        elif position['type'] == 'short':
          pnl = (position['entry_price'] - exit_price) * position['position_size'] / position['entry_price']
        
        cash_available += pnl + position['amount']
        total_invested -= position['amount']
        trades.append({
          'instrumentid': instrumentid,
          'type': position['type'],
          'entry_time': position['entry_time'],
          'entry_price': position['entry_price'],
          'exit_time': datetime,
          'exit_price': exit_price,
          'exit_method': exit_method,
          'amount': position['amount'],
          'pnl': pnl,
          'portfolio': cash_available + total_invested,
        })
        current_positions.remove(position)
        pnl_series.append(cash_available + total_invested - initial_amount)

    # Calculate performance metrics
    returns = pd.Series(pnl_series).pct_change().dropna()
    sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252) if not returns.empty else np.nan

    # Convert trades to DataFrame for easy analysis
    trades_df = pd.DataFrame(trades)
    missed_trades_df = pd.DataFrame(missed_trades)

    results = {
      'initial_amount': initial_amount,
      'final_amount': (cash_available + total_invested).round(2),
      'total_pnl': (cash_available + total_invested - initial_amount).round(2),
      'sharpe_ratio': sharpe_ratio,
      'trades': trades_df,
      'missed_trades': missed_trades_df
    }

    trades = pd.DataFrame(trades)
    if not trades.empty: trades = pd.DataFrame(trades).set_index(keys=['instrumentid']).sort_values(by='entry_time').round(2).replace(0, '-')
    print('=== History ===')
    print(trades)
    print('\n')

    print('=== My Portfolio ===')
    flat_positions = []
    for key, value in positions.items():
      for item in value:
        item['instrumentid'] = key  # Add instrumentid as a column
        flat_positions.append(item)

    flat_positions = pd.DataFrame(flat_positions)
    if not flat_positions.empty: flat_positions = flat_positions.set_index(keys=['instrumentid']).sort_values(by='entry_time').round(2).replace(0, '-')
    print(flat_positions)
    print('\n')

    print("=" * 100)
    print('Backtest Result')
    print("=" * 100)
    print(f'initial_amount: {results['initial_amount']}')
    print(f'final_amount:   {results['final_amount']}')
    print(f'total_pnl:      {results['total_pnl']}')
    print(f'sharpe_ratio:   {results['sharpe_ratio']}')

    return results