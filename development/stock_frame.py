import pandas as pd
import pprint
import requests
import ast
import operator
import numpy as np 
# import matplotlib.pyplot as plt

from typing import List
from typing import Dict
from typing import Union

from pandas.core.groupby import DataFrameGroupBy
from pandas.core.window import RollingGroupby
from pandas.core.window import Window

# able to print 500 rowss
pd.set_option('display.max_rows', 1000)

class StockFrame():

    def __init__(self, data: List[Dict], period: str) -> None:

        self._data = data
        self._period = period
        self._frame: pd.DataFrame = self.create_frame()
        self._symbol_groups = None
        self._symbol_rolling_groups = None

    @property
    def frame(self) -> pd.DataFrame:
        return self._frame

    @property
    def period(self) -> str:
        return self._period

    @property
    def symbol_groups(self) -> DataFrameGroupBy:

        self._symbol_groups: DataFrameGroupBy = self._frame.groupby(
            by='instrumentid',
            as_index=False,
            sort=True
        )

        return self._symbol_groups
    
    def create_frame(self) -> pd.DataFrame:
        # Make a data frame.
        price_df = pd.DataFrame(data=self._data)
        price_df = self._set_multi_index(price_df=price_df)

        return price_df

    # Converts the dataframe to a multi-index data frame.
    def _set_multi_index(self, price_df: pd.DataFrame) -> pd.DataFrame:

        price_df = price_df.set_index(keys=['instrumentid', 'fromdate'])

        return price_df

    def add_rows(self, data: List[Dict]) -> None:

        column_names = ['open', 'close', 'high', 'low']

        for quote in data:

            # Define the Index Tuple.
            row_id = (quote['instrumentid'], quote['fromdate'])

            # Define the values.
            row_values = [
                quote['open'],
                quote['close'],
                quote['high'],
                quote['low'],
            ]

            # Create a new row.
            new_row = pd.Series(data=row_values)

            # Add the row.
            self.frame.loc[row_id, column_names] = new_row.values

            self.frame.sort_index(inplace=True)

    def do_stock_exist(self, symbol: str) -> bool:

        return symbol in self._frame.index

    def do_indicator_exist(self, column_names: List[str]) -> bool:

        if set(column_names).issubset(self._frame.columns):
            return True
        else:
            raise KeyError("The following indicator columns are missing from the StockFrame: {missing_columns}".format(
                missing_columns=set(column_names).difference(
                    self._frame.columns)
            ))
            
    def _check_signals(self, indicators: dict, indciators_comp_key: List[str], indicators_key: List[str]) -> Union[pd.DataFrame, None]:
        """Returns the last row of the StockFrame if conditions are met.

        Overview:
        ----
        Before a trade is executed, we must check to make sure if the
        conditions that warrant a `buy` or `sell` signal are met. This
        method will take last row for each symbol in the StockFrame and
        compare the indicator column values with the conditions specified
        by the user.

        If the conditions are met the row will be returned back to the user.

        Arguments:
        ----
        indicators {dict} -- A dictionary containing all the indicators to be checked
            along with their buy and sell criteria.

        indicators_comp_key List[str] -- A list of the indicators where we are comparing
            one indicator to another indicator.

        indicators_key List[str] -- A list of the indicators where we are comparing
            one indicator to a numerical value.

        Returns:
        ----
        {Union[pd.DataFrame, None]} -- If signals are generated then, a pandas.DataFrame object
            will be returned. If no signals are found then nothing will be returned.
        """

        # Grab the last rows.
        last_rows = self._symbol_groups.tail(1)

        # Define a list of conditions.
        conditions = {}

        # Check to see if all the columns exist.
        if self.do_indicator_exist(column_names=indicators_key):

            for indicator in indicators_key:

                column = last_rows[indicator]

                # Grab the Buy & Sell Condition.
                buy_condition_target = indicators[indicator]['buy']
                sell_condition_target = indicators[indicator]['sell']

                buy_condition_operator = indicators[indicator]['buy_operator']
                sell_condition_operator = indicators[indicator]['sell_operator']

                condition_1: pd.Series = buy_condition_operator(
                    column, buy_condition_target
                )
                condition_2: pd.Series = sell_condition_operator(
                    column, sell_condition_target
                )

                condition_1 = condition_1.where(lambda x: x == True).dropna()
                condition_2 = condition_2.where(lambda x: x == True).dropna()

                conditions['buys'] = condition_1
                conditions['sells'] = condition_2
        
        # Store the indicators in a list.
        check_indicators = [] 
        
        # Split the name so we can check if the indicator exist.
        for indicator in indciators_comp_key:
            parts = indicator.split('_comp_')
            check_indicators += parts

        if self.do_indicator_exist(column_names=check_indicators):

            for indicator in indciators_comp_key:
                
                # Split the indicators.
                parts = indicator.split('_comp_')

                # Grab the indicators that need to be compared.
                indicator_1 = last_rows[parts[0]]
                indicator_2 = last_rows[parts[1]]

                # If we have a buy operator, grab it.
                if indicators[indicator]['buy_operator']:

                    # Grab the Buy Operator.
                    buy_condition_operator = indicators[indicator]['buy_operator']

                    # Grab the Condition.
                    condition_1: pd.Series = buy_condition_operator(
                        indicator_1, indicator_2
                    )

                    # Keep the one's that aren't null.
                    condition_1 = condition_1.where(lambda x: x == True).dropna()

                    # Add it as a buy signal.
                    conditions['buys'] = condition_1

                # If we have a sell operator, grab it.
                if indicators[indicator]['sell_operator']:

                    # Grab the Sell Operator.
                    sell_condition_operator = indicators[indicator]['sell_operator']

                    # Store it in a Pd.Series.
                    condition_2: pd.Series = sell_condition_operator(
                        indicator_1, indicator_2
                    )

                    # keep the one's that aren't null.
                    condition_2 = condition_2.where(lambda x: x == True).dropna()

                    # Add it as a sell signal.
                    conditions['sells'] = condition_2       

        return conditions
    
    def _get_signals(self) -> Union[pd.DataFrame, None]:

        # Grab the last rows.
        last_rows = self._symbol_groups.tail(1)

        # Define a list of conditions.
        conditions = {}

        # Get signals
        stop = last_rows['stop']
        crossover_signal = last_rows['CROSS']
        macd_signal = last_rows['MACD']

        # Combine signals
        signals = pd.concat([crossover_signal, macd_signal])

        buys:  pd.Series = signals.where(lambda x: x == 'buy').dropna().rename("buys")
        sells: pd.Series = signals.where(lambda x: x == 'sell').dropna().rename("sells")
        stops: pd.Series = stop.where(lambda x: x == 'stop').dropna().rename("stops")

        conditions['buys'] = buys
        conditions['sells'] = sells
        conditions['stops'] = stops

        return conditions
