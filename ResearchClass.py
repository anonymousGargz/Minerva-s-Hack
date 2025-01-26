import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime 
import yfinance as yf

class PlotEvaluations:
  def __init__(self, trades_list, size = (10,10)):
    self.trades = trades_list 
    plt.rcParams['figure.figsize'] = size

  def PlotSummary(self, saveAs=None):
    plot1 = plt.subplot2grid((3, 3), (0, 0), colspan=3, rowspan=2)
    plot2 = plt.subplot2grid((3, 3), (2, 0), colspan=2, rowspan=1)
    plot3 = plt.subplot2grid((3, 3), (2, 2), colspan=2, rowspan=1)
    self.PlotReturns(plot_type=plot1)
    self.PlotReturnsDistribution(plot_type=plot2)
    self.PlotTimeDependance(plot_type=plot3)
    plt.tight_layout()
    if saveAs:
      plt.savefig(saveAs)
    else:
      plt.show()
    return
  
  def PlotReturnsDistribution(self, plot_type=plt):
    if plot_type==plt:
      plt.hist(100*self.trades['Return'], 50)
      plt.title("Distribution of % Returns across 50 Bins")
      plt.yscale('log')
    if plot_type!=plt:
      plot_type.hist(100*self.trades['Return'], 50)
      plot_type.set_title("Return % Distribution")
      plot_type.set_yscale('log')

  def PlotReturns(self, plot_type=plt):
    if plot_type==plt:
      plot_type.plot(100*(1+self.trades['Return']).reset_index()['Return'].cumprod()-100, label='Strategy')
      plot_type.title('% Returns')
    if plot_type!=plt:
      plot_type.plot(100*(1+self.trades['Return']).reset_index()['Return'].cumprod()-100, label='Strategy')
      plot_type.set_title('% Returns')
  
  def PlotTimeDependance(self, plot_type=plt):
    if plot_type==plt:
      bins = np.linspace(1,self.trades['TradeDuration'].max(), 40)
      plt.hist(self.trades['TradeDuration'], bins=bins, color='b', label="Total", alpha=0.5)
      plt.hist([self.trades[self.trades['Return']> 0 ]['TradeDuration'],
                self.trades[self.trades['Return']< 0 ]['TradeDuration']], bins=bins, color=['g','r'], label=['Profitable Trades', 'Loss Trades'])
      plt.yscale('log')
      plt.title("Log Frequency Distribution of Trade Times")
      plt.xlabel("Trade times in 2m Intervals (first bar is 2m, second if 2x2=4m, third is 3x2=6m...)")
      plt.ylabel("Log Frequency Density")
    if plot_type != plt:
      bins = np.linspace(1,self.trades['TradeDuration'].max(), 40)
      plot_type.hist(self.trades['TradeDuration'], bins=bins, color='b', label="Total", alpha=0.5)
      plot_type.hist([self.trades[self.trades['Return']> 0 ]['TradeDuration'],
                    self.trades[self.trades['Return']< 0 ]['TradeDuration']], bins=bins, color=['g','r'], label=['Profitable Trades', 'Loss Trades'])
      plot_type.set_yscale('log')
      plot_type.set_title("Log Frequency Distribution of Trade Times")
      plot_type.set_xlabel("Trade times ")
      plot_type.set_ylabel("Log Frequency Density")
  
class EvaluationMetrics():
    def __init__(self,trade_df, stocks, start_date, end_date):
        self.trade_df = trade_df
        if len(self.trade_df) == 0:
          print("ERROR: Empty Returns!")
        self.returns = self.trade_df['Return']
        self.stocks = stocks
        self.start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")

    def sharpe(self):
        try:
            return round(np.sqrt(60) * self.returns.mean() / self.returns.std(),3)
        except:
            return np.nan
        
    def sortino(self):
        try:
            return round(np.sqrt(60) * self.returns.mean() / self.returns[self.returns < 0].std(),3)
        except:
            return np.nan
        
    def tstat(self):
        t = np.sqrt(len(self.returns)) * self.returns.mean() / self.returns.std()
        return round(t,3)

    def win_rate(self):
        self.returns = self.returns.dropna()
        return round(100 * len(self.returns[self.returns > 0]) / self.returns.count(),2)

    def avg_trade(self):
        return round(self.returns.mean(),6)

    def print_results(self):
        string = f'''
        Assets:\t\t {([asset for asset in self.stocks])}
        Start date:\t {self.start_date}
        End date:\t {self.end_date}
        Frequency: \t {"2m"}
        ---------------------------
        trade_df:\t\t {len(self.trade_df)}
        Costs: \t\t ${len(self.trade_df) * 1.6 * 2}/month
        Sharpe:\t\t {self.sharpe()} 
        Sortino:\t {self.sortino()} 
        t-stat:\t\t {self.tstat()}
        Total return: \t {round(100*((1+self.trade_df['Return']).prod()),3)}%
        Win rate:\t {self.win_rate()}%
        Avg trade:\t {round(100 * self.trade_df['Return'].mean(),3)}%
        Avg win:\t {round(100 * self.trade_df[self.trade_df['Return'] > 0]['Return'].mean(),3)}% 
        Avg loss:\t {round(100 * self.trade_df[self.trade_df['Return'] <= 0]['Return'].mean(),3)}%
        Min trade size:\t ${int((len(self.trade_df) * 1.6 * 2) / self.trade_df['Return'].mean())}
        Avg trade time:\t {self.trade_df['TradeDuration'].mean()}
        Avg win time:\t {self.trade_df[self.trade_df['Return'] >= 0]['TradeDuration'].mean()}
        Avg loss time:\t {self.trade_df[self.trade_df['Return'] <= 0]['TradeDuration'].mean()}
        '''

        
        return print(string)

    def drawdowns(self):
        cum_ret = self.returns.cumsum()
        dds = list(cum_ret / cum_ret.cummax() - 1)

        local_dds = []
        low = 0

        for dd in dds:
            if (dd < low):
                low = dd            

            if (dd == 0) and (low != 0):
                local_dds.append(low)
                low = 0

        # drawdowns will be represented as positive percentages
        all_dds = (pd.Series(local_dds) * -100)

        return all_dds # call .mean(), .max(), .plot() 

    def costs(self, trade_costs):
        months = (self.end_date - self.start_date).days / (365/12)
        return int(trade_costs * self.trade_df['Return'].count() / months)

    def trade_durations(self, df):
        return round((df['ExitIndex'] - df['EntryIndex']).mean(),2)

class TradesBook():
  """
  Allows a 1-at-a-time trading system by filling in two halves of an array at buy and sell eg:
  
  BUY:
    Nth_row_of_trade_array = ([EntryPrice | Sizing | SL |           |               | EntryIndex |           | TP ])
  SELL:
    Nth_row_of_trade_array = ([EntryPrice | Sizing | SL | ExitPrice | TradeDuration | EntryIndex | ExitIndex | TP])

  Inputs:
    data = price dataset which allows us to start with an array (of nan's) with same length of data (trade count wont exceed number of datapoints)
  
  Functions:
    OpenTrade & CloseTrade = Updates the TradeBook with input data
    PositionOpen = Boolean In/NotIn trade
    CurrentSizing = If PositionOpen, return current size of trade
    ActiveStopLossPrice & ActiveTakeProfitPrice = Return open order execution prices
    ActiveOrderExecutionPrice = Return price of price execution if open order executed this time period
    ReturnTradeBook = dataframe of TradesBook
    GetOpenOrderData = returns data about current open order.
  """
  def __init__(self, data):
    self.OrderBook = np.zeros(shape=(len(data), 9))
    self.OrderBook[:] = np.nan
    self.trade_count = 0
    self.PositionSize = 0

  def OpenTrade(self, EntryPrice, Sizing, StopLossPrice, EntryIndex, TargetPrice):
    self.OrderBook[self.trade_count, 0] = EntryPrice
    self.OrderBook[self.trade_count, 1] = Sizing
    self.OrderBook[self.trade_count, 2] = StopLossPrice
    self.OrderBook[self.trade_count, 5] = EntryIndex
    self.OrderBook[self.trade_count, 8] = TargetPrice
    self.PositionSize = Sizing

  def CloseTrade(self, ExitPrice, ExitIndex):
    self.OrderBook[self.trade_count, 3] = ExitPrice
    self.OrderBook[self.trade_count, 4] = ExitIndex - self.OrderBook[self.trade_count, 5]
    self.OrderBook[self.trade_count, 6] = ExitIndex
    self.OrderBook[self.trade_count, 7] = self.OrderBook[self.trade_count, 1]*((self.OrderBook[self.trade_count, 3]-self.OrderBook[self.trade_count, 0])/self.OrderBook[self.trade_count, 0])
    self.trade_count += 1
    self.PositionSize = 0
  
  def PositionOpen(self):
    """
    Boolean test for EntryPrice is NOT nan AND ExitPrice IS an. ie, do we have a trade open?
    """
    if ~np.isnan(self.OrderBook[self.trade_count, 0]) and np.isnan(self.OrderBook[self.trade_count, 3]):
      return True
    else: return False

  def CurrentSizing(self):
    """
    If we're in a trade, what is the size of the position (size of open trade)
    """
    if self.PositionOpen(): return self.OrderBook[self.trade_count, 1]
    else: return 0

  def ActiveStopLossPrice(self):
    return self.OrderBook[self.trade_count, 2]
  
  def ActiveTakeProfitPrice(self):
    return self.OrderBook[self.trade_count, 8]
  
  def ActiveOrderExecutionPrice(self, row):
    """
    Test if the last open SL/TP has been executed this time period by looping through them and comparing Low > Price < High.
    """
    prices = [self.ActiveStopLossPrice(), self.ActiveTakeProfitPrice()]
    for price in prices:
      if price < row['High'] and price > row['Low']: #Did this price fill in this candle?
        return price
    else: return False

  def ReturnTradeBook(self):
    cols = ['EntryPrice', 'Sizing', 'StopLossPrice', 'ExitPrice', 'TradeDuration', 'EntryIndex', 'ExitIndex', 'Return', 'TargetPrice']
    return pd.DataFrame(self.OrderBook, columns=cols).dropna() 

  def GetOpenOrderData(self):
    if self.PositionOpen(): return self.OrderBook[self.trade_count, 0], self.OrderBook[self.trade_count, 1], self.OrderBook[self.trade_count, 2], self.OrderBook[self.trade_count, 5], self.OrderBook[self.trade_count, 8]

class StrategyTemplate():
  """
  Class allows you to implement your own strategy and test it, minimising the code you need to write!

  Input
    ticker_list = list of assets to loop through. Gets from yfinance
    start_date, end_date = "2022-11-12" start muct be < 90days ago for sub-day times.
    interval = "2m", "5m" candle size.
    indicator_parameters = list of indicator parameters eg [10,20,10]

  Functions:
    GetData = Gets data, ensures progress bar for download is removed, as it gets teh output very messy for > 10 downloads
    AddIndicators = Add your own indicators to the dataset.
    ApplyStrategyThroughTickers = Loop through tickers, calling ApplyStrategyThroughTime at each stock
                                  and add the output TradeBook to the global TradeBook.
    ApplyStrategyThroughTime = Loops through teh rows of the datafile, applying strategyLogic at each timestep. 
                                  It calls TradesBook (class above) for each stock and gets the TradeBook for the stock.  
  """
  def __init__(self, ticker_list, start_date, end_date, interval, indicator_parameters=[]):
    self.ticker_list = ticker_list
    self.interval = interval
    self.indicator_parameters = indicator_parameters
    self.start_date = start_date
    self.end_date = end_date
    self.useful_variables = [] #Allows us to store values between timesteps, things like 'close 2 periods ago, or size of last close'

  def SetUsefulDataStore(self, value_to_add): #Append a value to the datastore
    self.useful_variables.append(value_to_add)

  def GetUsefulDataStore(self):
    if len(self.useful_variables) > 0:
      return self.useful_variables
    else: return None
    
  def GetData(self, ticker):
    # return yf.download(ticker, self.start_date, self.end_date, interval=self.interval, progress=False).reset_index()  #Needs to be integer index for our 'data.iterrows' loop. 
    return pd.read_parquet(f'{ticker}')
  

  def ApplyStrategyThroughTickers(self):
    TRADE_BOOK = pd.DataFrame()  # Global TradeBook of all stocks
    for ticker in self.ticker_list:
        self.data = self.GetData(ticker)
        print(f"Processing {ticker} - Columns: {self.data.columns}")
        if 'Return' not in self.data.columns:
            print(f"'Return' is missing for {ticker}!")
        self.AddIndicators()
        ticker_specific_tradebook = self.ApplyStrategyThroughTime(ticker)
        TRADE_BOOK = pd.concat([TRADE_BOOK, ticker_specific_tradebook])  # Add ticker's data to global TRADE_BOOK
    return TRADE_BOOK
  
  def ApplyStrategyThroughTime(self, ticker):
    TradeBook = TradesBook(self.data) #Call TradesBook Object allows us to do the 'Trading Simulation' stuff in that class (see above)
    for idx, row in self.data.iterrows():
      if idx == 0: continue #Allows for index-1 operations
      self.strategyLogic(TradeBook, row, idx) 
    ticker_specific_tradebook = TradeBook.ReturnTradeBook()
    ticker_specific_tradebook['TICKER'] = ticker #Allows us to tie trades to stocks in the global 
    return ticker_specific_tradebook

  def strategyLogic(self, TradeBook, row, idx):
    """
    Example for VolatilitySqueeze:
    When not in trade, if Bollinger Bands are outside Keltner Channels, trade in teh direction of the +- 100 momentum.
    When in trade, exit when youve been in trade for 8 periods, or sign of momentum switches.
      if TradeBook.CurrentSizing() == 0:
        enter_when = (row['UPPERBollengerSize'] > row['UPPERKeltnerSize'] and self.data['UPPERBollengerSize'][idx-1] > self.data['UPPERKeltnerSize'][idx-1])
        if enter_when:
          if row['Momentum'] > 100:#Long
            TradeBook.OpenTrade(row['Adj Close'], 1, np.sign(row['DMom']), idx, 0)
          if row['Momentum'] < 100:#Short
            TradeBook.OpenTrade(row['Adj Close'], -1, np.sign(row['DMom']), idx, 0)

      if TradeBook.CurrentSizing() != 0:
        exit_when = np.sign(row['DMom']) != TradeBook.GetOpenOrderData()[2] or (idx - TradeBook.GetOpenOrderData()[3]) > 7 #CUTOFF trade after 7 periods as profitability fell
        if exit_when: #exit
          TradeBook.CloseTrade(row['Adj Close'], idx)
    """
    pass  #Implement your own!
    
  
  def AddIndicators(self):
    """
    Add indicator values to the dataset you have, from your list of indicator values. For example:
    EMA_PARAM = self.indicator_parameters[0]
    self.data['UPPERKeltnerSize'] = self.data['Close'].ewm(span=EMA_PARAM, adjust=False, min_periods=EMA_PARAM).mean() + 2* Calc_ATR_SL(self.data, ATR_PARAM)
    """
    pass  #Implement your own!
