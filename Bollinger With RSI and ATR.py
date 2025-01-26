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
import plotly.graph_objects as go

pd.options.mode.chained_assignment = None  # default='warn'

class AMCrossover(StrategyTemplate):
    """
    Further refined AMCrossover strategy with RSI, Bollinger Bands, and ATR-based risk management.
    """

    def AddIndicators(self):
        """
        Adds indicators, including SMA, Bollinger Bands, RSI, and ATR.
        """
        SHORT_LOOKBACK_PERIOD = self.indicator_parameters[0]
        LONG_LOOKBACK_PERIOD = self.indicator_parameters[1]
        BB_PERIOD = self.indicator_parameters[3]
        BB_MULTIPLIER = self.indicator_parameters[4]
        ATR_PERIOD = self.indicator_parameters[5]


        # Simple Moving Averages
        self.data['SMA_SHORT'] = self.data['Close'].rolling(SHORT_LOOKBACK_PERIOD).mean()
        self.data['SMA_LONG'] = self.data['Close'].rolling(LONG_LOOKBACK_PERIOD).mean()

        # Bollinger Bands
        self.data['BB_MB'] = self.data['Close'].rolling(BB_PERIOD).mean()
        self.data['BB_SD'] = self.data['Close'].rolling(BB_PERIOD).std()
        self.data['BB_UB'] = self.data['BB_MB'] + BB_MULTIPLIER * self.data['BB_SD']
        self.data['BB_LB'] = self.data['BB_MB'] - BB_MULTIPLIER * self.data['BB_SD']

        # RSI (Relative Strength Index) - 10-period Tells us if the stock is overbought or oversold
        self.data['RSI'] = self.data['Close'].diff().apply(
            lambda x: max(x, 0)
        ).rolling(10).mean() / abs(self.data['Close'].diff()).rolling(10).mean() * 100

        # ATR (Average True Range) - 14-period Tells us the volatility of the stock
        self.data['ATR'] = self.data['High'].combine(
            self.data['Low'], max
        ).combine(self.data['Close'].shift(), max).combine(
            self.data['Close'].shift(), lambda x, y: abs(x - y)
        ).rolling(ATR_PERIOD).mean()

    def strategyLogic(self, TradeBook, row, idx):
        """
        Updated strategy logic with ATR-based risk management and improved filters.
        """
        if idx < max(self.indicator_parameters[1], self.indicator_parameters[3], self.indicator_parameters[5]):
            return

        # Close trade if an active order execution price is met
        if TradeBook.CurrentSizing() != 0 and TradeBook.ActiveOrderExecutionPrice(row):
            TradeBook.CloseTrade(TradeBook.ActiveOrderExecutionPrice(row), idx)

        # Long Signal: SMA crossover + RSI filter + Bollinger Bands
        if (TradeBook.CurrentSizing() == 0 and
            row['Close'] > self.data['BB_LB'][idx] and
            self.data['SMA_SHORT'][idx] > self.data['SMA_LONG'][idx] and
            40 < self.data['RSI'][idx] < 60):

            entry = row['Open']
            stop = entry - self.data['ATR'][idx]  # ATR-based stop-loss
            target = entry + 2 * self.data['ATR'][idx]  # Risk-reward ratio of 2:1
            TradeBook.OpenTrade(entry, 1, stop, idx, target)

        # Short Signal: SMA crossover + RSI filter + Bollinger Bands
        if (TradeBook.CurrentSizing() == 0 and
            row['Close'] < self.data['BB_UB'][idx] and
            self.data['SMA_SHORT'][idx] < self.data['SMA_LONG'][idx] and
            40 < self.data['RSI'][idx] < 60):

            entry = row['Open']
            stop = entry + self.data['ATR'][idx]
            target = entry - 2 * self.data['ATR'][idx]
            TradeBook.OpenTrade(entry, -1, stop, idx, target)

# Parameters: [short lookback period, long lookback period, stop loss percentage]
parameters = [5, 50, 0.01, 20, 2, 14]  # Add ATR period (14)
ticker_list = ['data/MNQc1.parquet']
today = datetime.datetime.now()
start_date = str((today - datetime.timedelta(days=59)).strftime("%Y-%m-%d"))
end_date = str(today.strftime("%Y-%m-%d"))
interval = "2m"           


AMCROSSOVER_TRADE_BOOK = AMCrossover(ticker_list, start_date, end_date, interval, parameters).ApplyStrategyThroughTickers()

# Evaluate strategy
metrics = EvaluationMetrics(AMCROSSOVER_TRADE_BOOK, ticker_list, start_date, end_date)
plots = PlotEvaluations(AMCROSSOVER_TRADE_BOOK, (10, 7))

metrics.print_results()
plots.PlotSummary()
