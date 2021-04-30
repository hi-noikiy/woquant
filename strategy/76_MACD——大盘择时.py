该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/11102

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

#发布自聚宽

import talib
import pandas as pd
import numpy as np
import math
from sklearn.model_selection import learning_curve

import talib
#import numpy as np
#import pandas as pd

def initialize(context):
    # # 股票类每笔交易时的手续费是：买入时佣金万分之三，卖出时佣金万分之三加千分之一印花税, 每笔交易佣金最低扣5块钱
    # set_order_cost(OrderCost(close_tax=0.000, open_commission=0.0000, close_commission=0.0000, min_commission=0), type='stock')
    # # 设定滑点为固定值
    # set_slippage(FixedSlippage(0.00))
    # 定义一个全局变量, 保存要操作的证券                                                                                           
    context.stocks = ['399300.XSHE']
    # 设置我们要操作的股票池
    set_universe(context.stocks)

# 初始化此策略
def handle_data(context, data):
    # 取得当前的现金
    cash = context.portfolio.cash
    # 循环股票列表
    for stock in context.stocks:
        # 获取股票的数据
        h = attribute_history(stock, 60, '1d', ('high','low','close'))
        # 创建STOCH买卖信号，包括最高价，最低价，收盘价和快速线（一般取为9），慢速线
        # 注意：STOCH函数使用的price必须是narray
        macd, macdsignal, macdhist = talib.MACD(h['close'].values, fastperiod=9, slowperiod=24, signalperiod=9)
        # 获得最近的kd值
        print(macdsignal)
        # 获取当前股票的数据
        current_position = context.portfolio.positions[stock].amount
        # 获取当前股票价格
        current_price = data[stock].price
        # 当slowk > 90 or slowd > 90，且拥有的股票数量>=0时，卖出所有股票
        if macd[-1] < 0 and current_position >= 0:
            order_target(stock, 0)
        # 当slowk < 10 or slowd < 10, 且拥有的股票数量<=0时，则全仓买入
        elif macd[-1] > 0 and current_position <= 0:
            # 买入股票
            order_value(stock, cash)
            # 记录这次买入
            log.info("Buying %s" % (stock))