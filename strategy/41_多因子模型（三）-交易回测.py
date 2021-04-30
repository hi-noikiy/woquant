该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/14084

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

# 导入函数库
from jqdata import *
from six import StringIO
import cPickle as pickle
import time
import datetime
from multiprocessing.dummy import Pool as ThreadPool
from jqfactor import Factor,calc_factors
import pandas as pd
import statsmodels.api as sm
import scipy.stats as st
import pickle
# 初始化函数，设定基准等等
def initialize(context):
    
    g.index='000300.XSHG'
    pkl_file_read = read_file("MyPackage_Final.pkl")
    load_Package = pickle.load(StringIO(pkl_file_read))
    g.univ_dict,g.ic_df,g.Effect_factor_dict=load_Package    
    g.trade_date_list=sort(list(g.univ_dict.keys()))[:-1]
    g.N=30
    
    set_benchmark(g.index)
    set_option('use_real_price', True)
    log.set_level('order', 'error')
    set_order_cost(OrderCost(close_tax=0.001,open_commission=0.0003,close_commission=0.0003,min_commission=5),type='stock')
    set_slippage(FixedSlippage(0))
    
def before_trading_start(context):
    g.trade_signal=False
    #看是否在调仓日
    date=context.current_dt.date()
    if date in g.trade_date_list:
        g.trade_signal=True

def handle_data(context,data):
    # 如果今天不是调仓日，就洗洗睡
    if g.trade_signal==False:
        return
    # 今天是调仓日，就是干！
    date=context.current_dt.date()
    ic=g.ic_df.loc[date,:]
    
    univ=g.univ_dict[date]
    factor_df=pd.DataFrame()
    for key,value in g.Effect_factor_dict.items():
        factor_df=factor_df.append(value.loc[date,univ].to_frame(key).T)
    
    stock_list=factor_df.multiply(ic,axis=0).sum().to_frame('a').sort('a',ascending=False).index[0:g.N]
    holding_list=filter_specials(stock_list,context)
    rebalance(context,holding_list)
    
def filter_specials(stock_list,context):
    current_data=get_current_data()
    stock_list=[stock for stock in stock_list if \
                (not current_data[stock].paused)
                and (not current_data[stock].is_st)
                and ('ST' not in current_data[stock].name)
                and ('*' not in current_data[stock].name)
                and ('退' not in current_data[stock].name)
                and (current_data[stock].low_limit<current_data[stock].day_open<current_data[stock].high_limit)
                and get_security_info(stock).start_date<context.previous_date-datetime.timedelta(365)
                ]
    return stock_list   
    
def rebalance(context,holding_list):
    every_stock = context.portfolio.portfolio_value/len(holding_list)  # 每只股票购买金额
    # 空仓只有买入操作
    if len(list(context.portfolio.positions.keys()))==0:
        # 原设定重scort始于回报率相关打分计算，回报率是升序排列
        for stock_to_buy in list(holding_list): 
            order_target_value(stock_to_buy,every_stock)
    else :
        # 不是空仓先卖出持有但是不在购买名单中的股票
        for stock_to_sell in list(context.portfolio.positions.keys()):
            if stock_to_sell not in list(holding_list):
                order_target_value(stock_to_sell, 0)
        # 因order函数调整为顺序调整，为防止先行调仓股票由于后行调仓股票占金额过大不能一次调整到位，这里运行两次以解决这个问题
        for stock_to_buy in list(holding_list): 
            order_target_value(stock_to_buy, every_stock)
        for stock_to_buy in list(holding_list): 
            order_target_value(stock_to_buy, every_stock)    
    


