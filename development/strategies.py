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
    self.sample_strategy()

    # Strategy
    self._strategy_name = 'sample_strategy'
    self._strategy_algo = self.sample_strategy_algo()

    self._indicator_client.implement_strategy(column_name=self._strategy_name, strategy=self._strategy_algo)
  def sample_strategy_algo(self) -> pd.DataFrame:

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

    # Check signals
    # ent_sig - get the first signal from the opt_dl_trend
    # ext_sig - get the first signal when trend change
    self._frame['ent_sig'] = np.where(self._frame['opt_dl_trend'] == self._frame['opt_dl_trend'].diff(), self._frame['opt_dl_trend'], 0)
    self._frame['ext_sig'] = np.where((self._frame['dl_trend'] != self._frame['dl_trend'].shift(1)) & (self._frame['dl_trend'] != 0), -self._frame['dl_trend'], 0)

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

  # TODO: Double Check
  def backtest_strategy(self, multiple_trade: bool = False) -> None:

    print('\nBacktesting strategy ==> ' + self._strategy_name)

    # Create results in dataframe type
    results = pd.DataFrame(columns=[
      'earn_ratio',   # earn ratio
      'loss_ratio',   # loss ratio
      'open',         # total number of positions opened
      'miss',         # total number of positions didnt opened due to not able multiple positions
      'win',          # total number of opened positions that earn money
      'loss',         # total number of opened positions that lost money
      'open/close',    # total number of positions that open and close in the same candle
      'win/loss',     # total number of positions that win and loss in the same candle
      'remain',       # total number of opened positions do not have results
      'win_rate_1',   # win rate of the total win and loss
      'profit_1',     # total money earned
      'win_rate_2',   # win rate of the total win and loss (remain counted as loss)
      'profit_2',     # total money earned
    ])      

    # Create result dict
    result = {}
    result['open'] = 0
    result['miss'] = 0
    result['win'] = 0
    result['loss'] = 0
    result['open/close'] = 0
    result['win/loss'] = 0
    result['remain'] = 0

    for symbol, group in self._stock_frame.symbol_groups: # symbol = '18 - gold'
      print('Backtesting ==> ' + symbol)

      # Move the entry signal to the next row
      group['ent_sig'] = group['ent_sig'].shift(1)

      # Remove the first row due to no signal
      group.drop(group.head(1).index, inplace=True)

      # For each row / candle in dataframe
      for index, frame in group.iterrows(): # index = '18 - gold', '2021-06-24t06:30:00z' ==> type tuple
        print(frame)

        if frame['ent_sig'] == 0: continue

        print(1)

        

    # # For each symbol
    # for symbol, group in self._stock_frame.symbol_groups: # symbol = '18 - gold'

    #   positions = []

    #   # For each row / candle in dataframe
    #   for index, frame in group.iterrows(): # index = '18 - gold', '2021-06-24t06:30:00z' ==> type tuple
        
    #     # Check signal
    #     if frame['ent_sig'] != 0:

    #       open_trade = False

    #       # Check able to open multiple positions
    #       if multiple_trade:
    #         open_trade = True
    #       else:

    #         # Check has opened position anot
    #         if len(positions) == 0:
    #           open_trade = True
    #         else:
    #           result['miss'] += 1

    #       # If able to open position
    #       if open_trade:

    #         # Create position
    #         position = {}
    #         position['fromdate'] = index[1]

    #         # Set take profit and stop loss
    #         position['tp'] = frame['tp']
    #         position['sl'] = frame['sl']

    #         # Add position to positions
    #         positions.append(position)
    #         result['open'] += 1
        
    #     ## Check positions met tp and ls
    #     # Check position is empty
    #     if positions:
          
    #       # For each position opened
    #       for position in positions:

    #         # Check does the position met the tp and sl
    #         current_time = index[1]
    #         current_high = frame['high']
    #         current_low  = frame['low']

    #         # Conditions
    #         win = False
    #         loss = False

    #         # Win
    #         if current_low < position['tp'] < current_high:
    #           result['win'] += 1
    #           win = True

    #         # Loss
    #         if current_low < position['sl'] < current_high:
    #           result['loss'] += 1
    #           loss = True

    #         # Win or loss met
    #         if win | loss:

    #           # Check does the position open and close in the same candle
    #           if position['fromdate'] == current_time:
    #             result['open/close'] += 1

    #           # Remove (close) the position in positions
    #           positions.remove(position)

    #         # Both win and loss met
    #         if win & loss:
    #           result['win/loss'] += 1

    #   # The remain positions havent close yet
    #   result['remain'] += int(len(positions))

    # Add each symbol results togather
    # result['open'] = 0
    # result['miss'] = 0
    # result['win'] = 0
    # result['loss'] = 0

    # # Print results
    # results = results.set_index(keys=['earn_ratio', 'loss_ratio'])
    # print("=" * 100)
    # print('Backtest Result')
    # print("=" * 100)
    # print(f'Strategy:       {self._strategy_name}')
    # print(f'Multiple trade: {multiple_trade}')
    # print("-" * 100)
    # print(results)
    # print("-" * 100)
    
    return results