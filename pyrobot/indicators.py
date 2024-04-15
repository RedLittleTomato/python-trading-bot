import numpy as np
import pandas as pd
import math

from typing import Any
from typing import Dict
from typing import Union

from pyrobot.stock_frame import StockFrame

class Indicators():

    """
    Represents an Indicator Object which can be used
    to easily add technical indicators to a StockFrame.
    """    
    
    def __init__(self, price_data_frame: StockFrame) -> None:
        """Initalizes the Indicator Client.

        Arguments:
        ----
        price_data_frame {pyrobot.StockFrame} -- The price data frame which is used to add indicators to.
            At a minimum this data frame must have the following columns: `['timestamp','close','open','high','low']`.
        
        Usage:
        ----
            >>> historical_prices_df = trading_robot.grab_historical_prices(
                start=start_date,
                end=end_date,
                bar_size=1,
                bar_type='minute'
            )
            >>> price_data_frame = pd.DataFrame(data=historical_prices)
            >>> indicator_client = Indicators(price_data_frame=price_data_frame)
            >>> indicator_client.price_data_frame
        """

        self._stock_frame: StockFrame = price_data_frame
        self._price_groups = price_data_frame.symbol_groups
        self._current_indicators = {}
        self._indicator_signals = {}
        self._frame = self._stock_frame.frame

        self._indicators_crossover_key = []
        self._indicators_comp_key = []
        self._indicators_key = []
        
        if self.is_multi_index:
            True

    def get_indicator_signal(self, indicator: str= None) -> Dict:
        """Return the raw Pandas Dataframe Object.

        Arguments:
        ----
        indicator {Optional[str]} -- The indicator key, for example `ema` or `sma`.

        Returns:
        ----
        {dict} -- Either all of the indicators or the specified indicator.
        """

        if indicator and indicator in self._indicator_signals:
            return self._indicator_signals[indicator]
        else:      
            return self._indicator_signals
    
    def set_indicator_signal(self, indicator: str, buy: float, sell: float, condition_buy: Any, condition_sell: Any, 
                             buy_max: float = None, sell_max: float = None, condition_buy_max: Any = None, condition_sell_max: Any = None) -> None:
        """Used to set an indicator where one indicator crosses above or below a certain numerical threshold.

        Arguments:
        ----
        indicator {str} -- The indicator key, for example `ema` or `sma`.

        buy {float} -- The buy signal threshold for the indicator.
        
        sell {float} -- The sell signal threshold for the indicator.

        condition_buy {str} -- The operator which is used to evaluate the `buy` condition. For example, `">"` would
            represent greater than or from the `operator` module it would represent `operator.gt`.
        
        condition_sell {str} -- The operator which is used to evaluate the `sell` condition. For example, `">"` would
            represent greater than or from the `operator` module it would represent `operator.gt`.

        buy_max {float} -- If the buy threshold has a maximum value that needs to be set, then set the `buy_max` threshold.
            This means if the signal exceeds this amount it WILL NOT PURCHASE THE INSTRUMENT. (defaults to None).
        
        sell_max {float} -- If the sell threshold has a maximum value that needs to be set, then set the `buy_max` threshold.
            This means if the signal exceeds this amount it WILL NOT SELL THE INSTRUMENT. (defaults to None).

        condition_buy_max {str} -- The operator which is used to evaluate the `buy_max` condition. For example, `">"` would
            represent greater than or from the `operator` module it would represent `operator.gt`. (defaults to None).
        
        condition_sell_max {str} -- The operator which is used to evaluate the `sell_max` condition. For example, `">"` would
            represent greater than or from the `operator` module it would represent `operator.gt`. (defaults to None).
        """

        # Add the key if it doesn't exist.
        if indicator not in self._indicator_signals:
            self._indicator_signals[indicator] = {}
            self._indicators_key.append(indicator)      

        # Add the signals.
        self._indicator_signals[indicator]['buy'] = buy     
        self._indicator_signals[indicator]['sell'] = sell
        self._indicator_signals[indicator]['buy_operator'] = condition_buy
        self._indicator_signals[indicator]['sell_operator'] = condition_sell

        # Add the max signals
        self._indicator_signals[indicator]['buy_max'] = buy_max  
        self._indicator_signals[indicator]['sell_max'] = sell_max
        self._indicator_signals[indicator]['buy_operator_max'] = condition_buy_max
        self._indicator_signals[indicator]['sell_operator_max'] = condition_sell_max

    def set_indicator_signal_compare(self, indicator_1: str, indicator_2: str, condition_buy: Any, condition_sell: Any) -> None:
        """Used to set an indicator where one indicator is compared to another indicator.

        Overview:
        ----
        Some trading strategies depend on comparing one indicator to another indicator.
        For example, the Simple Moving Average crossing above or below the Exponential
        Moving Average. This will be used to help build those strategies that depend
        on this type of structure.

        Arguments:
        ----
        indicator_1 {str} -- The first indicator key, for example `ema` or `sma`.

        indicator_2 {str} -- The second indicator key, this is the indicator we will compare to. For example,
            is the `sma` greater than the `ema`.

        condition_buy {str} -- The operator which is used to evaluate the `buy` condition. For example, `">"` would
            represent greater than or from the `operator` module it would represent `operator.gt`.
        
        condition_sell {str} -- The operator which is used to evaluate the `sell` condition. For example, `">"` would
            represent greater than or from the `operator` module it would represent `operator.gt`.
        """

        # Define the key.
        key = "{ind_1}_comp_{ind_2}".format(
            ind_1=indicator_1,
            ind_2=indicator_2
        )

        # Add the key if it doesn't exist.
        if key not in self._indicator_signals:
            self._indicator_signals[key] = {}
            self._indicators_comp_key.append(key)   

        # Grab the dictionary.
        indicator_dict = self._indicator_signals[key]

        # Add the signals.
        indicator_dict['type'] = 'comparison'
        indicator_dict['indicator_1'] = indicator_1
        indicator_dict['indicator_2'] = indicator_2
        indicator_dict['buy_operator'] = condition_buy
        indicator_dict['sell_operator'] = condition_sell

    def set_crossover_indicator_signal(self, indicator_1: str, indicator_2: str, indicator_3: str, condition_buy: Any=None, condition_sell: Any=None) -> None:

        # Define the key.
        key = "crossover_{ind_1}_{ind_2}_{ind_3}".format(
            ind_1=indicator_1,
            ind_2=indicator_2,
            ind_3=indicator_3
        )

        # Add the key if it doesn't exist.
        if key not in self._indicator_signals:
            self._indicator_signals[key] = {}
            self._indicators_crossover_key.append(key)   

        # Grab the dictionary.
        indicator_dict = self._indicator_signals[key]

        indicator_dict['type'] = 'crossover'
        indicator_dict['indicator_1'] = indicator_1
        indicator_dict['indicator_2'] = indicator_2
        indicator_dict['indicator_3'] = indicator_3
        indicator_dict['buy_operator'] = condition_buy
        indicator_dict['sell_operator'] = condition_sell

    @property
    def price_data_frame(self) -> pd.DataFrame:
        """Return the raw Pandas Dataframe Object.

        Returns:
        ----
        {pd.DataFrame} -- A multi-index data frame.
        """

        return self._frame

    @price_data_frame.setter
    def price_data_frame(self, price_data_frame: pd.DataFrame) -> None:
        """Sets the price data frame.

        Arguments:
        ----
        price_data_frame {pd.DataFrame} -- A multi-index data frame.
        """

        self._frame = price_data_frame

    @property
    def is_multi_index(self) -> bool:
        """Specifies whether the data frame is a multi-index dataframe.

        Returns:
        ----
        {bool} -- `True` if the data frame is a `pd.MultiIndex` object. `False` otherwise.
        """

        if isinstance(self._frame.index, pd.MultiIndex):
            return True
        else:
            return False

    def change_in_price(self, column_name: str = 'change_in_price') -> pd.DataFrame:
        """Calculates the Change in Price.

        Returns:
        ----
        {pd.DataFrame} -- A data frame with the Change in Price included.
        """

        locals_data = locals()
        del locals_data['self']
        
        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.change_in_price

        self._frame[column_name] = self._price_groups['close'].transform(
            lambda x: x.diff()
        )

        return self._frame

    def rsi(self, period: int = 14, method: str = 'wilders', ema: bool = True, column_name: str = 'rsi') -> pd.DataFrame:
        """Calculates the Relative Strength Index (RSI).

        Arguments:
        ----
        period {int} -- The number of periods to use to calculate the RSI.

        Keyword Arguments:
        ----
        method {str} -- The calculation methodology. (default: {'wilders'})

        Returns:
        ----
        {pd.DataFrame} -- A Pandas data frame with the RSI indicator included.

        Usage:
        ----
            >>> historical_prices_df = trading_robot.grab_historical_prices(
                start=start_date,
                end=end_date,
                bar_size=1,
                bar_type='minute'
            )
            >>> price_data_frame = pd.DataFrame(data=historical_prices)
            >>> indicator_client = Indicators(price_data_frame=price_data_frame)
            >>> indicator_client.rsi(period=14)
            >>> price_data_frame = inidcator_client.price_data_frame
        """

        locals_data = locals()
        del locals_data['self']

        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.rsi

        # # First calculate the Change in Price.
        # if 'change_in_price' not in self._frame.columns:
        #     self.change_in_price()

        # # Define the up days.
        # self._frame['up_day'] = self._price_groups['change_in_price'].transform(
        #     lambda x : np.where(x >= 0, x, 0)
        # )

        # # Define the down days.
        # self._frame['down_day'] = self._price_groups['change_in_price'].transform(
        #     lambda x : np.where(x < 0, x.abs(), 0)
        # )

        # # Calculate the EWMA for the Up days.
        # self._frame['ewma_up'] = self._price_groups['up_day'].transform(
        #     lambda x: x.ewm(span = period).mean()
        # )

        # # Calculate the EWMA for the Down days.
        # self._frame['ewma_down'] = self._price_groups['down_day'].transform(
        #     lambda x: x.ewm(span = period).mean()
        # )

        # # Calculate the Relative Strength
        # self._frame['relative_strength'] = self._frame['ewma_up'] / self._frame['ewma_down']

        # # Calculate the Relative Strength Index
        # self._frame[column_name] = self._frame['relative_strength'].apply(lambda x: 100 - (100 / (x + 1)))
        
        # # Clean up before sending back.
        # self._frame.drop(
        #     labels=['ewma_up', 'ewma_down', 'down_day', 'up_day', 'relative_strength', 'change_in_price'],
        #     axis=1,
        #     inplace=True
        # )

        close_delta = self._price_groups['close'].diff()

        # Make two series: one for lower closes and one for higher closes
        up = close_delta.clip(lower=0)
        down = -1 * close_delta.clip(upper=0)
        
        if ema == True:
            # Use exponential moving average
            ma_up = up.ewm(com = period - 1, adjust=True, min_periods = period).mean()
            ma_down = down.ewm(com = period - 1, adjust=True, min_periods = period).mean()
        else:
            # Use simple moving average
            ma_up = up.rolling(window = period).mean()
            ma_down = down.rolling(window = period).mean()
            
        rsi = ma_up / ma_down
        rsi = 100 - (100/(1 + rsi))
        self._frame[column_name] = rsi

        return self._frame

    def sma(self, period: int, field: str = 'close', column_name: str = 'sma') -> pd.DataFrame:
        """Calculates the Simple Moving Average (SMA).

        Arguments:
        ----
        period {int} -- The number of periods to use when calculating the SMA.

        Returns:
        ----
        {pd.DataFrame} -- A Pandas data frame with the SMA indicator included.

        Usage:
        ----
            >>> historical_prices_df = trading_robot.grab_historical_prices(
                start=start_date,
                end=end_date,
                bar_size=1,
                bar_type='minute'
            )
            >>> price_data_frame = pd.DataFrame(data=historical_prices)
            >>> indicator_client = Indicators(price_data_frame=price_data_frame)
            >>> indicator_client.sma(period=100)
        """

        locals_data = locals()
        del locals_data['self']

        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.sma

        # Add the SMA
        self._frame[column_name] = self._price_groups[field].transform(
            lambda x: x.rolling(window=period).mean()
        )

        self._frame.loc[0:period-1,column_name] = 0

        return self._frame
    
    def smma(self, period: int, field: str = 'close', column_name: str = 'smma') -> pd.DataFrame:
        """Calculates the Smoothed Moving Average (SMMA).

        Arguments:
        ----
        period {int} -- The number of periods to use when calculating the SMMA.

        Returns:
        ----
        {pd.DataFrame} -- A Pandas data frame with the SMMA indicator included.

        Usage:
        ----
            >>> historical_prices_df = trading_robot.grab_historical_prices(
                start=start_date,
                end=end_date,
                bar_size=1,
                bar_type='minute'
            )
            >>> price_data_frame = pd.DataFrame(data=historical_prices)
            >>> indicator_client = Indicators(price_data_frame=price_data_frame)
            >>> indicator_client.smma(period=100)
        """

        locals_data = locals()
        del locals_data['self']

        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.smma

        # Calculate medium
        self._frame['medium'] = (self._frame['high'] + self._frame['low']) / 2

        # Add the SMMA
        self._frame[column_name] = self._price_groups['medium'].transform(
            lambda x: x.ewm(span=(2 * period - 1)).mean()
        )

        # Clean up before sending back.
        self._frame.drop(
            labels=['medium'],
            axis=1,
            inplace=True
        )

        return self._frame 

    def ema(self, period: int, field: str = 'close', alpha: float = 0.0, column_name = 'ema') -> pd.DataFrame:
        """Calculates the Exponential Moving Average (EMA).

        Arguments:
        ----
        period {int} -- The number of periods to use when calculating the EMA.

        alpha {float} -- The alpha weight used in the calculation. (default: {0.0})

        Returns:
        ----
        {pd.DataFrame} -- A Pandas data frame with the EMA indicator included.

        Usage:
        ----
            >>> historical_prices_df = trading_robot.grab_historical_prices(
                start=start_date,
                end=end_date,
                bar_size=1,
                bar_type='minute'
            )
            >>> price_data_frame = pd.DataFrame(data=historical_prices)
            >>> indicator_client = Indicators(price_data_frame=price_data_frame)
            >>> indicator_client.ema(period=50, alpha=1/50)
        """

        locals_data = locals()
        del locals_data['self']

        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.ema

        # Add the EMA
        self._frame[column_name] = self._price_groups[field].transform(
            lambda x: x.ewm(span=period).mean()
        )

        self._frame.loc[0:period-1,column_name] = 0

        return self._frame

    def rate_of_change(self, period: int = 1, column_name: str = 'rate_of_change') -> pd.DataFrame:
        """Calculates the Rate of Change (ROC).

        Arguments:
        ----
        period {int} -- The number of periods to use when calculating 
            the ROC. (default: {1})

        Returns:
        ----
        {pd.DataFrame} -- A Pandas data frame with the ROC indicator included.

        Usage:
        ----
            >>> historical_prices_df = trading_robot.grab_historical_prices(
                start=start_date,
                end=end_date,
                bar_size=1,
                bar_type='minute'
            )
            >>> price_data_frame = pd.DataFrame(data=historical_prices)
            >>> indicator_client = Indicators(price_data_frame=price_data_frame)
            >>> indicator_client.rate_of_change()
        """
        locals_data = locals()
        del locals_data['self']

        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.rate_of_change

        # Add the Momentum indicator.
        self._frame[column_name] = self._price_groups['close'].transform(
            lambda x: x.pct_change(periods=period)
        )

        return self._frame        
    
    def alligator(self, column_name: str = 'alligator') -> pd.DataFrame:

        locals_data = locals()
        del locals_data['self']

        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.alligator

        # Calculate alligator's lips, teeth, jaws
        self.smma(period = 5,  column_name = 'lips')  # Green
        self.smma(period = 8,  column_name = 'teeth') # Red
        self.smma(period = 13, column_name = 'jaw')  # Blue

        # Move to offest
        self._frame['lips'] = self._price_groups['lips'].shift(3)
        self._frame['teeth'] = self._price_groups['teeth'].shift(5)
        self._frame['jaw'] = self._price_groups['jaw'].shift(8)

        return self._frame

    def awesome_oscillator(self, column_name: str = 'awesome_oscillator') -> pd.DataFrame:

        # Calculation
        # AO = SMA 5 OF MEDIAN PRICE - SMA 34 OF MEDIAN PRICE

        locals_data = locals()
        del locals_data['self']

        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.awesome_oscillator

        # Calculate sma 5 & 34
        self.sma(period = 5,  column_name = 'sma_5')
        self.sma(period = 34, column_name = 'sma_34')

        self._frame[column_name] = self._frame['sma_5'] - self._frame['sma_34']

        # Clean up before sending back.
        self._frame.drop(
            labels=['sma_5', 'sma_34'],
            axis=1,
            inplace=True
        )

        return self._frame
    
    def donchian_channel(self, high_period: int = 20, low_period: int = 20, column_name: str = 'donchian_channel') -> pd.DataFrame:

        locals_data = locals()
        del locals_data['self']

        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.donchian_channel

        # Calculate donchian upper channel
        self._frame['donchian_upper'] = self._price_groups['high'].transform(
            lambda x: x.rolling(window=high_period).max()
        )

        # Calculate donchian lower channel
        self._frame['donchian_lower'] = self._price_groups['low'].transform(
            lambda x: x.rolling(window=low_period).min()
        )

        # Calculate donchian middle channel
        self._frame['donchian_middle'] = (self._frame['donchian_upper'] + self._frame['donchian_lower']) / 2

        # Move donchain channel to next candle
        self._frame['donchian_upper'] = self._frame['donchian_upper'].shift(1)
        self._frame['donchian_lower'] = self._frame['donchian_lower'].shift(1)
        self._frame['donchian_middle'] = self._frame['donchian_middle'].shift(1)

        return self._frame   

    def trading_within(self, start_time: str = '00:00:00', end_time: str = '23:59:59', column_name: str = 'trading_within') -> pd.DataFrame:
        """Only able to trade within the time.

        Arguments:
        ----
        start_time {str} -- The starting time. (example: 10:30:00)
        end_time {str} -- The ending time. (example: 10:30:00)

        Returns:
        ----
        {pd.DataFrame} -- A Pandas data frame with able to trade bool included.

        """
        locals_data = locals()
        del locals_data['self']

        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.trading_within

        # Get time
        self._frame['time'] = self._frame.index.get_level_values(1).str.split('t').str[1].str[:-1]

        # Filter time range
        self._frame[column_name] = np.where((self._frame['time'] >= start_time) & (self._frame['time'] <= end_time), True, False)

        # Clean up before sending back.
        self._frame.drop(
            labels=['time'],
            axis=1,
            inplace=True
        )

        return self._frame

    def fractal(self, column_name: str = 'fractal') -> pd.DataFrame:

        locals_data = locals()
        del locals_data['self']

        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.fractal

        # Calculate fractal up - bullish breakout signal
        self._frame['bull_fractal'] = np.where((self._price_groups['high'] > self._price_groups['high'].shift(2)) & 
                                               (self._price_groups['high'] > self._price_groups['high'].shift(1)) &
                                               (self._price_groups['high'] > self._price_groups['high'].shift(-1)) &
                                               (self._price_groups['high'] > self._price_groups['high'].shift(-2)), 1.0, 0.0)

        # Calculate fractal down - bearish breakout signal
        self._frame['bear_fractal'] = np.where((self._price_groups['low'] < self._price_groups['low'].shift(2)) & 
                                               (self._price_groups['low'] < self._price_groups['low'].shift(1)) &
                                               (self._price_groups['low'] < self._price_groups['low'].shift(-1)) &
                                               (self._price_groups['low'] < self._price_groups['low'].shift(-2)), -1.0, 0.0)

        # Clean up before sending back.
        self._frame.drop(
            labels=[],
            axis=1,
            inplace=True
        )

        return self._frame
    
    def fractal_chaos_oscillator(self, column_name: str = 'fractal_chaos_oscillator') -> pd.DataFrame:

        locals_data = locals()
        del locals_data['self']

        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.fractal_chaos_oscillator

        # Calculate fractal up - bullish breakout signal
        self._frame['bull_fractal'] = np.where((self._frame['high'] > self._frame['high'].shift(2)) & 
                                               (self._frame['high'] > self._frame['high'].shift(1)) &
                                               (self._frame['high'] > self._frame['high'].shift(-1)) &
                                               (self._frame['high'] > self._frame['high'].shift(-2)), 1.0, 0.0)

        # Calculate fractal down - bearish breakout signal
        self._frame['bear_fractal'] = np.where((self._frame['low'] < self._frame['low'].shift(2)) & 
                                               (self._frame['low'] < self._frame['low'].shift(1)) &
                                               (self._frame['low'] < self._frame['low'].shift(-1)) &
                                               (self._frame['low'] < self._frame['low'].shift(-2)), -1.0, 0.0)

        # Calculate fractal chaos oscillator
        self._frame['bull_fractal'] = self._frame['bull_fractal'].shift(2)                                       
        self._frame['bear_fractal'] = self._frame['bear_fractal'].shift(2)
        self._frame[column_name] = self._frame['bull_fractal'] + self._frame['bear_fractal']

        # Clean up before sending back.
        self._frame.drop(
            labels=['bull_fractal', 'bear_fractal'],
            axis=1,
            inplace=True
        )

        return self._frame 

    def heikin_ashi(self, column_name: str = 'heikin_ashi') -> pd.DataFrame:

        locals_data = locals()
        del locals_data['self']

        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.heikin_ashi

        # Calculate Heikin Ashi open
        self._frame['HA_open'] = (self._frame['open'].shift(1) + self._frame['close'].shift(1)) / 2

        # Calculate Heikin Ashi close
        self._frame['HA_close'] = (self._frame['open'] + self._frame['low'] + self._frame['close'] + self._frame['high']) / 4

        # Clean up before sending back.
        self._frame.drop(
            labels=[],
            axis=1,
            inplace=True
        )

        return self._frame

    def bollinger_bands(self, period: int = 20, column_name: str = 'bollinger_bands') -> pd.DataFrame:

        locals_data = locals()
        del locals_data['self']

        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.bollinger_bands

        # Define the Moving Avg.
        self._frame['moving_avg'] = self._price_groups['close'].transform(
            lambda x : x.rolling(window=period).mean()
        )

        # Define Moving Std.
        self._frame['moving_std'] = self._price_groups['close'].transform(
            lambda x : x.rolling(window=period).std()
        )

        # Define the Upper Band.
        self._frame['band_upper'] = self._frame['moving_avg'] + (2 * self._frame['moving_std'])

        # Define the Middle Band
        self._frame['band_middle'] = self._frame['moving_avg']

        # Define the Lower Band
        self._frame['band_lower'] = self._frame['moving_avg'] - (2 * self._frame['moving_std'])

        # Define the Bollinger Band Width
        self._frame['band_width'] = (self._frame['band_upper'] - self._frame['band_lower']) / self._frame['band_middle']

        # Define the Bollinger Upper band and Lower diff
        self._frame['band_diff'] = (self._frame['band_upper'] - self._frame['band_lower'])

        # Clean up before sending back.
        self._frame.drop(
            labels=['moving_avg', 'moving_std'],
            axis=1,
            inplace=True
        )

        return self._frame   

    def average_true_range(self, period: int = 14, column_name: str ='average_true_range') -> pd.DataFrame:
        """Calculates the Average True Range (ATR).

        Arguments:
        ----
        period {int} -- The number of periods to use when calculating 
            the ATR. (default: {14})

        Returns:
        ----
        {pd.DataFrame} -- A Pandas data frame with the ATR included.

        Usage:
        ----
            >>> historical_prices_df = trading_robot.grab_historical_prices(
                start=start_date,
                end=end_date,
                bar_size=1,
                bar_type='minute'
            )
            >>> price_data_frame = pd.DataFrame(data=historical_prices)
            >>> indicator_client = Indicators(price_data_frame=price_data_frame)
            >>> indicator_client.average_true_range()
        """

        locals_data = locals()
        del locals_data['self']

        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.average_true_range


        # Calculate the different parts of True Range.
        self._frame['true_range_0'] = abs(self._frame['high'] - self._frame['low'])
        self._frame['true_range_1'] = abs(self._frame['high'] - self._frame.groupby(level=0)['close'].shift()) # groupby(level=0) 
        self._frame['true_range_2'] = abs(self._frame['low'] - self._frame.groupby(level=0)['close'].shift())  # --> to prevent get others
                                                                                                               #     symbol data while shift

        # Grab the Max.
        self._frame['true_range'] = self._frame[['true_range_0', 'true_range_1', 'true_range_2']].max(axis=1)

        # Calculate the Average True Range.
        self._frame[column_name] = self._frame['true_range'].transform(
            lambda x: x.ewm(span = period, min_periods = period).mean()
        )

        # Make NaN to 0
        # self._frame[column_name] = np.where(np.isnan(self._frame[column_name]), 0, self._frame[column_name])

        # Clean up before sending back.
        self._frame.drop(
            labels=['true_range_0', 'true_range_1', 'true_range_2', 'true_range'],
            axis=1,
            inplace=True
        )

        return self._frame

    def supertrend(self, atr_length: int = 10, multiplier : int = 3, column_name: str ='supertrend') -> pd.DataFrame:
        
        # Calculate high low average
        self._frame['hla'] = (self._frame['high'] + self._frame['low']) / 2

        # Calculate 10-day average true range
        self.average_true_range(period=10, column_name='10_atr')

        # Calculate basic and final upper band and lower band
        self._frame['basic_upperband'] = self._frame['hla'] + (multiplier * self._frame['10_atr'])
        self._frame['basic_lowerband'] = self._frame['hla'] - (multiplier * self._frame['10_atr'])

        # Initial final upper band and lower band same as basic upper band and lower band
        self._frame['final_upperband'] = self._frame['basic_upperband']
        self._frame['final_lowerband'] = self._frame['basic_lowerband']

        # Calculate final upper band and lower band
        self._frame['final_upperband'] = np.where((self._frame['basic_upperband'] < self._frame['final_upperband'].shift(1)) | 
                                                  (self._frame['close'].shift(1)  > self._frame['final_upperband'].shift(1)), self._frame['basic_upperband'], self._frame['final_upperband'].shift(1))
        self._frame['final_lowerband'] = np.where((self._frame['basic_lowerband'] > self._frame['final_lowerband'].shift(1)) | 
                                                  (self._frame['close'].shift(1)  < self._frame['final_lowerband'].shift(1)), self._frame['basic_lowerband'], self._frame['final_lowerband'].shift(1))

        # Calculate supertrend
        self._frame['supertrend'] = True
        # self._frame[column_name] = np.where((self._frame['supertrend'].shift(1) == self._frame['final_upperband'].shift(1)) & (self._frame['close'] < self._frame['final_upperband']), self._frame['final_upperband'], 
        #                            np.where((self._frame['supertrend'].shift(1) == self._frame['final_upperband'].shift(1)) & (self._frame['close'] > self._frame['final_upperband']), self._frame['final_lowerband'], 
        #                            np.where((self._frame['supertrend'].shift(1) == self._frame['final_lowerband'].shift(1)) & (self._frame['close'] > self._frame['final_lowerband']), self._frame['final_lowerband'], 
        #                            np.where((self._frame['supertrend'].shift(1) == self._frame['final_lowerband'].shift(1)) & (self._frame['close'] < self._frame['final_lowerband']), self._frame['final_upperband'], 
        #                                     self._frame['supertrend']))))

        # for i in range(1, len(self._frame.index)):
        #     curr, prev = i, i-1
            
        #     # if current close price crosses above upperband
        #     if self._frame['close'][curr] > self._frame['final_upperband'][prev]:
        #         self._frame['supertrend'][curr] = True
        #     # if current close price crosses below lowerband
        #     elif self._frame['close'][curr] < self._frame['final_lowerband'][prev]:
        #         self._frame['supertrend'][curr] = False
        #     # else, the trend continues
        #     else:
        #         self._frame['supertrend'][curr] = self._frame['supertrend'][prev]
                
        #         # adjustment to the final bands
        #         if self._frame['supertrend'][curr] == True and self._frame['final_lowerband'][curr] < self._frame['final_lowerband'][prev]:
        #             self._frame['final_lowerband'][curr] = self._frame['final_lowerband'][prev]
        #         if self._frame['supertrend'][curr] == False and self._frame['final_upperband'][curr] > self._frame['final_upperband'][prev]:
        #             self._frame['final_upperband'][curr] = self._frame['final_upperband'][prev]

        #     # to remove bands according to the trend direction
        #     if self._frame['supertrend'][curr] == True:
        #         self._frame['final_upperband'][curr] = np.nan
        #     else:
        #         self._frame['final_lowerband'][curr] = np.nan

        final_upperband_list = []
        final_lowerband_list = []
        supertrend_list = []

        for index, symbol in self._price_groups:

            length = len(symbol)
            final_upperband = list(symbol['final_upperband'])
            final_lowerband = list(symbol['final_lowerband'])
            close = list(symbol['close'])

            supertrend = [None] * length

            for i in range(1, length):
                curr, prev = i, i-1
                
                # if current close price crosses above upperband
                if close[curr] > final_upperband[prev]:
                    supertrend[curr] = True
                # if current close price crosses below lowerband
                elif close[curr] < final_lowerband[prev]:
                    supertrend[curr] = False
                # else, the trend continues
                else:
                    supertrend[curr] = supertrend[prev]
                    
                    # adjustment to the final bands
                    if supertrend[curr] == True and final_lowerband[curr] < final_lowerband[prev]:
                        final_lowerband[curr] = final_lowerband[prev]
                    if supertrend[curr] == False and final_upperband[curr] > final_upperband[prev]:
                        final_upperband[curr] = final_upperband[prev]

                # to remove bands according to the trend direction
                if supertrend[curr] == True:
                    final_upperband[curr] = np.nan
                else:
                    final_lowerband[curr] = np.nan
            
            # join list
            final_upperband_list += final_upperband
            final_lowerband_list += final_lowerband
            supertrend_list += supertrend

        self._frame['final_upperband'] = final_upperband_list
        self._frame['final_lowerband'] = final_lowerband_list
        self._frame['supertrend'] = supertrend_list

        self._frame['supertrend'] = np.where(self._frame['supertrend'] == True, 1.0, -1.0)

        # Clean up before sending back.
        self._frame.drop(
            labels=['hla', '10_atr', 'basic_upperband', 'basic_lowerband'],
            axis=1,
            inplace=True
        )

        return self._frame

    def macd(self, fast_period: int = 12, slow_period: int = 26, column_name: str = 'macd') -> pd.DataFrame:
        """Calculates the Moving Average Convergence Divergence (MACD).

        Arguments:
        ----
        fast_period {int} -- The number of periods to use when calculating 
            the fast moving MACD. (default: {12})

        slow_period {int} -- The number of periods to use when calculating 
            the slow moving MACD. (default: {26})

        Returns:
        ----
        {pd.DataFrame} -- A Pandas data frame with the MACD included.

        Usage:
        ----
            >>> historical_prices_df = trading_robot.grab_historical_prices(
                start=start_date,
                end=end_date,
                bar_size=1,
                bar_type='minute'
            )
            >>> price_data_frame = pd.DataFrame(data=historical_prices)
            >>> indicator_client = Indicators(price_data_frame=price_data_frame)
            >>> indicator_client.macd(fast_period=12, slow_period=26)
        """

        locals_data = locals()
        del locals_data['self']

        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.macd

        # Calculate the Fast Moving MACD.
        self._frame['macd_fast'] = self._price_groups['close'].transform(
            lambda x: x.ewm(span = fast_period, min_periods = fast_period).mean()
        )

        # Calculate the Slow Moving MACD.
        self._frame['macd_slow'] = self._price_groups['close'].transform(
            lambda x: x.ewm(span = slow_period, min_periods = slow_period).mean()
        )

        # Calculate the difference between the fast and the slow.
        self._frame['macd'] = round(self._frame['macd_fast'] - self._frame['macd_slow'], 6)

        # Calculate the Exponential moving average of the fast.
        self._frame['signal_line'] = self._price_groups['macd'].transform(
            lambda x: round(x.ewm(span = 9, min_periods = 8).mean(), 6)
        )

        # Calculate the MACD histogram.
        self._frame['macd_histogram'] = self._frame['macd'] - self._frame['signal_line']

        # Clean up before sending back.
        self._frame.drop(
            labels=['macd_fast', 'macd_slow'],
            axis=1,
            inplace=True
        )

        return self._frame 

    def mass_index(self, period: int = 9, column_name: str = 'mass_index') -> pd.DataFrame:
        """Calculates the Mass Index indicator.

        Arguments:
        ----
        period {int} -- The number of periods to use when calculating 
            the mass index. (default: {9})

        Returns:
        ----
        {pd.DataFrame} -- A Pandas data frame with the Mass Index included.

        Usage:
        ----
            >>> historical_prices_df = trading_robot.grab_historical_prices(
                start=start_date,
                end=end_date,
                bar_size=1,
                bar_type='minute'
            )
            >>> price_data_frame = pd.DataFrame(data=historical_prices)
            >>> indicator_client = Indicators(price_data_frame=price_data_frame)
            >>> indicator_client.mass_index(period=9)
        """

        locals_data = locals()
        del locals_data['self']

        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.mass_index

        # Calculate the Diff.
        self._frame['diff'] = self._frame['high'] - self._frame['low']

        # Calculate Mass Index 1
        self._frame['mass_index_1'] = self._frame['diff'].transform(
            lambda x: x.ewm(span = period, min_periods = period - 1).mean()
        )

        # Calculate Mass Index 2
        self._frame['mass_index_2'] = self._frame['mass_index_1'].transform(
            lambda x: x.ewm(span = period, min_periods = period - 1).mean()
        )
        
        # Grab the raw index.
        self._frame['mass_index_raw'] = self._frame['mass_index_1'] / self._frame['mass_index_2']

        # Calculate the Mass Index.
        self._frame['mass_index'] = self._frame['mass_index_raw'].transform(
            lambda x: x.rolling(window=25).sum()
        )

        # Clean up before sending back.
        self._frame.drop(
            labels=['diff', 'mass_index_1', 'mass_index_2', 'mass_index_raw'],
            axis=1,
            inplace=True
        )

        return self._frame
    
    def force_index(self, period: int, column_name: str = 'force_index') -> pd.DataFrame:
        """Calculates the Force Index.

        Arguments:
        ----
        period {int} -- The number of periods to use when calculating 
            the force index.

        Returns:
        ----
        {pd.DataFrame} -- A Pandas data frame with the force index included.

        Usage:
        ----
            >>> historical_prices_df = trading_robot.grab_historical_prices(
                start=start_date,
                end=end_date,
                bar_size=1,
                bar_type='minute'
            )
            >>> price_data_frame = pd.DataFrame(data=historical_prices)
            >>> indicator_client = Indicators(price_data_frame=price_data_frame)
            >>> indicator_client.force_index(period=9)
        """

        locals_data = locals()
        del locals_data['self']

        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.force_index

        # Calculate the Force Index.
        self._frame[column_name] = self._frame['close'].diff(period)  * self._frame['volume'].diff(period)

        return self._frame

    def ease_of_movement(self, period: int, column_name: str = 'ease_of_movement') -> pd.DataFrame:
        """Calculates the Ease of Movement.

        Arguments:
        ----
        period {int} -- The number of periods to use when calculating 
            the Ease of Movement.

        Returns:
        ----
        {pd.DataFrame} -- A Pandas data frame with the Ease of Movement included.

        Usage:
        ----
            >>> historical_prices_df = trading_robot.grab_historical_prices(
                start=start_date,
                end=end_date,
                bar_size=1,
                bar_type='minute'
            )
            >>> price_data_frame = pd.DataFrame(data=historical_prices)
            >>> indicator_client = Indicators(price_data_frame=price_data_frame)
            >>> indicator_client.ease_of_movement(period=9)
        """

        locals_data = locals()
        del locals_data['self']

        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.ease_of_movement
        
        # Calculate the ease of movement.
        high_plus_low = (self._frame['high'].diff(1) + self._frame['low'].diff(1))
        diff_divi_vol = (self._frame['high'] - self._frame['low']) / (2 * self._frame['volume'])
        self._frame['ease_of_movement_raw'] = high_plus_low * diff_divi_vol

        # Calculate the Rolling Average of the Ease of Movement.
        self._frame['ease_of_movement'] = self._frame['ease_of_movement_raw'].transform(
            lambda x: x.rolling(window=period).mean()
        )

        # Clean up before sending back.
        self._frame.drop(
            labels=['ease_of_movement_raw'],
            axis=1,
            inplace=True
        )

        return self._frame

    def commodity_channel_index(self, period: int, column_name: str = 'commodity_channel_index') -> pd.DataFrame:
        """Calculates the Commodity Channel Index.

        Arguments:
        ----
        period {int} -- The number of periods to use when calculating 
            the Commodity Channel Index.

        Returns:
        ----
        {pd.DataFrame} -- A Pandas data frame with the Commodity Channel Index included.

        Usage:
        ----
            >>> historical_prices_df = trading_robot.grab_historical_prices(
                start=start_date,
                end=end_date,
                bar_size=1,
                bar_type='minute'
            )
            >>> price_data_frame = pd.DataFrame(data=historical_prices)
            >>> indicator_client = Indicators(price_data_frame=price_data_frame)
            >>> indicator_client.commodity_channel_index(period=9)
        """

        locals_data = locals()
        del locals_data['self']

        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.commodity_channel_index

        # Calculate the Typical Price.
        self._frame['typical_price'] = (self._frame['high'] + self._frame['low'] + self._frame['close']) / 3

        # Calculate the Rolling Average of the Typical Price.
        self._frame['typical_price_mean'] = self._frame['pp'].transform(
            lambda x: x.rolling(window=period).mean()
        )

        # Calculate the Rolling Standard Deviation of the Typical Price.
        self._frame['typical_price_std'] = self._frame['pp'].transform(
            lambda x: x.rolling(window=period).std()
        )

        # Calculate the Commodity Channel Index.
        self._frame[column_name] = self._frame['typical_price_mean'] / self._frame['typical_price_std']

        # Clean up before sending back.
        self._frame.drop(
            labels=['typical_price', 'typical_price_mean', 'typical_price_std'],
            axis=1,
            inplace=True
        )

        return self._frame

    def standard_deviation(self, period: int, column_name: str = 'standard_deviation') -> pd.DataFrame:
        """Calculates the Standard Deviation.

        Arguments:
        ----
        period {int} -- The number of periods to use when calculating 
            the standard deviation.

        Returns:
        ----
        {pd.DataFrame} -- A Pandas data frame with the Standard Deviation included.

        Usage:
        ----
            >>> historical_prices_df = trading_robot.grab_historical_prices(
                start=start_date,
                end=end_date,
                bar_size=1,
                bar_type='minute'
            )
            >>> price_data_frame = pd.DataFrame(data=historical_prices)
            >>> indicator_client = Indicators(price_data_frame=price_data_frame)
            >>> indicator_client.standard_deviation(period=9)
        """

        locals_data = locals()
        del locals_data['self']

        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.standard_deviation

        # Calculate the Standard Deviation.
        self._frame[column_name] = self._frame['close'].transform(
            lambda x: x.ewm(span=period).std()
        )

        return self._frame

    def chaikin_oscillator(self, period: int, column_name: str = 'chaikin_oscillator') -> pd.DataFrame:
        """Calculates the Chaikin Oscillator.

        Arguments:
        ----
        period {int} -- The number of periods to use when calculating 
            the Chaikin Oscillator.

        Returns:
        ----
        {pd.DataFrame} -- A Pandas data frame with the Chaikin Oscillator included.

        Usage:
        ----
            >>> historical_prices_df = trading_robot.grab_historical_prices(
                start=start_date,
                end=end_date,
                bar_size=1,
                bar_type='minute'
            )
            >>> price_data_frame = pd.DataFrame(data=historical_prices)
            >>> indicator_client = Indicators(price_data_frame=price_data_frame)
            >>> indicator_client.chaikin_oscillator(period=9)
        """

        locals_data = locals()
        del locals_data['self']

        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.chaikin_oscillator

        # Calculate the Money Flow Multiplier.
        money_flow_multiplier_top = 2 * (self._frame['close'] - self._frame['high'] - self._frame['low'])
        money_flow_multiplier_bot = (self._frame['high'] - self._frame['low'])

        # Calculate Money Flow Volume
        self._frame['money_flow_volume'] = (money_flow_multiplier_top / money_flow_multiplier_bot) * self._frame['volume']

        # Calculate the 3-Day moving average of the Money Flow Volume.
        self._frame['money_flow_volume_3'] = self._frame['money_flow_volume'].transform(
            lambda x: x.ewm(span=3, min_periods=2).mean()
        )

        # Calculate the 10-Day moving average of the Money Flow Volume.
        self._frame['money_flow_volume_10'] = self._frame['money_flow_volume'].transform(
            lambda x: x.ewm(span=10, min_periods=9).mean()
        )

        # Calculate the Chaikin Oscillator.
        self._frame[column_name] = self._frame['money_flow_volume_3'] - self._frame['money_flow_volume_10']

        # Clean up before sending back.
        self._frame.drop(
            labels=['money_flow_volume_3', 'money_flow_volume_10', 'money_flow_volume'],
            axis=1,
            inplace=True
        )

        return self._frame

    def kst_oscillator(self, r1: int, r2: int, r3: int, r4: int, n1: int, n2: int, n3: int, n4: int, column_name: str = 'kst_oscillator') -> pd.DataFrame:
        """Calculates the Mass Index indicator.

        Arguments:
        ----
        period {int} -- The number of periods to use when calculating 
            the mass index. (default: {9})

        Returns:
        ----
        {pd.DataFrame} -- A Pandas data frame with the Mass Index included.

        Usage:
        ----
            >>> historical_prices_df = trading_robot.grab_historical_prices(
                start=start_date,
                end=end_date,
                bar_size=1,
                bar_type='minute'
            )
            >>> price_data_frame = pd.DataFrame(data=historical_prices)
            >>> indicator_client = Indicators(price_data_frame=price_data_frame)
            >>> indicator_client.mass_index(period=9)
        """

        locals_data = locals()
        del locals_data['self']

        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.kst_oscillator

        # Calculate the ROC 1.
        self._frame['roc_1'] = self._frame['close'].diff(r1 - 1)  / self._frame['close'].shift(r1 - 1)

        # Calculate the ROC 2.
        self._frame['roc_2'] = self._frame['close'].diff(r2 - 1)  / self._frame['close'].shift(r2 - 1)

        # Calculate the ROC 3.
        self._frame['roc_3'] = self._frame['close'].diff(r3 - 1)  / self._frame['close'].shift(r3 - 1)

        # Calculate the ROC 4.
        self._frame['roc_4'] = self._frame['close'].diff(r4 - 1)  / self._frame['close'].shift(r4 - 1)


        # Calculate the Mass Index.
        self._frame['roc_1_n'] = self._frame['roc_1'].transform(
            lambda x: x.rolling(window=n1).sum()
        )

        # Calculate the Mass Index.
        self._frame['roc_2_n'] = self._frame['roc_2'].transform(
            lambda x: x.rolling(window=n2).sum()
        )

        # Calculate the Mass Index.
        self._frame['roc_3_n'] = self._frame['roc_3'].transform(
            lambda x: x.rolling(window=n3).sum()
        )

        # Calculate the Mass Index.
        self._frame['roc_4_n'] = self._frame['roc_4'].transform(
            lambda x: x.rolling(window=n4).sum()
        )

        self._frame[column_name] = 100 * (self._frame['roc_1_n'] + 2 * self._frame['roc_2_n'] + 3 * self._frame['roc_3_n'] + 4 * self._frame['roc_4_n'])
        self._frame[column_name + "_signal"] = self._frame['column_name'].transform(
            lambda x: x.rolling().mean()
        )
        
        # Clean up before sending back.
        self._frame.drop(
            labels=['roc_1', 'roc_2', 'roc_3', 'roc_4', 'roc_1_n', 'roc_2_n', 'roc_3_n', 'roc_4_n'],
            axis=1,
            inplace=True
        )

        return self._frame

    def stochastic_oscillator(self, period: int = 14, smoothing_period: int = 3, column_name: str = 'stochastic_oscillator') -> pd.DataFrame:
        """Calculates the Stochastic Oscillator.

        %k < 20 and %d < 20 and %k > %d - Oversold   (buy)
        %k > 80 and %d > 80 and %k < %d - Overbought (sell)

        Returns:
        ----
        {pd.DataFrame} -- A Pandas data frame with the Stochastic Oscillator included.

        Usage:
        ----
            >>> historical_prices_df = trading_robot.grab_historical_prices(
                start=start_date,
                end=end_date,
                bar_size=1,
                bar_type='minute'
            )
            >>> price_data_frame = pd.DataFrame(data=historical_prices)
            >>> indicator_client = Indicators(price_data_frame=price_data_frame)
            >>> indicator_client.stochastic_oscillator()
        """

        locals_data = locals()
        del locals_data['self']

        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.stochastic_oscillator

        # Define the highest high and lowest low within the period
        self._frame['highest_high'] = self._price_groups['high'].transform(
            lambda x : x.rolling(window=period).max()
        )

        self._frame['lowest_low'] = self._price_groups['low'].transform(
            lambda x : x.rolling(window=period).min()
        )

        # Calculate the Fast Stochastic indicator (%K).
        self._frame['%K'] = (
            (self._frame['close'] - self._frame['lowest_low']) * 100 /
            (self._frame['highest_high'] - self._frame['lowest_low'])
        )

        # Calculate the Slow Stochastic Indicator (%D).
        self._frame['%D'] = self._price_groups['%K'].transform(
            lambda x : x.rolling(window=smoothing_period).mean()
        )

        # Clean up before sending back.
        self._frame.drop(
            labels=['highest_high', 'lowest_low'],
            axis=1,
            inplace=True
        )

        return self._frame
    
    def stochastic_momentum_index(self, k_periods: int = 10, k_smoothing_periods: int = 3, k_double_smoothing_periods: int = 3, d_periods: int = 10, column_name: str = 'stochastic_momentum_index') -> pd.DataFrame:
        """Calculates the Stochastic Momentum Index.

        -40 - Oversold   (buy)
        40  - Overbought (sell)

        Returns:
        ----
        {pd.DataFrame} -- A Pandas data frame with the Stochastic Momentum Index included.

        Usage:
        ----
            >>> historical_prices_df = trading_robot.grab_historical_prices(
                start=start_date,
                end=end_date,
                bar_size=1,
                bar_type='minute'
            )
            >>> price_data_frame = pd.DataFrame(data=historical_prices)
            >>> indicator_client = Indicators(price_data_frame=price_data_frame)
            >>> indicator_client.stochastic_momentum_index()
        """

        locals_data = locals()
        del locals_data['self']

        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.stochastic_momentum_index

        # Calculate the highest high and lowest low within the period
        self._frame['highest_high'] = self._price_groups['high'].transform(
            lambda x : x.rolling(window=k_periods).max()
        )

        self._frame['lowest_low'] = self._price_groups['low'].transform(
            lambda x : x.rolling(window=k_periods).min()
        )

        # Calculate the midpoint price of the highest high and the lowest low in the selected range
        self._frame['midpoint'] = (self._frame['highest_high'] + self._frame['lowest_low']) / 2

        # Calculate the difference of bar’s closing price from the midpoint of the range
        self._frame['d'] = self._frame['close'] - self._frame['midpoint']

        # Calculate the difference of the highest high and the lowest low
        self._frame['hl'] = self._frame['highest_high'] - self._frame['lowest_low']

        # Calculate d & hl with ema
        self.ema(period=k_smoothing_periods, field='d', column_name='d_ema')
        self.ema(period=k_smoothing_periods, field='hl',column_name='hl_ema')

        # Calculate double d & hl with ema
        self.ema(period=k_double_smoothing_periods, field='d_ema', column_name='d_smooth')
        self.ema(period=k_double_smoothing_periods, field='hl_ema',column_name='hl_smooth')

        # Divide hl_smooth by 2
        self._frame['hl_smooth'] = self._frame['hl_smooth'] / 2

        # Calculate smi
        self._frame['smi'] = 100 * (self._frame['d_smooth'] / self._frame['hl_smooth'])

        # Calculate smi signal
        self.ema(period=d_periods, field='smi', column_name='smi_signal')

        # Clean up before sending back.
        self._frame.drop(
            labels=[
              'highest_high', 'lowest_low', 
              'midpoint', 'd', 'hl',
              'd_ema', 'hl_ema',
              'd_smooth', 'hl_smooth'
            ],
            axis=1,
            inplace=True
        )

        return self._frame 

    def parabolic_sar(self, min_af: float = 0.02, max_af: float = 0.2, column_name: str = 'parabolic_sar') -> pd.DataFrame:

        locals_data = locals()
        del locals_data['self']

        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = locals_data
        self._current_indicators[column_name]['func'] = self.parabolic_sar

        psar_list = []
        psarbear_list = []
        psarbull_list = []

        for index, symbol in self._price_groups:

            length = len(symbol)
            high = list(symbol['high'])
            low = list(symbol['low'])
            close = list(symbol['close'])
            psar = close[0:len(close)]
            psarbull = [None] * length
            psarbear = [None] * length
            bull = True
            af = min_af
            hp = high[0]
            lp = low[0]
            for i in range(2,length):
                if bull:
                    psar[i] = psar[i - 1] + af * (hp - psar[i - 1])
                else:
                    psar[i] = psar[i - 1] + af * (lp - psar[i - 1])
                reverse = False
                if bull:
                    if low[i] < psar[i]:
                        bull = False
                        reverse = True
                        psar[i] = hp
                        lp = low[i]
                        af = min_af
                else:
                    if high[i] > psar[i]:
                        bull = True
                        reverse = True
                        psar[i] = lp
                        hp = high[i]
                        af = min_af
                if not reverse:
                    if bull:
                        if high[i] > hp:
                            hp = high[i]
                            af = min(af + min_af, max_af)
                        if low[i - 1] < psar[i]:
                            psar[i] = low[i - 1]
                        if low[i - 2] < psar[i]:
                            psar[i] = low[i - 2]
                    else:
                        if low[i] < lp:
                            lp = low[i]
                            af = min(af + min_af, max_af)
                        if high[i - 1] > psar[i]:
                            psar[i] = high[i - 1]
                        if high[i - 2] > psar[i]:
                            psar[i] = high[i - 2]
                if bull:
                    psarbull[i] = psar[i]
                    psarbear[i] = '-'
                else:
                    psarbear[i] = psar[i]
                    psarbull[i] = '-'

            # join list
            psar_list += psar
            psarbear_list += psarbear
            psarbull_list += psarbull

        # self._frame[column_name] = psar_list
        self._frame['psarbear'] = psarbear_list
        self._frame['psarbull'] = psarbull_list

        return self._frame

    def implement_strategy(self, column_name: str, strategy):

        self._current_indicators[column_name] = {}
        self._current_indicators[column_name]['args'] = {}
        self._current_indicators[column_name]['func'] = strategy

    def refresh(self):
        """Updates the Indicator columns after adding the new rows."""

        # First update the groups since, we have new rows.
        self._price_groups = self._stock_frame.symbol_groups

        # Grab all the details of the indicators so far.
        for indicator in self._current_indicators:
            
            # Grab the function.
            indicator_argument = self._current_indicators[indicator]['args']

            # Grab the arguments.
            indicator_function = self._current_indicators[indicator]['func']

            # Update the function.
            indicator_function(**indicator_argument)

    def check_signals(self) -> Union[pd.DataFrame, None]:
        """Checks to see if any signals have been generated.

        Returns:
        ----
        {Union[pd.DataFrame, None]} -- If signals are generated then a pandas.DataFrame
            is returned otherwise nothing is returned.
        """

        signals_df = self._stock_frame._check_signals(
            indicators=self._indicator_signals,
            indciators_comp_key=self._indicators_comp_key,
            indicators_key=self._indicators_key
        )

        return signals_df
    
    def get_signals(self) -> Union[pd.DataFrame, None]:

        signals_df = self._stock_frame._get_signals()

        return signals_df


# #KST Oscillator  
# def KST(df, r1, r2, r3, r4, n1, n2, n3, n4):  
#     M = df['Close'].diff(r1 - 1)  
#     N = df['Close'].shift(r1 - 1)  
#     ROC1 = M / N  
#     M = df['Close'].diff(r2 - 1)  
#     N = df['Close'].shift(r2 - 1)  
#     ROC2 = M / N  
#     M = df['Close'].diff(r3 - 1)  
#     N = df['Close'].shift(r3 - 1)  
#     ROC3 = M / N  
#     M = df['Close'].diff(r4 - 1)  
#     N = df['Close'].shift(r4 - 1)  
#     ROC4 = M / N  
#     KST = pd.Series(pd.rolling_sum(ROC1, n1) + pd.rolling_sum(ROC2, n2) * 2 + pd.rolling_sum(ROC3, n3) * 3 +
#  pd.rolling_sum(ROC4, n4) * 4, name = 'KST_' + str(r1) + '_' + str(r2) + '_' + str(r3) + '_' + str(r4) + '_' +
#  str(n1) + '_' + str(n2) + '_' + str(n3) + '_' + str(n4))  
#     df = df.join(KST)  
#     return df

    ### Old
    # def bollinger_bands(self, period: int = 20, column_name: str = 'bollinger_bands') -> pd.DataFrame:
    #     """Calculates the Bollinger Bands.

    #     Arguments:
    #     ----
    #     period {int} -- The number of periods to use when calculating 
    #         the Bollinger Bands. (default: {20})

    #     Returns:
    #     ----
    #     {pd.DataFrame} -- A Pandas data frame with the Lower and Upper band
    #         indicator included.

    #     Usage:
    #     ----
    #         >>> historical_prices_df = trading_robot.grab_historical_prices(
    #             start=start_date,
    #             end=end_date,
    #             bar_size=1,
    #             bar_type='minute'
    #         )
    #         >>> price_data_frame = pd.DataFrame(data=historical_prices)
    #         >>> indicator_client = Indicators(price_data_frame=price_data_frame)
    #         >>> indicator_client.bollinger_bands()
    #     """
    #     locals_data = locals()
    #     del locals_data['self']

    #     self._current_indicators[column_name] = {}
    #     self._current_indicators[column_name]['args'] = locals_data
    #     self._current_indicators[column_name]['func'] = self.bollinger_bands

    #     # Define the Moving Avg.
    #     self._frame['moving_avg'] = self._price_groups['close'].transform(
    #         lambda x : x.rolling(window=period).mean()
    #     )

    #     # Define Moving Std.
    #     self._frame['moving_std'] = self._price_groups['close'].transform(
    #         lambda x : x.rolling(window=period).std()
    #     )

    #     # Define the Upper Band.
    #     self._frame['band_upper'] = 4 * (self._frame['moving_std'] / self._frame['moving_avg'])

    #     # Define the lower band
    #     self._frame['band_lower'] = (
    #         (self._frame['close'] - self._frame['moving_avg']) + 
    #         (2 * self._frame['moving_std']) / 
    #         (4 * self._frame['moving_std'])
    #     )

    #     # Clean up before sending back.
    #     self._frame.drop(
    #         labels=['moving_avg', 'moving_std'],
    #         axis=1,
    #         inplace=True
    #     )

    #     return self._frame   