import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.pyplot import Figure as fig
from pylab import rcParams
import datetime
from datetime import timedelta
import statsmodels.api as sm
rcParams['figure.figsize'] = 20,10
from ResearchClass import PlotEvaluations, EvaluationMetrics, TradesBook, StrategyTemplate
import os

pd.options.mode.chained_assignment = None  # default='warn'
class BollingerBandsStrategy(StrategyTemplate):
    """
    Bollinger Bands strategy class that inherits from StrategyTemplate.
    This strategy generates buy and sell signals based on Bollinger Bands.
    """

    def AddIndicators(self):
        """
        Adds Bollinger Bands indicators to the data.
        Bollinger Bands consist of a middle SMA band, upper band, and lower band.
        """
        LOOKBACK_PERIOD = self.indicator_parameters[0]  # Bollinger Bands lookback period
        STD_DEV_MULTIPLIER = self.indicator_parameters[1]  # Standard deviation multiplier

        # Calculate Bollinger Bands
        self.data['BB_MIDDLE'] = self.data['Close'].rolling(LOOKBACK_PERIOD).mean()
        self.data['BB_STD'] = self.data['Close'].rolling(LOOKBACK_PERIOD).std()
        self.data['BB_UPPER'] = self.data['BB_MIDDLE'] + (STD_DEV_MULTIPLIER * self.data['BB_STD'])
        self.data['BB_LOWER'] = self.data['BB_MIDDLE'] - (STD_DEV_MULTIPLIER * self.data['BB_STD'])

    def strategyLogic(self, TradeBook, row, idx):
        """
        Defines the Bollinger Bands strategy logic.

        Parameters:
        - TradeBook: The TradeBook object that manages trades.
        - row: The current row of data.
        - idx: The current index in the data.
        """
        # Skip the initial periods to allow for indicator warmup
        if idx < self.indicator_parameters[0]:
            return

        # Close trade if an active order execution price is met
        if TradeBook.CurrentSizing() != 0 and TradeBook.ActiveOrderExecutionPrice(row):
            TradeBook.CloseTrade(TradeBook.ActiveOrderExecutionPrice(row), idx)

        # Open a long trade if price crosses above the lower Bollinger Band
        if TradeBook.CurrentSizing() == 0 and row['Close'] < row['BB_LOWER']:
            entry = row['Open']
            stop = row['Open'] * (1 - self.indicator_parameters[2])  # Stop-loss as a percentage of entry
            target = row['BB_MIDDLE']  # Target set to middle band
            TradeBook.OpenTrade(entry, 1, stop, idx, target)

        # Open a short trade if price crosses below the upper Bollinger Band
        if TradeBook.CurrentSizing() == 0 and row['Close'] > row['BB_UPPER']:
            entry = row['Open']
            stop = row['Open'] * (1 + self.indicator_parameters[2])  # Stop-loss as a percentage of entry
            target = row['BB_MIDDLE']  # Target set to middle band
            TradeBook.OpenTrade(entry, -1, stop, idx, target)
    # Parameters: [lookback period, std deviation multiplier, stop loss percentage]
parameters = [20, 2, 0.015]
ticker_list = ['data/MNQc1.parquet']
today = datetime.datetime.now()
start_date = str((today - datetime.timedelta(days=59)).strftime("%Y-%m-%d"))
end_date = str(today.strftime("%Y-%m-%d"))
interval = "2m"



# Apply the Bollinger Bands strategy
BB_TRADE_BOOK = BollingerBandsStrategy(ticker_list, start_date, end_date, interval, parameters).ApplyStrategyThroughTickers()

# Evaluate the strategy performance
bb_metrics = EvaluationMetrics(BB_TRADE_BOOK, ticker_list, start_date, end_date)
bb_plots = PlotEvaluations(BB_TRADE_BOOK, (10, 7))

# Print the evaluation metrics and plot the summary
bb_metrics.print_results()
bb_plots.PlotSummary()


