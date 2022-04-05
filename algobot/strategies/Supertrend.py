from typing import List, Union
import time
import logging
from algobot.data import Data
import numpy as np
import  pandas as pd
import cProfile
import pstats

from algobot.enums import BEARISH, BULLISH
# from algobot.Superoption import Option
from algobot.traders.backtester import Backtester
from algobot.helpers import get_random_color
from algobot.algorithms import get_ema, get_sma, get_wma, supertrend, convert_renko, get_atr


from algobot.strategies.strategy import Strategy


from PyQt5.QtWidgets import (QApplication, QCompleter, QFileDialog,
                             QMainWindow, QMessageBox, QTableWidgetItem)




class Supertrend(Strategy):
    def __init__(self, parent=None, inputs: list = (None,) * 6, precision: int = 2):
        """
        Basic Moving Average strategy.
        """
        super().__init__(name='Supertrend', parent=parent, precision=precision)
        self.Buy_multiplier: float = inputs[0]
        self.Sell_multiplier: float = inputs[1]
        self.Parameter: str = inputs[2]
        self.ATR_buy_period: int = inputs[3]
        self.ATR_sell_period: int = inputs[4]
        self.ATR_period: int = inputs[5]
        self.dynamic = True
        self.description = "Supertrend strategy"
        self.loggern = logging.getLogger()
        self.loggern.setLevel(logging.INFO)
        self.formatter = logging.Formatter('%(asctime)s %(levelname)s::%(message)s')
        self.ts = time.time()
        # self.file_handler = logging.FileHandler('D:\Work\Programming\info' + str(self.ts) + '.log')
        # self.file_handler.setFormatter(self.formatter)
        # self.file_handler.setLevel(logging.DEBUG)
        # self.loggern.addHandler(self.file_handler)
        self.x = 1
        self.final_data = []
        self.final_data_current = []
        self.renko_current = {}
        self.renko = {}

        ma1 = f'{self.Buy_multiplier}{self.Sell_multiplier}({self.ATR_buy_period})({self.ATR_sell_period})  - {self.Parameter}'
        self.plotDict['Current Price'] = [self.get_current_trader_price(), '00ff00']
        self.plotDict['Close Price'] = [67767,'0000ff']
        self.plotDict['Supertrend'] = [45545,'000000']

        self.strategyDict['general'] = {
            'Buy Multiplier': self.Buy_multiplier,
            'Sell Multiplier': self.Sell_multiplier,
            'Parameter': self.Parameter,
            'ATR buy period': self.ATR_buy_period,
            'ATR sell period': self.ATR_sell_period,
            'ATR period': self.ATR_period

        }



        #if parent:  # Only validate if parent exists. If no parent, this mean's we're just calling this for param types.
        #   self.validate_options()

    def set_inputs(self, inputs: list):
        """
        Sets trading options provided.
        """
        self.Buy_multiplier = inputs[0]
        self.Sell_multiplier = inputs[1]
        self.Parameter = inputs[2]
        self.ATR_buy_period = inputs[3]
        self.ATR_sell_period = inputs[4]
        self.ATR_period = inputs[5]

    def get_min_option_period(self) -> int:
        """
        Returns the minimum period required to perform moving average calculations. For instance, if we needed to
        calculate SMA(25), we need at least 25 periods of data, and we'll only be able to start from the 26th period.
        :return: Minimum period of days required.
        """
        minimum = 10
        # for option in self.tradingOptions:
        minimum = max(minimum, self.ATR_sell_period, self.ATR_buy_period)
        return minimum

    @staticmethod
    def get_param_types() -> List[tuple]:
        """
        This function will return all the parameter types of the Moving Average strategy for the GUI.
        The moving average tuple will return a tuple type with all the supported moving averages.
        The parameter tuple will return a tuple type with all the supported parameters.
        The initial value will return the int type.
        The final value will return the int type.
        """
        
        parameters = ['High', 'Low', 'Open', 'Close', 'High/Low', 'Open/Close']
        return [('Buy_multiplier', float),
                ('Sell_multiplier', float),
                ('Parameter', tuple, parameters),
                ('ATR_buy_period', int),
                ('ATR_sell_period', int),
                ('ATR_period', int)
                ]

    def get_params(self) -> list:
        """
        This function will return all the parameters used for the Moving Average strategy.
        """
        return [
            self.Buy_multiplier,
            self.Sell_multiplier,
            self.Parameter,
            self.ATR_buy_period,
            self.ATR_sell_period,
            self.ATR_period
        ]

    def get_trend(self, data: Union[List[dict], Data] = None, log_data: bool = True) -> int:
        """
        This function should return the current trend for the Moving Average strategy with the provided data.
        :param data: Data container to get trend from - it can either be a list or a Data object.
        :param log_data: Boolean specifying whether current information regarding strategy should be logged or not.

        """
        # print('----------------------------------------------------------')
        # profile = cProfile.Profile()
        # profile.enable()
        parent = self.parent
        trends = []  # Current option trends. They all have to be the same to register a trend.

        data_obj = data


        if isinstance(data, Data):
            # Get a copy of the data + the current values. Note we create a copy because we don't want to mutate the
            # actual Data object. We limit data objects to hold 1000 items at a time, so this is not a very expensive
            # operation.

            data = data.data
                   # + [data.current_values]
            df = pd.DataFrame(data)
            print(len(df))
            df = df.tail(100)
            df = df.reset_index()
            df['date'] = df['date_utc']
            self.renko = convert_renko(df, data_obj.atr)
            self.final_data = self.renko.to_dict('records')
            self.plotDict['Close Price'] = [self.final_data[- 1]['close'], get_random_color()]
            self.plotDict['Current Price'] = [self.get_current_trader_price(), '00ff00']
            print('------------------------')
            print(self.final_data[- 1]['close'])
            print(data[-1]['close'])



        if type(data_obj) == list:  # This means it was called by the optimizer/backtester.

            #convert list to pandas dataframe and then back to list
            # atr = get_atr(self.ATR_period, data)


            print(self.parent)
            avg1 = supertrend(data, self.Buy_multiplier,self.Sell_multiplier, self.ATR_buy_period, self.ATR_sell_period)
        else:  # This means it was called by the live bot / simulation.

            print('aaaaaaaaaaaaaaa')
            avg1 = supertrend(self.final_data, self.Buy_multiplier, self.Sell_multiplier, self.ATR_buy_period, self.ATR_sell_period)

        prefix, interval = self.get_prefix_and_interval_type(data_obj)

        # Now, let's throw these values in the statistics window. Note that the prefix is necessary. The prefix is
        # either blank or "Lower Interval". The lower interval and regular interval keys need to be different.
        # Otherwise, they'll just override each other which would be chaos.
        self.strategyDict[interval][f'{prefix} Supertrend'] = avg1[1]


        # Same example as way above, but pretty much get a prettified string.
        ma1_string = f'{self.Buy_multiplier}{self.Sell_multiplier}({self.ATR_buy_period})({self.ATR_sell_period})'


        # Set the values to the statistics window dictionary.
        self.strategyDict[interval][f'{prefix}{ma1_string}'] = avg1[1]

        self.plotDict['Supertrend'] = [
            supertrend(data, self.Buy_multiplier, self.Sell_multiplier, self.ATR_buy_period, self.ATR_sell_period),
            'FF0000']


        if interval == 'regular' and not isinstance(data_obj, list):  # Only plot for regular interval values.
            # Note that the value of this dictionary is a list. The first contains the value and the second contains
            # the color. We only want to change the value, so modify the first value (which is at the 0th index).
            self.plotDict['Supertrend'][0] = avg1[1]


        # if log_data:  # If you want to log the data, set advanced logging to True. Note this will write a lot of data.
        #     self.parent.output_message(f'Supertrend: {avg1[1]}')






        if avg1[0] == 1.0 :
            trends.append(BULLISH)
                
        elif avg1[0] == 2.0 :
            trends.append(BEARISH)
        else:  # If they're the same, that means no trend.
            trends.append(None)

        if all(trend == BULLISH for trend in trends):
            self.trend = BULLISH
        elif all(trend == BEARISH for trend in trends):
            self.trend = BEARISH
        else:
            self.trend = None

        # profile.disable()
        # ps = pstats.Stats(profile)
        # ps.print_stats()
        # print('----------------------------------------------------------')

        return self.trend

    def validate_options(self):
        """
        Validates options provided. If the list of options provided does not contain all options, an error is raised.
        """
        if len(self.tradingOptions) == 0:  # Checking whether options exist.
            raise ValueError("No trading options provided.")

        for Superoption in self.tradingOptions:
            if type(Superoption) != Option:
                raise TypeError(f"'{option}' is not a valid option type.")

    # def initialize_plot_dict(self):
    #     """
    #     Initializes plot dictionary for the Moving Average class.
    #     """
    #     # TODO: Add support for colors in the actual program.
    #     for option in self.tradingOptions:
    #         initialName, finalName = option.get_pretty_option()
    #         self.plotDict[initialName] = [self.get_current_trader_price(), get_random_color()]
    #         self.plotDict[finalName] = [self.get_current_trader_price(), get_random_color()]