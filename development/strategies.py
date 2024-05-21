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

    # dl_trend
    self._frame['dl_trend'] = np.where(self._frame['ema_10'] > self._frame['ema_20'], 1, -1)

    # Clean up before sending back.
    self._frame.drop(
      labels=[],
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
  def backtest_strategy(self, multiple_trade: bool = False, atr: bool = False) -> None:

    print('Backtesting ...')

    # Move the signal to the next row
    self._frame['signal'] = self._frame['signal'].shift(1)

    # Remove the first row due to no signal
    self._frame.drop(self._frame.head(1).index, inplace=True)

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

    # For each earn pct
    for i in range(1, 10): # from 1.001 to 1.009

      # For each loss pct
      for j in range(1, 10):
        
        # Set profit and loss percentage
        if atr:
          earn_ratio = 1 + ((i - 1))
          loss_ratio = 1 + ((j - 1))
        else:
          earn_ratio = 1 + (i / 1000)
          loss_ratio = 1 + (j / 1000)

        # Create result dict
        result = {}
        result['open'] = 0
        result['miss'] = 0
        result['win'] = 0
        result['loss'] = 0
        result['open/close'] = 0
        result['win/loss'] = 0
        result['remain'] = 0

        # For each symbol
        for symbol, group in self._stock_frame.symbol_groups: # symbol = '18 - gold'

          positions = []

          # For each row / candle in dataframe
          for index, candle in group.iterrows(): # index = '18 - gold', '2021-06-24t06:30:00z' ==> type tuple
           
            # Check signal
            if candle['signal'] != '-':

              open_trade = False

              # Check able to open multiple positions
              if multiple_trade:
                open_trade = True
              else:

                # Check has opened position anot
                if len(positions) == 0:
                  open_trade = True
                else:
                  result['miss'] += 1

              # If able to open position
              if open_trade:

                # Create position
                position = {}
                position['fromdate'] = index[1]

                # Set take profit and stop loss
                if atr:
                  if candle['signal'] == 'buy':
                    position['tp'] = candle['open'] + (candle['atr'] * earn_ratio)
                    position['sl'] = candle['open'] - (candle['atr'] * loss_ratio)
                  else:
                    position['tp'] = candle['open'] - (candle['atr'] * earn_ratio)
                    position['sl'] = candle['open'] + (candle['atr'] * loss_ratio)

                else:
                  if candle['signal'] == 'buy':
                    position['tp'] = candle['open'] * earn_ratio
                    position['sl'] = candle['open'] / loss_ratio
                  else:
                    position['tp'] = candle['open'] / earn_ratio
                    position['sl'] = candle['open'] * loss_ratio

                # Add position to positions
                positions.append(position)
                result['open'] += 1
            
            ## Check positions met tp and ls

            # Check position is empty
            if positions:
              
              # For each position opened
              for position in positions:

                # Check does the position met the tp and sl
                current_time = index[1]
                current_high = candle['high']
                current_low  = candle['low']

                # Conditions
                win = False
                loss = False

                # Win
                if current_low < position['tp'] < current_high:
                  result['win'] += 1
                  win = True

                # Loss
                if current_low < position['sl'] < current_high:
                  result['loss'] += 1
                  loss = True

                # Win or loss met
                if win | loss:

                  # Check does the position open and close in the same candle
                  if position['fromdate'] == current_time:
                    result['open/close'] += 1

                  # Remove (close) the position in positions
                  positions.remove(position)

                # Both win and loss met
                if win & loss:
                  result['win/loss'] += 1

          # The remain positions havent close yet
          result['remain'] += int(len(positions))

        # Add each symbol results togather
        results = results.append({
          'earn_ratio':   earn_ratio,
          'loss_ratio':   loss_ratio,
          
          'open':         result['open'],
          'miss':         result['miss'],
          'win':          result['win'],
          'loss':         result['loss'],
          'open/close':   result['open/close'],
          'win/loss':     result['win/loss'],
          'remain':       result['remain'],

          'win_rate_1':   str(round(result['win'] / result['open'] * 100, 2)) + '%',
          'profit_1':     (result['win'] * i) - (result['loss'] * j),

          'win_rate_2':   str(round(result['win'] / (result['win'] + result['loss'] + result['remain']) * 100, 2)) + '%',
          'profit_2':     (result['win'] * i) - ((result['loss'] + result['remain']) * j),    
        }, ignore_index = True)

    # Print results
    results = results.set_index(keys=['earn_ratio', 'loss_ratio'])
    print("=" * 100)
    print('Backtest Result')
    print("=" * 100)
    print(f'Strategy:       {self._strategy_name}')
    print(f'Multiple trade: {multiple_trade}')
    print(f'Atr used:       {atr}')
    print("-" * 100)
    print(results)
    print("-" * 100)
    
    return results
  def new_backtest_strategy(self, trading_budget: int = 50, leverage: int = 1, multiple_trade: bool = False, risk_ratio: str = '1:1', print_result: bool = True) -> pd.DataFrame:

    print(f'Backtesting ==> {self._strategy_name} ...')

    # Define earn and loss ratio
    earn_ratio = float(risk_ratio.split(':')[0])
    loss_ratio = float(risk_ratio.split(':')[1])

    # Create results in dataframe
    results = pd.DataFrame(columns=[
      'symbol',           # each symbols
      'open',             # total number of positions opened
      'miss',             # total number of positions didnt opened due to not able multiple positions
      'multi',            # total number of position opening when there is other positions opened
      'highest',          # highest record of opened positions number
      'win',              # total number of opened positions that earn money
      'loss',             # total number of opened positions that lost money
      'open/close',       # total number of positions that open and close in the same candle
      'win/loss',         # total number of positions that win and loss in the same candle
      'remain',           # total number of opened positions do not have results
      'win_rate',         # win rate of the total win and loss
      'earn',             # total money earn
      'lost',             # total money lost
      'profit/loss',      # total money earned (trade with same trading budget)
      'equity',           # final money
    ])

    # For each symbol
    for symbol, group in self._stock_frame.symbol_groups: # symbol = '18 - gold'

      # Move all signals to the next row
      group['signal']      = group['signal'].shift(1)
      group['stop_loss']   = group['stop_loss'].shift(1)   if 'stop_loss' in group else 0
      group['take_profit'] = group['take_profit'].shift(1) if 'take_profit' in group else 0
      group['stop_signal'] = group['stop_signal'].shift(1) if 'stop_signal' in group else '-'
      group['atr']         = group['atr'].shift(1)         if 'atr' in group else 0

      # Remove the first row due to no signal
      group.drop(group.head(14).index, inplace=True)

      # Create result dict of this symbol
      result = {}
      result['open'] = 1
      result['miss'] = 0
      result['multi'] = 0
      result['highest'] = 0
      result['win'] = 0
      result['loss'] = 0
      result['profit/loss'] = 0
      result['open/close'] = 0
      result['earn'] = 0
      result['lost'] = 0
      result['win/loss'] = 0
      result['remain'] = 0

      # Create positions slot
      positions = []
      ongoing_trading_budget = trading_budget

      # For each row / candle in dataframe
      for index, candle in group.iterrows(): # index = '18 - gold', '2021-06-24t06:30:00z' ==> type tuple
        
        # Skip this candle is no signal and opened positions
        if candle['signal'] == '-' and not positions:
          continue

        open_trade = False

        # Check signal
        if candle['signal'] != '-':

          open_trade = True

          # Check able multiple trade and have opened position
          if not multiple_trade and len(positions) > 0:

            open_trade = False
            result['miss'] += 1
        
        # If positions not empty
        if positions:

          current_time = index[1]
          current_high = candle['high']
          current_low  = candle['low']

          # Get the highest record of opened positions number
          if len(positions) > result['highest']:
            result['highest'] = len(positions)

          # For each position opened
          for position in positions:

            # Check conditions
            win = False
            loss = False
            profit_loss = 0

            # Win
            if current_low < position['tp'] < current_high:
              result['profit/loss']  += abs((position['open'] - position['tp']) * position['units_1'])
              ongoing_trading_budget += abs((position['open'] - position['tp']) * position['units_2'])
              result['win'] += 1
              result['earn'] += abs((position['open'] - position['tp']) * position['units_1'])
              profit_loss = abs((position['open'] - position['tp']) * position['units_1'])
              win = True

            # Loss
            if current_low < position['sl'] < current_high:
              result['profit/loss']  -= abs((position['open'] - position['sl']) * position['units_1'])
              ongoing_trading_budget -= abs((position['open'] - position['sl']) * position['units_2'])
              result['loss'] += 1
              result['lost'] -= abs((position['open'] - position['sl']) * position['units_1'])
              profit_loss = -abs((position['open'] - position['sl']) * position['units_1'])
              loss = True

            # Both win and loss met
            if win & loss:
              result['win/loss'] += 1

            # Win or loss met
            if win | loss:

              print(f"{position['datetime']} ==> {current_time} ({position['action']}) {profit_loss}")

              # Check does the position open and close in the same candle
              if position['datetime'] == current_time:
                result['open/close'] += 1

              # Remove (close) the position in positions
              positions.remove(position)
        
        # Check stop signal
        if candle['stop_signal'] != '-' and positions:

          current_time = index[1]
          current_open = candle['open']
          current_high = candle['high']
          current_low  = candle['low']

          # For each position opened
          for position in positions:

            closed = False
            profit_loss = 0

            if position['action'] == 'buy' and (candle['stop_signal'] == 'buy_stop' or candle['stop_signal'] == 'stop'):

              profit_loss = (current_open - position['open']) * position['units_1']
              ongoing_trading_budget += (current_open - position['open']) * position['units_2']
              result['profit/loss'] += profit_loss
              closed = True

            if position['action'] == 'sell' and (candle['stop_signal'] == 'sell_stop' or candle['stop_signal'] == 'stop'):

              profit_loss = (position['open'] - current_open) * position['units_1']
              ongoing_trading_budget += (position['open'] - current_open) * position['units_2']
              result['profit/loss'] += profit_loss
              closed = True

            if profit_loss > 0:
              result['earn'] += profit_loss
            else:
              result['lost'] += profit_loss
            
            print(f"{position['datetime']} ==> {current_time} ({position['action']}) {profit_loss}")

            # Remove (close) the position in positions
            if closed:

              # Check does the position open and close in the same candle
              if position['datetime'] == current_time:
                result['open/close'] += 1
              
              # Check profit loss
              if profit_loss > 0:
                result['win'] += 1
              else:
                result['loss'] += 1
              positions.remove(position)
              
        # Open position
        if open_trade:

          # Create position
          position = {}
          position['datetime'] = index[1]
          position['action'] = candle['signal']
          position['open'] = candle['open']
          position['units_1'] = trading_budget * leverage / candle['open']
          position['units_2'] = ongoing_trading_budget * leverage / candle['open']
          
          # Set take profit and stop loss
          if position['action'] == 'buy':
            if candle['take_profit'] == 0 and candle['atr']:
              candle['take_profit'] = candle['open'] + (candle['atr'] * earn_ratio)
            if candle['stop_loss'] == 0 and candle['atr']:
              candle['stop_loss'] = candle['open'] - (candle['atr'] * loss_ratio)
          else:
            if candle['take_profit'] == 0 and candle['atr']:
              candle['take_profit'] = candle['open'] - (candle['atr'] * earn_ratio)
            if candle['stop_loss'] == 0 and candle['atr']:
              candle['stop_loss'] = candle['open'] + (candle['atr'] * loss_ratio)

          position['tp'] = float(candle['take_profit'])
          position['sl'] = float(candle['stop_loss'])

          # Add position to positions
          positions.append(position)
          result['open'] += 1

          # Position opened when there are other opened positions
          if len(positions) > 1:
            result['multi'] += 1
        
      # The remain positions havent close yet
      result['remain'] += int(len(positions))

      # Add each symbol results togather
      results = results.append({
        'symbol':         symbol,
        'open':           result['open'],
        'miss':           result['miss'],
        'multi':          result['multi'],
        'highest':        result['highest'],
        'win':            result['win'],
        'loss':           result['loss'],
        'open/close':     result['open/close'],
        'win/loss':       result['win/loss'],
        'remain':         result['remain'],
        'earn':           result['earn'],
        'lost':           result['lost'],
        'win_rate':       str(round(result['win'] / result['open'] * 100, 2)) + '%',
        'profit/loss':    result['profit/loss'],
        'equity':         (ongoing_trading_budget - trading_budget) / leverage
      }, ignore_index = True)

    # Print results
    if print_result:

      results = results.set_index(keys=['symbol'])
      print("=" * 100)
      print('Backtest Result')
      print("=" * 100)
      print(f'Strategy:       {self._strategy_name}')
      print(f'Period:         {self._period}')
      print(f'Trading budget: {trading_budget}')
      print(f'Leverage:       x{leverage}')
      print(f'Earn ratio:     {earn_ratio}')
      print(f'Loss ratio:     {loss_ratio}')
      print("-" * 100)
      print(results)
      print("-" * 100)
      print('Total earn: {}'.format(results['profit/loss'].sum()))
    
    return results
