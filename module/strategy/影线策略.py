# @Time : 2021/1/26 14:54
# @Author : LiuBin
# @File : 连板策略.py
# @Description : 
# @Software: PyCharm
from ..strategy import StrategyBag
import datetime
import pandas as pd
from jqdata import *


# 初始化函数，设定基准等等
def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('002475.XSHE')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 禁用未来函数
    # set_option("avoid_future_data", True)
    # 最大持仓股票数量
    g.max_hold = 1
    g.security = '002475.XSHE'
    # 过滤掉order系列API产生的比error级别低的log
    log.set_level('order', 'info')
    # 输出内容到日志 log.info()
    log.info('初始函数开始运行且全局只运行一次')

    ### 股票交易相关设定 ###
    # 股票类每笔交易时的手续费是：买入时佣金万分之三，卖出时佣金万分之三加千分之一印花税, 每笔交易佣金最低扣5块钱
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.00015, close_commission=0.00015, min_commission=5),
                   type='stock')

    ## 运行函数（reference_security为运行时间的参考标的；传入的标的只做种类区分，因此传入'000300.XSHG'或'510300.XSHG'是一样的）
    # 开盘时运行
    # run_daily(before_market_open, time='before_open', reference_security='000300.XSHG')
    run_daily(market_open, time='every_bar', reference_security='000300.XSHG')

## 开盘时运行函数
def market_open(context):
    ts = context.current_dt.time()
    if ts.hour == 9 and ts.minute <=45:
       return
    log.info('函数运行时间(market_open):' + str(ts))
    flag = StrategyBag.is_cross_shadow_line(g.security,unit='15m',context=context)
    if flag > 0:
        # 执行买入函数
        StrategyBag.buy(context, [g.security], g.max_hold)
    elif flag < 0:
        StrategyBag.sell(context, [g.security])
