该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/11165

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

# 导入函数库
import jqdata
import talib
import pandas as pd
import numpy as np
import datetime
from datetime import timedelta
import math
from numpy import nan

# 初始化函数，设定基准等等
def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000001.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 输出内容到日志 log.info()
    log.info('初始函数开始运行且全局只运行一次')
    # 过滤掉order系列API产生的比error级别低的log
    # log.set_level('order', 'error')
    g.num_stock = 10
    g.index = '000001.XSHG'
    g.index2 = '000300.XSHG'#沪深300
    g.index8 = '399006.XSHE'#创业板指数
    # g.index2 = '000016.XSHG'#上证50
    # g.index8 = '399333.XSHE'#中小板R 
    g.risk_ratio = 0.10
    ### 股票相关设定 ###
    # 股票类每笔交易时的手续费是：买入时佣金万分之三，卖出时佣金万分之三加千分之一印花税, 每笔交易佣金最低扣5块钱
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    run_monthly(rebalence,1,time = '14:50')

    
## 开盘前运行函数     
# def before_trading_start(context):
    
    
## 开盘时运行函数
def handle_data(context, data):
    if market_not_safe(g.index2,g.index8):
        # if len(context.portfolio.positions) >0:
        clear_position(context)
        return
    # if g.days%g.period == 0:
    #     if [context.current_dt.hour,context.current_dt.minute] == [14,50]:
        # rebalence(context)
    # g.days = g.days+1
    # for stock in context.portfolio.positions:
    #     if can_sell(stock):
    #         order_target_value(stock,0)
 
def rebalence(context):
    # if not market_not_safe(g.index2,g.index8):
    
    stocklist = select_stock(context)
    #卖出
    for stock in context.portfolio.positions:
        if stock not in stocklist:
            order_target_value(stock,0)
    stock_values = calPosition(context,stocklist)
    for stock in stock_values:
        curPrice = attribute_history(stock, 1, '1m', ('close'),fq='pre')['close'].values
        curValue = context.portfolio.positions[stock].total_amount * curPrice
        target_value = stock_values[stock]
        if abs(target_value - curValue)>0.2:
            order_target_value(stock,target_value)
    
def select_stock(context):
    stocklist = get_index_stocks(g.index)
    stock_list = filter_specials(stocklist)
    stock_list = filter_new_and_sub_new(stock_list)
    stock_list = filter_big_amout_of_increase(stock_list)
    factor_dict = {}
    for stock in stock_list:
        temp = []
        temp.append(get_smart_money_factor(stock))
        factor_dict[stock] = temp
    df_factor = pd.DataFrame(factor_dict).T 
    df_factor = df_factor.dropna()
    df_factor.columns = ['smart_money_factor']
    df = df_factor.sort('smart_money_factor')
    print df.head()
    # stock_list = list(df.index.values)[:int(len(df)*0.1)]
    stock_list = list(df.index.values)[:10]
    
    return stock_list
    

def filter_big_amout_of_increase(stocklist,ratio = 0.2):
    stock_dict = {}
    for stock in stocklist:
        stock_dict[stock] = get_growth_rate(stock)
    sort_list = sorted(stock_dict.items(),key = lambda x:x[1])
    stock_list = sort_list[:int(len(sort_list)*(1-ratio))]
    stock_list = [stock[0] for stock in stock_list]
    return stock_list

def filter_new_and_sub_new(stocklist,days = 60):
    stock_list = []
    for stock in stocklist:
        start_date = get_security_info(stock).start_date
        if (datetime.date.today()-start_date)>timedelta(60):
            stock_list.append(stock)
    return stock_list



def get_smart_money_factor(stock,count_day = 1):
    
    df = attribute_history(stock,count_day*230,'1m',['open','close','volume'])
    df['zdf'] = abs(df['close']/df['open']-1)
    df['smart'] = df['zdf']/(df['volume'].apply(math.sqrt))
    df = df.sort('smart',ascending = False)
    df['cum_vol'] = df['volume'].cumsum()
    df['cum_vol'] = df['cum_vol']/df.ix[-1,'cum_vol']
    df_smart = df[df['cum_vol']<=0.2]
    all_vol = df['volume'].sum()
    all_smartvol = df_smart['volume'].sum()
    VWAP_smart = (df_smart['volume']*df_smart['close']/all_smartvol).sum()
    VWAP_all = (df['volume']*df['close']/all_vol).sum()
    try:
        factor = VWAP_smart/VWAP_all
    except:
        factor = nan
    return factor



    
def filter_specials(stock_list):
    curr_data = get_current_data()
    stock_list = [stock for stock in stock_list if \
                  (not curr_data[stock].paused)  # 未停牌
                  and (not curr_data[stock].is_st)  # 非ST
                  and ('ST' not in curr_data[stock].name)
                  and ('*' not in curr_data[stock].name)
                  and ('退' not in curr_data[stock].name)
                  and (curr_data[stock].low_limit < curr_data[stock].day_open < curr_data[stock].high_limit)  # 未涨跌停
                  ]

    return stock_list

def market_not_safe(index2,index8):
    gr_index2 = get_growth_rate(index2)
    gr_index8 = get_growth_rate(index8)
    if gr_index2 <= 0 and  gr_index8 <= 0:
        return True

def get_growth_rate(security, n=20):
    lc = get_close_price(security, n)
    c = get_close_price(security, 1, '1m')
    
    #判断是数据是否为空
    if not isnan(lc) and not isnan(c) and lc != 0:
        return (c - lc) / lc
    else:
        log.error("数据非法, security: %s, %d日收盘价: %f, 当前价: %f" %(security, n, lc, c))
        return 0
        

def can_buy(security,short=5,long=20):
    #检查均线是否多头
    ma_short = attribute_history(security, short, '1d', ('close'), True).mean()['close']
    ma_long = attribute_history(security, long, '1d', ('close'), True).mean()['close']
    cur_price = get_close_price(security,1,'1m')
    yes_price = get_close_price(security,1)
    if ma_short >= ma_long and cur_price > yes_price:
        return True
        




def get_close_price(security, n, unit='1d'):
    return attribute_history(security, n, unit, ('close'), True,fq='pre')['close'][0]
   
def clear_position(context):
    if len(context.portfolio.positions)>0:
        for stock in context.portfolio.positions:
            order_target_value(stock,0)
        log.info('大盘止损,全盘清仓')


def calPosition(context, buylist):
    # 每次调仓，用 positionAdjustFactor 来控制承受的风险，最大损失为总仓位 * positionAdjustFactor
    positionAdjustValue = context.portfolio.total_value * g.risk_ratio
    Ajustvalue_per_stock = float(positionAdjustValue)/len(buylist)

    hStocks = history(1, '1m', 'close', buylist, df=False)

    risk_value = {}
    # 计算组合后的 ATR，此处假设资金是平均分配。
    for stock in buylist:
        curATR = 2*float(fun_getATR(stock))
        if curATR != 0 :
            risk_value[stock] = hStocks[stock]*Ajustvalue_per_stock/curATR
        else:
            risk_value[stock] = 0

    total_value = sum([risk_value[stock] for stock in risk_value])
    if total_value > context.portfolio.total_value:
        tempdict = {}
        for stock in buylist:
            tempdict[stock] = context.portfolio.total_value*(risk_value[stock]/total_value)
        risk_value = tempdict
    return risk_value   


def fun_getATR(stock):
    ATRlag = 14

    # 计算ATR及Keltner Band 
    try:
        hStock = attribute_history(stock, ATRlag+10, '1d', ('close','high','low') , df=False)
    except:
        log.info('%s 获取历史数据失败' %stock)
        return 0
    close_ATR = fun_normalizeData(hStock['close'])
    high_ATR = fun_normalizeData(hStock['high'])
    low_ATR = fun_normalizeData(hStock['low'])
    try:
        ATR = talib.ATR(high_ATR, low_ATR, close_ATR, timeperiod=ATRlag)
    except:
        return 0

    return ATR[-1]

def fun_normalizeData(myData):
    # 去极值
    std = np.std(myData)
    MA = np.mean(myData)
    for i in range(len(myData)):
        if myData[i] > MA + 3*std:
            myData[i] = MA + 3*std
        elif myData[i] < MA - 3*std:
            myData[i] = MA - 3*std
    return myData    

