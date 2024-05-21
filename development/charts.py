import numpy as np
import pandas as pd

from typing import Any
from typing import Dict
from typing import Union

from pyrobot.stock_frame import StockFrame

class Charts():

    """
    Represents a Chart Object which can be used
    to easily add chert patterns to a StockFrame.
    """    

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