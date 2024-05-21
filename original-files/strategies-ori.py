import numpy as np
import pandas as pd

from typing import Union

from pyrobot.indicators import Indicators
from pyrobot.stock_frame import StockFrame

class Strategies():

  def __init__(self, price_data_frame: StockFrame, indicator_client: Indicators) -> None:

    self._stock_frame: StockFrame = price_data_frame
    self._indicator_client: Indicators = indicator_client

    self._period = self._stock_frame.period
    self._frame = self._stock_frame.frame

    self._strategy_name = ''
    self._signals = {}

  def empty_indicators(self) -> None:

    self._strategy_name = 'all_strategy'

    # Indicators
    self.empty_strategy()

    self._indicator_client.implement_strategy(column_name=self._strategy_name, strategy=self.empty_strategy)
  
  def empty_strategy(self) -> pd.DataFrame:

    # Clean up before sending back.
    self._frame.drop(
        labels=[],
        axis=1,
        inplace=True
    )

    return self._frame

  def all_strategy_indicators(self) -> None:

    self._strategy_name = 'all_strategy'

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
    self._indicator_client.implement_strategy(column_name=self._strategy_name, strategy=self.all_strategy)

  def all_strategy(self) -> pd.DataFrame:

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

  def supertrend_psar_indicators(self) -> None:

    self._strategy_name = 'supertrend_psar_strategy'

    self._indicator_client.supertrend()
    self._indicator_client.parabolic_sar()
    self.supertrend_psar_strategy()
    self._indicator_client.implement_strategy(column_name=self._strategy_name, strategy=self.supertrend_psar_strategy)
  
  def supertrend_psar_strategy(self) -> pd.DataFrame:

    # parabolic sar
    self._frame['psar_b_trend'] = np.where(self._frame['psarbull'] != '-', 1.0, 0.0)
    self._frame['psar_s_trend'] = np.where(self._frame['psarbear'] != '-', -1.0, 0.0)
    self._frame['psar_trend']   = self._frame['psar_b_trend'] + self._frame['psar_s_trend']

    # Filter signal
    self._frame['signal'] = np.where(self._frame['psar_trend'] == self._frame['supertrend'], self._frame['supertrend'], 0.0)

    # Set stop loss
    # self._frame['b_sl'] = np.where(self._frame['signal'] == 1.0, self._frame['close'] - (self._frame['low'] - self._frame['final_lowerband']) * 2 / 3, 0.0)  # buy stop loss
    # self._frame['s_sl'] = np.where(self._frame['signal'] == -1.0, self._frame['close'] + (self._frame['final_upperband'] - self._frame['high']) * 2 / 3, 0.0) # sell stop loss
    self._frame['b_sl'] = np.where(self._frame['signal'] == 1.0, self._frame['final_lowerband'], 0.0)  # buy stop loss
    self._frame['s_sl'] = np.where(self._frame['signal'] == -1.0, self._frame['final_upperband'], 0.0) # sell stop loss
    self._frame['sl'] = self._frame['b_sl'] + self._frame['s_sl']                                      # stop loss
    self._frame['sl'] = self._frame['sl'].round(2)

    # Set take profit
    self._frame['b_tp'] = np.where(self._frame['signal'] == 1.0,  self._frame['close'] + 1.0 * (abs(self._frame['low'] - self._frame['final_lowerband'])), 0.0)  # buy take profit
    self._frame['s_tp'] = np.where(self._frame['signal'] == -1.0, self._frame['close'] - 1.0 * (abs(self._frame['high'] - self._frame['final_upperband'])), 0.0)  # sell take profit
    self._frame['tp'] = self._frame['b_tp'] + self._frame['s_tp']                                                        # take profit
    self._frame['tp'] = self._frame['tp'].round(2)

    # Get signal
    self._frame['signal'] = np.where(self._frame['signal'] == self._frame['signal'].diff(), self._frame['signal'], 0.0)

    # Rename
    self._frame['signal'] = np.where(self._frame['signal'] == 1.0, 'buy', 
                            np.where(self._frame['signal'] == -1.0, '-', '-'))
    # self._frame['stop_signal'] = np.where(self._frame['stop'] == 0.0, '-', 'stop')
    self._frame['stop_loss'] = np.where(self._frame['sl'] != 0.0, self._frame['sl'], '-')
    self._frame['take_profit'] = np.where(self._frame['tp'] != 0.0, self._frame['tp'], '-')

    # Clean up before sending back.
    self._frame.drop(
        labels=[
          'b_sl', 's_sl', 'b_tp', 's_tp',
        ],
        axis=1,
        inplace=True
    )

    return self._frame
  def MACD_PSAR_EMA_strategy_indicators(self) -> None:

    self._strategy_name = 'MACD_PSAR_EMA_strategy'

    # Indicators
    self._indicator_client.macd()
    self._indicator_client.parabolic_sar()
    self._indicator_client.ema(period=200, column_name='ema_200')
    self._indicator_client.implement_strategy(column_name=self._strategy_name, strategy=self.MACD_PSAR_EMA_strategy)

  def MACD_PSAR_EMA_strategy(self) -> pd.DataFrame:

    # Set trends
    self._frame['psar_trend'] = np.where(self._frame['psarbull'] != '-', 1.0, -1.0)

    self._frame['macd_trend'] = np.where(self._frame['macd'] > self._frame['signal_line'], 1.0, -1.0)
    
    self._frame['ema_trend']  = np.where(self._frame['ema_200'] < self._frame['low'], 1.0, 
                               np.where(self._frame['ema_200'] > self._frame['high'], -1.0, 0.0))

    # Check signals
    self._frame['signal'] = np.where(self._frame['psar_trend'] != self._frame['macd_trend'], 0.0, 
                            np.where(self._frame['psar_trend'] != self._frame['ema_trend'], 0.0, self._frame['psar_trend']))
    self._frame['signal'] = np.where(self._frame['signal'] == self._frame['signal'].diff(), self._frame['signal'], 0.0)
    self._frame['close_signal'] = self._frame['psar_trend'].diff()

    # Rename
    self._frame['signal'] = np.where(self._frame['signal'] == 1.0, 'buy', 
                            np.where(self._frame['signal'] == -1.0, 'sell', '-'))
    # self._frame['close_signal'] = np.where(self._frame['close_signal'] != 0.0, 'close', '-')

    # self._frame['psar_trend'] = np.where(self._frame['psar_trend'] == 1.0, 'buy', 'sell')
    # self._frame['macd_trend'] = np.where(self._frame['macd_trend'] == 1.0, 'buy', 'sell')
    # self._frame['ema_trend']  = np.where(self._frame['ema_trend'] == 1.0, 'buy', 
    #                             np.where(self._frame['ema_trend'] == -1.0, 'sell', '-'))

    # Clean up before sending back.
    self._frame.drop(
        labels=['macd', 'signal_line', 'parabolic_sar', 'psarbull', 'psarbear', 'ema_200',
                'psar_trend', 'macd_trend', 'ema_trend'],
        axis=1,
        inplace=True
    )

    return self._frame

  def crossover_strategy_indicators(self) -> None:

    self._indicator_client.sma(period=2, column_name='sma_2')
    self._indicator_client.sma(period=7, column_name='sma_7')
    self._indicator_client.sma(period=200, column_name='sma_200')
    self._indicator_client.implement_strategy(column_name='crossover_strategy', strategy=self.crossover_strategy)

  def crossover_strategy(self) -> pd.DataFrame:

    # define the zone
    self._frame['zone'] = np.where(self._frame['sma_200'] < self._frame['low'], 1.0, 
                          np.where(self._frame['sma_200'] > self._frame['high'], -1.0, 0.0))
    self._frame['stop'] = self._frame['zone'].diff()

    # # define the zone gap
    # self._frame['gaps'] = abs(self._frame['close'] - self._frame['sma_200'])
    # # self._frame['gaps'] = self._frame['sma_2'].diff()
    # self._frame['diff'] = self._frame['gaps'].diff()
    # self._frame['zone'] = np.where(self._frame['diff'] < 0, self._frame['zone'], 0.0)

    # check crossover
    self._frame['compare'] = np.where(self._frame['sma_2'] > self._frame['sma_7'], 1.0, 0.0)
    self._frame['cross'] = self._frame['compare'].diff()

    # rename
    self._frame['zone'] = np.where(self._frame['zone'] == 1.0, 'buy', 
                          np.where(self._frame['zone'] == -1.0, 'sell', '-'))
    self._frame['stop'] = np.where(self._frame['stop'] == 0.0, '-', 'stop')
    self._frame['cross'] = np.where(self._frame['cross'] == 1.0, 'buy', 
                            np.where(self._frame['cross'] == -1.0, 'sell', '-'))

    # get signals
    self._frame['CROSS'] = np.where((self._frame['zone'] == 'buy') & (self._frame['cross'] == 'buy'), 'buy',
                            np.where((self._frame['zone'] == 'sell') & (self._frame['cross'] == 'sell'), 'sell', '-'))

    # Clean up before sending back.
    self._frame.drop(
        labels=['sma_2', 'sma_7', 'sma_200', 'compare'],
        # labels=['signal','gaps','diff'],
        axis=1,
        inplace=True
    )

    return self._frame

  def MACD_EMA_strategy_indicators(self) -> None:

    self._indicator_client.ema(period=200, column_name='ema_200')
    self._indicator_client.macd()
  
  def MACD_EMA_strategy(self) -> pd.DataFrame:

    # define the zone
    self._frame['zone'] = np.where(self._frame['ema_200'] < self._frame['low'], 1.0, 
                          np.where(self._frame['ema_200'] > self._frame['high'], -1.0, 0.0))
    # self._frame['stop'] = self._frame['zone'].diff()

    # check crossover
    self._frame['compare'] = np.where(self._frame['macd'] > self._frame['signal_line'], 1.0, 0.0)
    self._frame['cross'] = self._frame['compare'].diff()

    # rename
    self._frame['zone'] = np.where(self._frame['zone'] == 1.0, 'buy', 
                np.where(self._frame['zone'] == -1.0, 'sell', '-'))
    self._frame['cross'] = np.where(self._frame['cross'] == 1.0, 'buy', 
                            np.where(self._frame['cross'] == -1.0, 'sell', '-'))

    # get signals
    self._frame['MACD'] = np.where((self._frame['zone'] == 'buy') & (self._frame['cross'] == 'buy'), 'buy',
                          np.where((self._frame['zone'] == 'sell') & (self._frame['cross'] == 'sell'), 'sell', '-'))

    # Clean up before sending back.
    self._frame.drop(
        labels=['ema_200', 'macd', 'signal_line', 'compare', 'zone', 'cross'],
        axis=1,
        inplace=True
    )

  # Not Working
  def RSI_SMA_strategy_indicators(self) -> None:

    strategy_name = 'RSI_SMA_strategy'

    # Indicators
    self._indicator_client.sma(period=200, column_name='sma_200')
    self._indicator_client.rsi(period=10)
    self._indicator_client.implement_strategy(column_name=strategy_name, strategy=self.RSI_SMA_strategy)

  def RSI_SMA_strategy(self) -> pd.DataFrame:

    self._frame['buy1'] = np.where((self._frame['close'] > self._frame['sma_200']) & (self._frame['rsi'] < 30), 'Yes', 'No')
    # self._frame.loc[(self._frame['close'] > self._frame['sma_200']) & (self._frame['rsi'] < 30), 'buy2'] = 'yes'
    # self._frame.loc[(self._frame['close'] < self._frame['sma_200']) | (self._frame['rsi'] > 30), 'buy2'] = 'no'

    # Clean up before sending back.
    self._frame.drop(
        labels=['change_in_price'],
        axis=1,
        inplace=True
    )

    return self._frame

  def tri_EMA_strategy_indicators(self) -> None:

    self._strategy_name = 'tri_EMA_strategy'

    # Indicators
    self._indicator_client.ema(period=8, column_name='ema_8')
    # self._indicator_client.ema(period=9, column_name='ema_9')
    # self._indicator_client.ema(period=13, column_name='ema_13')
    self._indicator_client.ema(period=14, column_name='ema_14')
    # self._indicator_client.ema(period=21, column_name='ema_21')
    self._indicator_client.ema(period=50, column_name='ema_50')
    self._indicator_client.ema(period=100, column_name='ema_100')
    self._indicator_client.ema(period=150, column_name='ema_150')
    self._indicator_client.sma(period=200, column_name='sma_200')
    self._indicator_client.stochastic_oscillator()
    self._indicator_client.average_true_range(column_name='atr')
    self._indicator_client.implement_strategy(column_name=self._strategy_name, strategy=self.tri_EMA_strategy)

  def tri_EMA_strategy(self) -> pd.DataFrame:

    # Set signal trend
    self._frame['ema_b_trend'] = np.where((self._frame['ema_8']   > self._frame['ema_14']) &
                                          (self._frame['ema_14']  > self._frame['ema_50']) &
                                          (self._frame['ema_50']  > self._frame['ema_100']) &
                                          (self._frame['ema_100'] > self._frame['ema_150']), 1.0, 0.0)

    self._frame['ema_s_trend'] = np.where((self._frame['ema_8']   < self._frame['ema_14']) &
                                          (self._frame['ema_14']  < self._frame['ema_50']) &
                                          (self._frame['ema_50']  < self._frame['ema_100']) &
                                          (self._frame['ema_100'] < self._frame['ema_150']), -1.0, 0.0)

    self._frame['ema_trend']   = self._frame['ema_b_trend'] + self._frame['ema_s_trend']
    
    self._frame['sma_trend']   = np.where(self._frame['sma_200'] < self._frame['low'], 1.0, 
                                 np.where(self._frame['sma_200'] > self._frame['high'], -1.0, 0.0))
    self._frame['stoch_trend'] = np.where(self._frame['%K'] < self._frame['%D'], 1.0, -1.0)

    # Filter signal
    self._frame['signal'] = np.where(self._frame['ema_trend'] != self._frame['sma_trend'], 0.0, self._frame['ema_trend'])
                            # np.where(self._frame['ema_trend'] != self._frame['stoch_trend'], 0.0, self._frame['ema_trend']))

    # Get signal
    self._frame['signal'] = np.where(self._frame['signal'] == self._frame['signal'].diff(), self._frame['signal'], 0.0)

    # Rename
    self._frame['signal'] = np.where(self._frame['signal'] == 1.0, 'buy', 
                            np.where(self._frame['signal'] == -1.0, 'sell', '-'))

    # Clean up before sending back.
    self._frame.drop(
        labels=['ema_8', 'ema_14', 'ema_50', 'ema_100', 'ema_150','sma_200', '%K', '%D',
                'ema_b_trend', 'ema_s_trend', 'ema_trend', 'sma_trend', 'stoch_trend'],
        axis=1,
        inplace=True
    )

    return self._frame

  def breakouts_strategy_indicators(self) -> None:

    self._strategy_name = 'breakouts_strategy'

    # Indicators
    self._indicator_client.sma(period=55, field='high',  column_name='sma_55_h')
    self._indicator_client.sma(period=55, field='close', column_name='sma_55_c')
    self._indicator_client.sma(period=55, field='low',   column_name='sma_55_l')
    self._indicator_client.sma(period=200, column_name='sma_200')
    self.breakouts_strategy()

    self._indicator_client.implement_strategy(column_name=self._strategy_name, strategy=self.breakouts_strategy)

  def breakouts_strategy(self) -> pd.DataFrame:

    # Set trend
    self._frame['sma_b_trend'] = np.where((self._frame['low'] > self._frame['sma_55_h']) &
                                          (self._frame['low'] > self._frame['sma_200']), 1.0, 0.0)
    self._frame['sma_s_trend'] = np.where((self._frame['high'] < self._frame['sma_55_l']) &
                                          (self._frame['high'] < self._frame['sma_200']), -1.0, 0.0)
    self._frame['sma_trend'] = self._frame['sma_b_trend'] + self._frame['sma_s_trend']

    # Get signal
    self._frame['signal'] = np.where(self._frame['sma_trend'] == self._frame['sma_trend'].diff(), self._frame['sma_trend'], 0.0)

    # Set stop loss
    self._frame['b_sl'] = np.where(self._frame['signal'] == 1.0, self._frame['low'].shift(), 0.0)   # buy stop loss
    self._frame['s_sl'] = np.where(self._frame['signal'] == -1.0, self._frame['high'].shift(), 0.0) # sell stop loss
    self._frame['sl'] = self._frame['b_sl'] + self._frame['s_sl']                           # stop loss

    # Set take profit
    self._frame['b_tp'] = np.where(self._frame['signal'] == 1.0,  (self._frame['close'] + 3 * (self._frame['close'] - self._frame['low'])), 0.0)   # buy take profit
    self._frame['s_tp'] = np.where(self._frame['signal'] == -1.0, (self._frame['close'] - 3 * (self._frame['high'] - self._frame['close'])), 0.0)  # sell take profit
    self._frame['tp'] = self._frame['b_tp'] + self._frame['s_tp']                                                                                  # take profit

    # Define green and red candle
    self._frame['g_c'] = np.where(self._frame['open'] < self._frame['close'], 1.0, 0.0)  # green candle
    self._frame['r_c'] = np.where(self._frame['open'] > self._frame['close'], -1.0, 0.0) # red candle

    # Check 3 previous candles 
    self._frame['b_s'] = self._frame['r_c'].transform( # buy stop
      lambda x: x.rolling(window=3).sum()
    )
    self._frame['s_s'] = self._frame['g_c'].transform( # sell stop
      lambda x: x.rolling(window=3).sum()
    )

    # If 3 candles trend (green or red) are same, set stop signal
    self._frame['b_s'] = np.where(self._frame['b_s'] == -3.0, 1.0, 0.0)
    self._frame['s_s'] = np.where(self._frame['s_s'] == 3.0, -1.0, 0.0)

    # Get the first stop signal
    self._frame['b_s'] = np.where(self._frame['b_s'] == self._frame['b_s'].diff(), self._frame['b_s'], 0.0)
    self._frame['s_s'] = np.where(self._frame['s_s'] == self._frame['s_s'].diff(), self._frame['s_s'], 0.0)

    # Check the stop signal is inside the trend
    self._frame['b_s'] = np.where((self._frame['sma_b_trend'] == 1.0) &
                                  (self._frame['b_s'] == 1.0), 1.0, 0.0)
    self._frame['s_s'] = np.where((self._frame['sma_s_trend'] == -1.0) &
                                  (self._frame['s_s'] == -1.0), -1.0, 0.0)
    self._frame['stop_signal'] = self._frame['b_s'] + self._frame['s_s']

    # Rename
    self._frame['signal'] = np.where(self._frame['signal'] == 1.0, 'buy', 
                            np.where(self._frame['signal'] == -1.0, 'sell', '-'))
    self._frame['stop_loss'] = np.where(self._frame['sl'] != 0.0, self._frame['sl'], '-')
    self._frame['take_profit'] = np.where(self._frame['tp'] != 0.0, self._frame['tp'], '-')
    self._frame['stop_signal'] = np.where(self._frame['stop_signal'] == 1.0, 'buy_stop', 
                                 np.where(self._frame['stop_signal'] == -1.0, 'sell_stop', '-'))

    # Clean up before sending back.
    self._frame.drop(
        labels=['sma_55_h', 'sma_55_c', 'sma_55_l', 'sma_200', 
                'sma_trend', 'sma_b_trend', 'sma_s_trend', 'b_sl', 's_sl', 'g_c', 'r_c', 'b_s', 's_s'],
        axis=1,
        inplace=True
    )

    return self._frame

  def test(self) -> None:

    self._strategy_name = 'test'

    # Indicators
    self._indicator_client.rsi()
    self._indicator_client.macd()
    self._indicator_client.alligator()
    self._indicator_client.parabolic_sar()
    self._indicator_client.awesome_oscillator()
    self._indicator_client.stochastic_momentum_index(k_periods=5, d_periods=5)
    self.test_strategy()

    self._indicator_client.implement_strategy(column_name=self._strategy_name, strategy=self.test_strategy)
  
  def test_strategy(self) -> pd.DataFrame:

    # Calculate macd trends
    self._frame['macd_trend'] = np.where(self._frame['macd'] > self._frame['signal_line'], 1.0, -1.0)

    # Calculate awesome oscillator trends
    self._frame['awesome_oscillator'] = np.where(self._frame['awesome_oscillator'] > 0, 1.0, -1.0)

    # stochastic_momentum_index
    self._frame['smi_trend'] = np.where(self._frame['smi'] > self._frame['smi_signal'], 1.0, -1.0)

    # Calculate rsi trend
    self._frame['rsi_b_trend'] = np.where(self._frame['rsi'] >= 60, 1.0, 0.0)
    self._frame['rsi_s_trend'] = np.where(self._frame['rsi'] <= 40, -1.0, 0.0)
    self._frame['rsi_trend']   = self._frame['rsi_b_trend'] + self._frame['rsi_s_trend']

    # Calculate parabolic sar trend
    self._frame['psar_b_trend'] = np.where(self._frame['psarbull'] != '-', 1.0, 0.0)
    self._frame['psar_s_trend'] = np.where(self._frame['psarbear'] != '-', -1.0, 0.0)
    self._frame['psar_trend']   = self._frame['psar_b_trend'] + self._frame['psar_s_trend']

    # Define green and red candle
    self._frame['green_candle'] = np.where(self._frame['open'] < self._frame['close'], 1.0, 0.0)
    self._frame['red_candle']   = np.where(self._frame['open'] > self._frame['close'], -1.0, 0.0)
    self._frame['candle']       = self._frame['green_candle'] + self._frame['red_candle']

    # Find the biggest and lowest line of alligator
    self._frame['biggest_alligator'] = self._frame[['lips', 'teeth', 'jaw']].max(axis=1)
    self._frame['lowest_alligator']  = self._frame[['lips', 'teeth', 'jaw']].min(axis=1)

    # Determine the candle is above or below the alligator
    self._frame['alligator_b_trend'] = np.where(self._frame['low'] > self._frame['biggest_alligator'], 1.0, 0.0)
    self._frame['alligator_s_trend'] = np.where(self._frame['high'] < self._frame['lowest_alligator'], -1.0, 0.0)
    self._frame['alligator_trend']   = self._frame['alligator_b_trend'] + self._frame['alligator_s_trend']

    # Get signal
    self._frame['signal'] = np.where((self._frame['macd_trend'] == self._frame['alligator_trend']) & 
                                     (self._frame['macd_trend'] == self._frame['psar_trend']) &
                                     (self._frame['macd_trend'] == self._frame['smi_trend']) &
                                     (self._frame['macd_trend'] == self._frame['smi_trend']) &
                                     (self._frame['macd_trend'] == self._frame['smi_trend']), self._frame['macd_trend'], 0.0)
    self._frame['signal'] = self._frame['alligator_trend']

    # Set stop signal
    self._frame['stop'] = np.where(self._frame['signal'] == 0.0, 1.0, 0.0)

    # Set stop loss
    self._frame['b_sl'] = np.where(self._frame['signal'] == 1.0, self._frame['low'], 0.0)
    self._frame['s_sl'] = np.where(self._frame['signal'] == -1.0, self._frame['high'], 0.0)
    self._frame['sl'] = self._frame['b_sl'] + self._frame['s_sl']

    # Filter noise
    # self._frame['signal'] = np.where(self._frame['signal'] == self._frame['signal'].diff(), self._frame['signal'], 0.0)
    # self._frame['stop'] = np.where(self._frame['stop'] == self._frame['stop'].diff(), self._frame['stop'], 0.0)

    # Rename
    self._frame['signal'] = np.where(self._frame['signal'] == 1.0, 'buy', 
                            np.where(self._frame['signal'] == -1.0, 'sell', '-'))
    self._frame['stop_signal'] = np.where(self._frame['stop'] != 0.0, 'stop', '-')
    self._frame['stop_loss'] = np.where(self._frame['sl'] != 0.0, self._frame['sl'], '-')

    # Clean up before sending back.
    self._frame.drop(
        labels=[
          'rsi',
          'macd', 'signal_line', 'macd_histogram',
          'lips', 'teeth', 'jaw',
          'psarbull', 'psarbear',
          'smi', 'smi_signal',
          'rsi_b_trend', 'rsi_s_trend',
          'psar_b_trend', 'psar_s_trend',
          'alligator_b_trend', 'alligator_s_trend',
          'biggest_alligator', 'lowest_alligator',
          'green_candle', 'red_candle',
          'b_sl', 's_sl'
        ],
        axis=1,
        inplace=True
    )

    return self._frame
  
  def fractals_alligator(self) -> None:

    self._strategy_name = 'fractals_alligator'

    # Indicators
    self._indicator_client.rsi()
    self._indicator_client.macd()
    self._indicator_client.alligator()
    self._indicator_client.heikin_ashi()
    self._indicator_client.parabolic_sar()
    self._indicator_client.donchian_channel()
    self._indicator_client.stochastic_oscillator()
    self._indicator_client.fractal_chaos_oscillator(column_name='fco')
    self.fractals_alligator_strategy()

    self._indicator_client.implement_strategy(column_name=self._strategy_name, strategy=self.fractals_alligator_strategy)
  
  def fractals_alligator_strategy(self) -> pd.DataFrame:

    # Calculate rsi trend
    self._frame['rsi_b_trend'] = np.where(self._frame['rsi'] >= 60, 1.0, 0.0)
    self._frame['rsi_s_trend'] = np.where(self._frame['rsi'] <= 40, -1.0, 0.0)
    self._frame['rsi_trend']   = self._frame['rsi_b_trend'] + self._frame['rsi_s_trend']

    # Calculate MACD trend
    self._frame['macd_trend'] = np.where(self._frame['macd'] > self._frame['signal_line'], 1.0, -1.0)

    # Determine the lack of the market
    self._frame['macd_gap'] = np.where(abs(self._frame['macd_histogram']) > 0.2, True, False)
    self._frame['macd_market_trend'] = np.where((self._frame['macd_gap'] == False) &
                                           (self._frame['macd_gap'].shift(1) == False) & 
                                           (self._frame['macd_gap'].shift(2) == False), False, True)

    # Define macd histogram trend
    self._frame['macd_histogram_trend'] = np.where(self._frame['macd_histogram'] > self._frame['macd_histogram'].shift(1), 1.0, -1.0)
    self._frame['macd_histogram_trend'] = np.where((self._frame['macd_histogram_trend'] == self._frame['macd_histogram_trend'].shift(1)) &
                                                   (self._frame['macd_histogram_trend'] == self._frame['macd_histogram_trend'].shift(2)), 1.0, -1.0)

    # Find the biggest and lowest line of alligator
    self._frame['biggest_alligator'] = self._frame[['lips', 'teeth', 'jaw']].max(axis=1)
    self._frame['lowest_alligator']  = self._frame[['lips', 'teeth', 'jaw']].min(axis=1)

    # Determine the candle is above or below the alligator
    self._frame['alligator_b_trend'] = np.where(self._frame['low'] > self._frame['biggest_alligator'], 1.0, 0.0)
    self._frame['alligator_s_trend'] = np.where(self._frame['high'] < self._frame['lowest_alligator'], -1.0, 0.0)
    self._frame['alligator_trend']   = self._frame['alligator_b_trend'] + self._frame['alligator_s_trend']

    # Calculate parabolic sar trend
    self._frame['psar_b_trend'] = np.where(self._frame['psarbull'] != '-', 1.0, 0.0)
    self._frame['psar_s_trend'] = np.where(self._frame['psarbear'] != '-', -1.0, 0.0)
    self._frame['psar_trend']   = self._frame['psar_b_trend'] + self._frame['psar_s_trend']

    # Calculate stochastic oscillator trend
    self._frame['stoch_b_trend'] = np.where((self._frame['%K'] < self._frame['%D']) & (self._frame['%K'] <= 50), 1.0, 0.0)
    self._frame['stoch_s_trend'] = np.where((self._frame['%K'] > self._frame['%D']) & (self._frame['%K'] >= 50), -1.0, 0.0)
    self._frame['stoch_trend']   = self._frame['stoch_b_trend'] + self._frame['stoch_s_trend']

    # Calculate heikin ashi trend
    self._frame['HA_b_trend'] = np.where(self._frame['HA_open'] < self._frame['HA_close'], 1.0, 0.0)
    self._frame['HA_s_trend'] = np.where(self._frame['HA_open'] > self._frame['HA_close'], -1.0, 0.0)
    self._frame['HA_trend']   = self._frame['HA_b_trend'] + self._frame['HA_s_trend']

    # Calculate donchian channel trend
    self._frame['donchian_b_trend'] = np.where((self._frame['donchian_upper'] > self._frame['donchian_upper'].shift(1)) & 
                                               (self._frame['donchian_upper'] < self._frame['high']), 1.0, 0.0)
    self._frame['donchian_s_trend'] = np.where((self._frame['donchian_lower'] < self._frame['donchian_lower'].shift(1)) & 
                                               (self._frame['donchian_lower'] > self._frame['low']), -1.0, 0.0)
    self._frame['donchian_trend']   = self._frame['donchian_b_trend'] + self._frame['donchian_s_trend']
    self._frame['donchian_trend']   = np.where((self._frame['donchian_middle'] == self._frame['donchian_middle'].shift(1)) & 
                                               (self._frame['donchian_middle'] == self._frame['donchian_middle'].shift(2)), False, True)

    # Define green and red candle
    self._frame['green_candle'] = np.where(self._frame['open'] < self._frame['close'], 1.0, 0.0)
    self._frame['red_candle']   = np.where(self._frame['open'] > self._frame['close'], -1.0, 0.0)
    self._frame['candle']       = self._frame['green_candle'] + self._frame['red_candle']

    # Calculate candle trend
    self._frame['candle_trend'] = np.where(self._frame['candle'] == self._frame['candle'].shift(1), self._frame['candle'], 0.0)

    # Define the current candle low (high) is above (below) the previous candel low (high) while buy (sell)
    self._frame['candle_b_trend'] = np.where((self._frame['candle_trend'] == 1.0) & (self._frame['low'] > self._frame['low'].shift(1)), self._frame['candle_trend'], 0.0)
    self._frame['candle_s_trend'] = np.where((self._frame['candle_trend'] == -1.0) & (self._frame['high'] < self._frame['high'].shift(1)), self._frame['candle_trend'], 0.0)
    self._frame['candle_trend'] = self._frame['candle_b_trend'] + self._frame['candle_s_trend']

    # Determine the market trend
    self._frame['signal'] = np.where((self._frame['macd_trend'] == self._frame['alligator_trend']) & 
                                    (self._frame['macd_trend'] == self._frame['psar_trend']) & 
                                    (self._frame['macd_trend'] == self._frame['HA_trend']) & 
                                    (self._frame['macd_trend'] == self._frame['rsi_trend']) & 
                                    # (self._frame['macd_trend'] == self._frame['donchian_trend']) & 
                                    # (self._frame['macd_trend'] == self._frame['macd_histogram_trend']) & 
                                    # (self._frame['macd_trend'] == self._frame['stoch_trend']) & 
                                    # (self._frame['donchian_trend']) & 
                                    (self._frame['macd_histogram_trend']), self._frame['macd_trend'], 0.0)

    # Find signal
    # self._frame['signal'] = np.where(self._frame['trend'] == self._frame['candle_trend'], self._frame['trend'], 0.0)
    
    # Define stop signal
    self._frame['stop1'] = np.where(self._frame['macd_trend'] != self._frame['macd_trend'].shift(1), 1.0, 0.0)
    self._frame['stop2'] = np.where(self._frame['alligator_trend'].shift(1) == -self._frame['alligator_trend'].diff(), 1.0, 0.0)
    self._frame['stop3'] = np.where(self._frame['psar_trend'] != self._frame['psar_trend'].shift(1), 1.0, 0.0)
    # self._frame['stop4'] = np.where(self._frame['trend'] == self._frame['fco'], 1.0, 0.0)
    self._frame['stop5'] = np.where(self._frame['HA_trend'] != self._frame['HA_trend'].shift(1), 1.0, 0.0)
    self._frame['stop6'] = np.where(self._frame['macd_histogram_trend'] != self._frame['macd_histogram_trend'].shift(1), 1.0, 0.0)
    self._frame['stop7'] = np.where(self._frame['donchian_trend'].shift(1) == -self._frame['donchian_trend'].diff(), 1.0, 0.0)
    self._frame['stop7'] = np.where(self._frame['donchian_trend'] == False, 1.0, 0.0)
    self._frame['stop'] = self._frame['stop1'] + self._frame['stop2'] + self._frame['stop5']+ self._frame['stop6']
    self._frame['stop'] = np.where(self._frame['stop'] != 0.0, 1.0, 0.0)

    # Set stop loss
    # self._frame['b_sl'] = np.where(self._frame['signal'] == 1.0, self._frame['biggest_alligator'], 0.0)
    # self._frame['s_sl'] = np.where(self._frame['signal'] == -1.0, self._frame['lowest_alligator'], 0.0)
    # self._frame['sl'] = self._frame['b_sl'] + self._frame['s_sl']

    # # Set take profit
    # self._frame['b_tp'] = np.where(self._frame['signal'] == 1.0,  (3 * self._frame['close'] - 2 * self._frame['sl']), 0.0)
    # self._frame['s_tp'] = np.where(self._frame['signal'] == -1.0, (3 * self._frame['close'] + 2 * self._frame['sl']), 0.0)
    # self._frame['tp'] = self._frame['b_tp'] + self._frame['s_tp']

    # Filter noise
    # self._frame['signal'] = np.where(self._frame['signal'] == self._frame['signal'].diff(), self._frame['signal'], 0.0)
    # self._frame['stop'] = np.where(self._frame['stop'] == self._frame['stop'].diff(), self._frame['stop'], 0.0)

    # Rename
    self._frame['signal'] = np.where(self._frame['signal'] == 1.0, 'buy', 
                            np.where(self._frame['signal'] == -1.0, 'sell', '-'))
    self._frame['stop_signal'] = np.where((self._frame['stop'] != 0.0) & (self._frame['signal'] == '-'), 'stop', '-')
    # self._frame['stop_loss'] = np.where(self._frame['sl'] != 0.0, self._frame['sl'], '-')
    # self._frame['take_profit'] = np.where(self._frame['tp'] != 0.0, self._frame['tp'], '-')

    # self._frame['signal'] = 'buy'

    # Clean up before sending back.
    self._frame.drop(
        labels=[
                'macd', 'signal_line', 'macd_histogram', 
                'lips', 'teeth', 'jaw',
                'psarbull', 'psarbear', 
                'fco',
                'rsi',
                '%K', '%D',
                'donchian_upper', 'donchian_lower', 'donchian_middle',
                'macd_gap', 'macd_market_trend',
                'biggest_alligator', 'lowest_alligator',
                'alligator_b_trend', 'alligator_s_trend', 
                'HA_open', 'HA_close', 'HA_b_trend', 'HA_s_trend', 
                'rsi_b_trend', 'rsi_s_trend', 
                'psar_b_trend', 'psar_s_trend', 
                'stoch_b_trend', 'stoch_s_trend', 
                'donchian_b_trend', 'donchian_s_trend',
                'green_candle', 'red_candle', 'candle', 
                'candle_b_trend', 'candle_s_trend',
                'macd_trend', 'alligator_trend', 'psar_trend', 'HA_trend', 'stoch_trend', 'donchian_trend', 'rsi_trend', 'candle_trend',
                'stop'
              ],
        axis=1,
        inplace=True
    )

    return self._frame
  
  def xiang_strategy_indicators(self) -> None:

    self._strategy_name = 'xiang_strategy'

    # Indicators
    self._indicator_client.macd()
    self._indicator_client.parabolic_sar()
    self._indicator_client.stochastic_oscillator(period=5, smoothing_period=5)
    self._indicator_client.sma(period=200, column_name='sma_200')
    self._indicator_client.average_true_range(column_name='atr')
    self.xiang_strategy()
    self._indicator_client.implement_strategy(column_name=self._strategy_name, strategy=self.xiang_strategy)

  def xiang_strategy(self) -> pd.DataFrame:

    # Set trend
    self._frame['macd_trend'] = np.where(self._frame['macd'] > self._frame['signal_line'], 1.0, -1.0)

    self._frame['psar_b_trend'] = np.where(self._frame['psarbull'] != '-', 1.0, 0.0)
    self._frame['psar_s_trend'] = np.where(self._frame['psarbear'] != '-', -1.0, 0.0)
    self._frame['psar_trend']   = self._frame['psar_b_trend'] + self._frame['psar_s_trend']

    self._frame['stoch_b_trend'] = np.where((self._frame['%K'] > self._frame['%D']) & (self._frame['%K'] < 30), 1.0, 0.0)
    self._frame['stoch_s_trend'] = np.where((self._frame['%K'] < self._frame['%D']) & (self._frame['%K'] > 70), -1.0, 0.0)
    self._frame['stoch_trend']   = self._frame['stoch_b_trend'] + self._frame['stoch_s_trend']
    # self._frame['stoch_trend'] = np.where(self._frame['%K'] < self._frame['%D'], 1.0, -1.0)

    self._frame['sma_b_trend'] = np.where(self._frame['low'] > self._frame['sma_200'], 1.0, 0.0)
    self._frame['sma_s_trend'] = np.where(self._frame['high'] < self._frame['sma_200'], -1.0, 0.0)
    self._frame['sma_trend'] = self._frame['sma_b_trend'] + self._frame['sma_s_trend']

    # Filter signal
    self._frame['signal'] = np.where(self._frame['macd_trend'] != self._frame['psar_trend'], 0.0, 
                            np.where(self._frame['macd_trend'] != self._frame['stoch_trend'], 0.0, self._frame['macd_trend']))
                            # np.where(self._frame['macd_trend'] != self._frame['sma_trend'], 0.0, self._frame['macd_trend'])))

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

  # def get_strategy_signals(self) -> Union[pd.DataFrame, None]:

  #   # Grab the last rows.
  #   last_rows = self._stock_frame.symbol_groups.tail(1)

  #   # Define a list of conditions.
  #   conditions = {}

  #   # Get signals
  #   signals = last_rows['signal']
  #   if "close_signal" in self._signals: close_signals = last_rows[self._signals['close_signal']]
  #   # atr           = last_rows['atr']

  #   # Filter out signals
  #   buys = sells = close = pd.Series()
  #   buys:  pd.Series = signals.where(lambda x: x == 'buy').dropna()
  #   sells: pd.Series = signals.where(lambda x: x == 'sell').dropna()
  #   # close: pd.Series = close_signals.where(lambda x: x == 'close').dropna().rename("close")

  #   # Set stop loss
  #   # buy_index  = np.intersect1d(stop_loss.index, buys.index)
  #   # sell_index = np.intersect1d(stop_loss.index, sells.index)

  #   # buys  = stop_loss.loc[buy_index].rename("buys")
  #   # sells = stop_loss.loc[sell_index].rename("sells")

  #   conditions['buys'] = buys.rename("buys")
  #   conditions['sells'] = sells.rename("sells")
  #   conditions['close'] = close.rename("close")
  #   # conditions['atr'] = atr.rename("atr")

  #   return conditions

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
