from __future__ import (absolute_import, division, print_function, unicode_literals)
import datetime # for datetime objects
import backtrader as bt # backtracder platform
import backtrader.analyzers as btanalyzers
import os.path # to manage paths
import sys # to find out the script name (in argv[0])
import matplotlib
from matplotlib.dates import (HOURS_PER_DAY, MIN_PER_HOUR, SEC_PER_MIN, MONTHS_PER_YEAR, DAYS_PER_WEEK, SEC_PER_HOUR, SEC_PER_DAY, num2date, rrulewrapper, YearLocator, MicrosecondLocator)

# Strategy: If the price has been falling 3 sessions in a row … BUY BUY BUY!!!
# adjustable parameters: symbol, size, side = long, target profit, max loss
# EXIT if target profit is met, or if max loss is met

# Creates Strategy
class StrategySma(bt.Strategy):
    params = (
        ('maperiod', 15),
    )

    def log(self, txt, dt=None):
        '''Logging Function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.dataclose = self.datas[0].close # Keep a reference to the 'close' line in the data[0] dataseries

        self.order = None # to keep track of pending orders and buy price/commission
        self.buyPrice = None
        self.buyComm = None

        self.sma = bt.indicators.MovingAverageSimple( # add a MovingAverageCimple indicator
            self.datas[0], period=self.params.maperiod
        )

        # Indicators for the plotting show
        bt.indicators.ExponentialMovingAverage(self.datas[0], period = 25)
        bt.indicators.WeightedMovingAverage(self.datas[0], period = 25, subplot = True)
        bt.indicators.Stochastic(self.datas[0])
        bt.indicators.MACDHisto(self.datas[0])
        rsi = bt.indicators.RSI(self.datas[0])
        bt.indicators.SmoothedMovingAverage(rsi, period = 10)
        bt.indicators.ATR(self.datas[0], plot=False)

    def notifyOrder(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return # buy/sell order submitted/accepted to/by broker -- Nothing to do

        # Check if an order has been compoleted
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, Price: %.2F, Cost: %.2f, Comm: %.2f' %
                (order.executed.price,
                order.executed.value,
                order.executed.comm))

                self.buyPrice = order.executed.price
                self.buyComm = order.executed.comm

            else: # SELL
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm: %.2f' % 
                (order.executed.price,
                order.executed.value,
                order.executed.comm))
            
            self.bar_executed = len(self)
        
        elif order.status in [order.Cancelled, order.Margin, order.Rejected]:
            self.log('Order Cancelled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notifyTrade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS: %.2f, NET: %.2f' %
            (trade.pnl, trade.pnlcomm))


    def next(self):
        self.log('Close, %.2f' % self.dataclose[0]) # Simply log the closing price of the series from the reference

        if self.order: # Check if an order is pending... if yes, we cannot send a 2nd one
            return
        
        if not self.position: # Check if we are in the market
            
            if self.dataclose[0] > self.sma[0]: # Not yet... we MIGHT BUY if....
                # current close greater than sma

                    self.log('BUY CREATE, %.2f' % self.dataclose[0]) # BUY BUY BUY (with default parameters)

                    self.order = self.buy() # Keep track of the created order to avoid a 2nd order
        
        else:
            # already in the market, we might sell
            if self.dataclose[0] < self.sma[0]:

                self.log('SELL CREATE, %.2f' % self.dataclose[0]) # SELL SELL SELL (with all possible default parameters)

                self.order = self.sell() # keep track of the created order to avoid a 2nd order


if __name__ == '__main__':
    cerebro = bt.Cerebro() # creates Cerebro entity

    cerebro.addstrategy(StrategySma) # add a strategy

    modpath = os.path.dirname(os.path.abspath(sys.argv[0])) # finds where the script is
    datapath = os.path.join(modpath, 'C:\\Users\\casan\\venv_caspianquant\\caspianquant\\XRP-USD 11.18.17-11.18.22.csv')

    # Create a Data Feed
    data = bt.feeds.YahooFinanceCSVData(
        dataname = datapath,
        fromdate = datetime.date(2017, 11, 17), # do not pass values before this date
        todate = datetime.date(2020, 11, 18), # do not pass value after this date
        reverse = False
    )

    cerebro.adddata(data) # add the Data Feed to Cerebro

    cerebro.broker.setcash(1000.0) # set desired cash start
    print('Starting Portgolio Value: %.2f' % cerebro.broker.getvalue()) # print out starting conditions

    cerebro.addsizer(bt.sizers.FixedSize, stake=10)

    cerebro.addanalyzer(btanalyzers.SharpeRatio, _name = 'sharpe') # How to get the Sharpe Analyzer
    cerebro.addanalyzer(btanalyzers.Transactions, _name = 'tx') # The Transactions Analyzer
    cerebro.addanalyzer(btanalyzers.TradeAnalyzer, _name = 'trades') # The Trade Analyzer

    cerebro.broker.setcommission(commission=0.00) # set the commission = 0.1%.... devide by 100 to remove the %

    cerebro.run() # run over everything

    print('Final Portfolio Value: % .2f' % cerebro.broker.getvalue()) # print out final result

    back = cerebro.run()
    endValue = cerebro.broker.getvalue()
    sharpe = back[0].analyzers.sharpe.get_analysis()

    print(f'Sharpe Ratio is {sharpe}')

    cerebro.plot()
