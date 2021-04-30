该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/11115

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

# 克隆自聚宽文章：https://www.joinquant.com/post/10246
# 标题：【量化课堂】RSRS(阻力支撑相对强度)择时策略（上）
# 作者：JoinQuant量化课堂

# 导入函数库
import jqdata
from jqdata import *
import pandas as pd
from pandas import Series, DataFrame
import numpy as np
import matplotlib
from pandas.stats.api import ols
import datetime
import time


# 初始化函数，设定基准等等
def initialize(context):
    # 设定上证指数作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 输出内容到日志 log.info()
    log.info('初始函数开始运行且全局只运行一次')
    # 过滤掉order系列API产生的比error级别低的log
    # log.set_level('order', 'error')
    
    ### 股票相关设定 ###
    # 股票类每笔交易时的手续费是：买入时佣金万分之三，卖出时佣金万分之三加千分之一印花税, 每笔交易佣金最低扣5块钱
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    
    ## 运行函数（reference_security为运行时间的参考标的；传入的标的只做种类区分，因此传入'000300.XSHG'或'510300.XSHG'是一样的）
      # 开盘前运行
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG') 
      # 开盘时运行
    run_daily(market_open, time='open', reference_security='000300.XSHG')
      # 收盘后运行
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')

    # 设置RSRS指标中N, M的值
    g.N = 18
    g.M = 480
    
    # 要操作的股票：平安银行（g.为全局变量）
    g.security = '000300.XSHG'
    
    # 买入阈值
    g.buy = 0.7
    g.sell = -0.7
    
    
    # 计算出所有需要的RSRS斜率指标
    # 计算交易日期区间长度(包括开始前一天)
    g.trade_date_range = len(get_trade_days(start_date = context.run_params.start_date, end_date = context.run_params.end_date)) + 1
    # 取出交易日期时间序列(包括开始前一天)
    g.trade_date_series = get_trade_days(end_date = context.run_params.end_date, count = g.trade_date_range)
    # 计算RSRS斜率的时间区间长度
    g.date_range = len(get_trade_days(start_date = context.run_params.start_date, end_date = context.run_params.end_date)) + g.M
    # 取出计算RSRS斜率的时间序列
    g.date_series = get_trade_days(end_date = context.run_params.end_date, count = g.date_range)
    # 建立RSRS斜率空表
    g.RSRS_ratio_list = Series(np.zeros(len(g.date_series)), index = g.date_series)
    # 填入各个日期的RSRS斜率值
    for i in g.date_series:
        g.RSRS_ratio_list[i] = RSRS_ratio(g.N, i)
        
        
    
    # 计算标准化的RSRS指标
    # 计算均值序列
    g.trade_mean_series =  pd.rolling_mean(g.RSRS_ratio_list, g.M)[-g.trade_date_range:]
    # 计算标准差序列
    g.trade_std_series = pd.rolling_std(g.RSRS_ratio_list, g.M)[-g.trade_date_range:]
    # 计算标准化RSRS指标序列
    g.RSRS_stdratio_list = Series(np.zeros(len(g.trade_date_series)), index = g.trade_date_series)
    g.RSRS_stdratio_list = (g.RSRS_ratio_list[-g.trade_date_range:] - g.trade_mean_series) /  g.trade_std_series
    #print g.RSRS_stdratio_list
        
    
  
# 附: RSRS斜率指标定义
def RSRS_ratio(N, date):
    security = g.security
    stock_price_high = get_price(security, end_date = date, count = N)['high']
    stock_price_low = get_price(security, end_date = date, count = N)['low']
    ols_reg = ols(y = stock_price_high, x = stock_price_low)
    return ols_reg.beta.x
    
    
    
    
## 开盘前运行函数     
def before_market_open(context):
    # 输出运行时间
    log.info('函数运行时间(before_market_open)：'+str(context.current_dt.time()))

    # 给微信发送消息（添加模拟交易，并绑定微信生效）
    send_message('美好的一天~')


    

    
## 开盘时运行函数
def market_open(context):
    log.info('函数运行时间(market_open):'+str(context.current_dt.time()))
    security = g.security
    # 取得当前的现金
    cash = context.portfolio.available_cash

    # 如果上一时间点的RSRS斜率大于买入阈值, 则全仓买入
    if g.RSRS_stdratio_list[context.previous_date] > g.buy:
        # 记录这次买入
        log.info("标准化RSRS斜率大于买入阈值, 买入 %s" % (security))
        # 用所有 cash 买入股票
        order_value(security, cash)
    # 如果上一时间点的RSRS斜率小于卖出阈值, 则空仓卖出
    elif g.RSRS_stdratio_list[context.previous_date] < g.sell and context.portfolio.positions[security].closeable_amount > 0:
        # 记录这次卖出
        log.info("标准化RSRS斜率小于卖出阈值, 卖出 %s" % (security))
        # 卖出所有股票,使这只股票的最终持有量为0
        order_target(security, 0)
 
## 收盘后运行函数  
def after_market_close(context):
    log.info(str('函数运行时间(after_market_close):'+str(context.current_dt.time())))
    #得到当天所有成交记录
    trades = get_trades()
    for _trade in trades.values():
        log.info('成交记录：'+str(_trade))
    log.info('一天结束')
    log.info('##############################################################')
