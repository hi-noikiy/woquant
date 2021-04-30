该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/11713

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

import pandas as pd
import datetime
import numpy as np
import math
import time
import jqdata
from pandas import Series, DataFrame
import statsmodels.api as sm
import scipy.stats as scs
import matplotlib.pyplot as plt
#from pandas import Series, DataFrame

#总体回测前要做的事情
def initialize(context):
    set_params()        #1设置策参数
    set_variables() #2设置中间变量
    set_backtest()   #3设置回测条件

#1
#设置策参数
def set_params():
    g.tc=15  # 调仓频率
    g.yb=63  # 样本长度
    g.N=20   # 持仓数目
    
    #ARL=total_liability/total_assetsARL=total_liability/total_assets
    #g.factors=["market_cap","roe","pe_ratio","eps"] # 选出来的可用因子
    #g.factors=["market_cap","roe","pe_ratio","ps_ratio"] # 用户选出来的因子
    #g.factors=["circulating_market_cap","eps","net_profit_to_total_revenue","roe","pcf_ratio","ps_ratio","pe_ratio","turnover_ratio"] # 用户选出来的因子
    g.factors=["circulating_market_cap","ps_ratio","eps","net_profit_to_total_revenue","roe","pcf_ratio","pe_ratio","turnover_ratio"] # 用户选出来的因子
    # 因子等权重里1表示因子值越小越好，-1表示因子值越大越好
    g.weights=[[-1],[1],[-1],[-1],[-1],[-1],[1],[1]]
#2
#设置中间变量
def set_variables():
    g.t=0              #记录回测运行的天数
    g.if_trade=False   #当天是否交易

#3
#设置回测条件
def set_backtest():
    set_option('use_real_price', True)#用真实价格交易
    log.set_level('order', 'error')

'''
================================================================================
每天开盘前
================================================================================
'''

#每天开盘前要做的事情
def before_trading_start(context):
    if g.t%g.tc==0:
        #每g.tc天，交易一次性
        g.if_trade=True 
        # 设置手续费与手续费
        set_slip_fee(context) 
        # 设置可行股票池：获得当前开盘的沪深300股票池并剔除当前或者计算样本期间停牌的股票
        g.all_stocks = set_feasible_stocks(get_index_stocks('000300.XSHG'),g.yb,context)
        # 查询所有财务因子
        #运行时会报error，说g.q不能序列化，于是把它后置了
        #g.q = query(valuation,balance,cash_flow,income,indicator).filter(valuation.code.in_(g.all_stocks))
    g.t+=1

#4
# 设置可行股票池
# 过滤掉当日停牌的股票,且筛选出前days天未停牌股票
# 输入：stock_list为list类型,样本天数days为int类型，context（见API）
# 输出：list
def set_feasible_stocks(stock_list,days,context):
    # 得到是否停牌信息的dataframe，停牌的1，未停牌得0
    suspened_info_df = get_price(list(stock_list), start_date=context.current_dt, end_date=context.current_dt, frequency='daily', fields='paused')['paused'].T
    # 过滤停牌股票 返回dataframe
    unsuspened_index = suspened_info_df.iloc[:,0]<1
    # 得到当日未停牌股票的代码list:
    unsuspened_stocks = suspened_info_df[unsuspened_index].index
    # 进一步，筛选出前days天未曾停牌的股票list:
    feasible_stocks=[]
    current_data=get_current_data()
    #获取指定天数内是否有停牌，和为0则没有停牌
    for stock in unsuspened_stocks:
        if sum(attribute_history(stock, days, unit='1d',fields=('paused'),skip_paused=False))[0]==0:
            feasible_stocks.append(stock)
    return feasible_stocks
    
#5
# 根据不同的时间段设置滑点与手续费
def set_slip_fee(context):
    # 将滑点设置为0
    set_slippage(FixedSlippage(0)) 
    # 根据不同的时间段设置手续费
    dt=context.current_dt
    log.info(type(context.current_dt))
    
    if dt>datetime.datetime(2013,1, 1):
        set_commission(PerTrade(buy_cost=0.0003, sell_cost=0.0013, min_cost=5)) 
        
    elif dt>datetime.datetime(2011,1, 1):
        set_commission(PerTrade(buy_cost=0.001, sell_cost=0.002, min_cost=5))
            
    elif dt>datetime.datetime(2009,1, 1):
        set_commission(PerTrade(buy_cost=0.002, sell_cost=0.003, min_cost=5))
                
    else:
        set_commission(PerTrade(buy_cost=0.003, sell_cost=0.004, min_cost=5))

'''
================================================================================
每天交易时
================================================================================
'''
def handle_data(context, data):
    if g.if_trade==True:
    # 计算现在的总资产，以分配资金，这里是等额权重分配
        g.everyStock=context.portfolio.portfolio_value/g.N
        # 获得因子排序，返回一个dataframe,有股票代码、有得分、有因子值
        df_caiwu=getRankedFactors(g.factors,g.all_stocks)
        toBuy=df_caiwu.index[0:g.N]
        # 对于不需要持仓的股票，全仓卖出
        order_stock_sell(context,toBuy)
        # 对于不需要持仓的股票，按分配到的份额买入
        order_stock_buy(context,toBuy)
    g.if_trade=False    

#6
#获得卖出信号，并执行卖出操作
#输入：context,toBuy-list
#输出：none
def order_stock_sell(context,toBuy):
    # 对于不需要持仓的股票，全仓卖出
        for i in context.portfolio.positions:
            if i not in toBuy:
                order_target_value(i, 0)

#7
#获得买入信号，并执行买入操作
#输入：context,toBuy-list
#输出：none
def order_stock_buy(context,toBuy):
    # 对于不需要持仓的股票，按分配到的份额买入
    for i in toBuy:
        if i not in context.portfolio.positions:
            order_target_value(i,g.everyStock)

#9
#取因子数据
#输入：f-全局通用的查询,股票列表
#输出：因子数据，打分完毕的股票的代码-dataframe
def getRankedFactors(f,all_stocks):
    # 获得股票的基本面数据
    q = query(valuation,balance,cash_flow,income,indicator).filter(valuation.code.in_(all_stocks))
    df = get_fundamentals(q)
    #获取我们指定因子的df
    df1= df[f]
    #将股票名字当作列表
    df1.index = df.code
    #把因子值变成排序的值
    df1=df1.rank(axis=0, method='average', ascending=True)
    #进行打分
    points=np.dot(df1.values,g.weights)
    #打分加入df
    df1['points']=pd.Series(list(points),index=df1.index)
    #排序
    df1=df1.sort('points',ascending=True)
    #返回一个打完分的df
    return df1

'''
================================================================================
每天收盘后
================================================================================
'''
# 每日收盘后要做的事情（本策略中不需要）
def after_trading_end(context):
    return
