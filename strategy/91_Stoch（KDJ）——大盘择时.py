该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/11103

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

#发布自聚宽社区

import talib
import pandas as pd
import numpy as np
import math
from sklearn.svm import SVR  
from sklearn.model_selection import GridSearchCV  
from sklearn.model_selection import learning_curve


def initialize(context):
    # 股票类每笔交易时的手续费是：买入时佣金万分之三，卖出时佣金万分之三加千分之一印花税, 每笔交易佣金最低扣5块钱
    set_order_cost(OrderCost(close_tax=0.000, open_commission=0.0000, close_commission=0.0000, min_commission=0), type='stock')
    # 设定滑点为固定值
    set_slippage(FixedSlippage(0.00))
    
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
        slowk, slowd = talib.STOCH(h['high'].values,h['low'].values,h['close'].values,
                                            fastk_period=17,slowk_period=9,
                                            slowk_matype=0,slowd_period=7,slowd_matype=0)
        # 获得最近的kd值
        
        print(slowk)
        # print(slowk[-6:-1])
        # MA_stoch_5 = slowk[-5:].mean()
        
        # print(MA_stoch_5)
        # MA_stoch_now=slowk[-1]
        # 获取当前股票的数据
        current_position = context.portfolio.positions[stock].amount
        # 获取当前股票价格
        current_price = data[stock].price
        # 当slowk > 90 or slowd > 90，且拥有的股票数量>=0时，卖出所有股票
        if (slowk[-1] < 80 and slowk[-2] > 80 and current_position >= 0) or (slowk[-1] > 20 and slowk[-1] < 80 and slowk[-1] < slowd[-1] and current_position >= 0):
            order_target(stock, 0)
        # 当slowk < 10 or slowd < 10, 且拥有的股票数量<=0时，则全仓买入
        elif (slowk[-1] > 20 and slowk[-2] < 20 and current_position <= 0) or (slowk[-1] > 20 and slowk[-1] > 80 and slowk[-1] > slowd[-1] and current_position <= 0):
            # 买入股票
            order_value(stock, cash)
            # 记录这次买入
            log.info("Buying %s" % (stock))
