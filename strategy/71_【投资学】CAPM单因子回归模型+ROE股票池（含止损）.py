该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/13973

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

#策略概述：以ROE为筛选标准，选择沪深300中满足条件的股票作为股票池
#采用CAPM模型，利用选单因子回归，计算出阿尔法值，选出阿尔法值最大的前16支股票进行投资
import numpy as np
from scipy import stats
import pylab

'''
============================================================================
初始化
============================================================================
'''

def initialize(context):
    set_params()        #1设置策略参数
    set_variables()     #2设置中间变量
    set_backtest()    # 3设置回测条件
    run_daily(stop, time='after_close')
    
#1设置策略参数
def set_params():
    g.index = '000300.XSHG'
    #每次取alpha最小的16支股票
    g.num = 16
    #每次回归调用前days天的数据
    g.days = 121
    g.tc = 10
    g.N = 121          # 需要前多少天的数据
    g.rf=0.04/252           #无风险利率，用于计算超额收益
    g.ROE_requirement=10 #ROE大于10%
    
#2设置中间变量
def set_variables():
    g.t=0               #记录连续回测天数
    g.if_trade=False    #当天是否交易
    g.feasible_stocks=[]
    
#3设置回测条件
def set_backtest():
    set_benchmark('000300.XSHG')
    set_option('use_real_price',True) # 用真实价格交易
    log.set_level('order','error')    # 设置报错等级
    
'''
=====================================================================
每天回测前
=====================================================================
'''
def before_trading_start(context):
    if g.t % g.tc ==0:
        #每g.tc天，交易一次
        g.if_trade=True 
        # 设置手续费与手续费
        set_slip_fee(context) 
        
        
        # 获得ROE大于设定的值的股票池
        a=query(indicator.code,indicator.roe
        # 筛选 ROE大于设定的值
        ).filter(indicator.roe > g.ROE_requirement
        # 排序 按ROE从大到小排
        ).order_by(indicator.roe.desc()
        ).limit(1000)
        ROE_securities=get_fundamentals(a)
        securities_list=list(ROE_securities.code)


        g.feasible_stocks = set_feasible_stocks(securities_list,g.N,context)
    g.t+=1
    
#4 剔除股票池中在样本期间停牌的股票
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
    for stock in unsuspened_stocks:
        if not(isnan(attribute_history(stock, days, unit='1d',fields=('close'),skip_paused=True).iloc[0,0])):
            feasible_stocks.append(stock)
    return feasible_stocks    

#5 根据不同的时间段，设置滑点与手续费
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
=====================================================================
每天回测时
=====================================================================
'''
def handle_data(context, data):
    to_sell, to_buy = get_signal(context)
    sell_and_buy_stocks(context, to_sell, to_buy)

#6 将股票价格转化为超额收益率，输入为days天的股票收盘价，输出为days-1天的超额收益率
def price2ret(price):
    ret = []
    rf = g.rf
    for i in range(len(price)-1):
        ret.append((price[i+1] - price[i])/price[i] - rf)
    return ret

#7 获得调仓信号
def get_signal(context):
    if g.if_trade == True:
        num = g.num
    #stocks为ROE筛选过后的股票代码list
        stocks = g.feasible_stocks
    #取days个交易日的数据
        days = g.days
    #security为沪深300的指数代码
        security = g.index
    #取得沪深300指数的收盘价
        marketporfolio = attribute_history(security, days, '1d', 'close')
    #计算沪深300指数的收益率
        marketreturn = price2ret(marketporfolio['close'])
        alpha=[]
    #用for循环计算通过ROE筛选的股票池中的每个股票的alpha
        for stock in stocks:
            stockprice = attribute_history(stock, days, '1d', 'close')
            stockreturn = price2ret(stockprice['close'])
            beta, stockalpha, r_value, p_value, slope_std_error = stats.linregress(marketreturn, stockreturn)
            alpha.append([stock,stockalpha])
    #对每只股票的alpha进行排序
        sortedalpha = sorted(alpha,key=lambda X:X[1])
    #取alpha最大的num支股票——————————————
        targetstocks = sortedalpha[(-num):]
    #——————————————————————————————————
        targetstock = []
        taralpha = []
    #用for循环得到目标股票的代码和对应的alpha
        for k1 in range(len(targetstocks)):
            targetstock.append(targetstocks[k1][0])
            taralpha.append(targetstocks[k1][1])
        taralpha = [(max(taralpha) - p)/(max(taralpha) - min(taralpha)) for p in taralpha]
        totalalpha = sum(taralpha)
        
    #计算每个股票的持仓权重：根据alpha来分配
        weights = [x/totalalpha for x in taralpha]
    #得到当前以持有的股票池
        present = context.portfolio.positions
    #得到当前股票池中的股票代码
        stocksnow = present.keys()
   
        if len(stocksnow)>0:
            valuenow = []
            stockandvalue = {}
            for stock in stocksnow:
                s_amount = context.portfolio.positions[stock].sellable_amount
                l_s_p = context.portfolio.positions[stock].last_sale_price
                valuenow = s_amount*l_s_p
                stockandvalue[stock] = valuenow
    #得到当前股票组合和剩余资金总和
        capital = context.portfolio.portfolio_value
    #得到按照目标权重配股时对应的股票配资
        tarcapallocation = [capital*x for x in weights]
        tarstoandcap = dict(zip(targetstock, tarcapallocation))
        to_sell = {}
    #若当前持有股票市值大于目标市值，则进行卖出
        for stock in stocksnow:
            if stock in targetstock:
                gap = tarstoandcap[stock] - stockandvalue[stock]
                if gap<0:
                    to_sell[stock] = tarstoandcap[stock]
            else:
                to_sell[stock] = 0
    
    #按照目标配比对目标股票组合进行买入
        to_buy = {}
        for stock in targetstock:
            to_buy[stock] = tarstoandcap[stock]
        #print(to_sell, to_buy)
        return to_sell, to_buy
    else:
        return {},{}
        
#8 调整仓位
def sell_and_buy_stocks(context, to_sell, to_buy):
    if g.if_trade:
        for stock in to_sell.keys():
            order_target_value(stock, to_sell[stock])
        for stock in to_buy.keys():
            order_target_value(stock, to_buy[stock])
    g.if_trade = False

#9 止损
def stop(context):
    # 循环查看持仓的每个股票
    for stock in context.portfolio.positions:
        # 如果股票收盘价格除以平均成本小于0.7，即亏损超过30%
        if (context.portfolio.positions[stock].price/context.portfolio.positions[stock].avg_cost < 0.7): 
            # 调整stock的持仓为0，即卖出
            order_target(stock, 0) 
            #剩余资金用于买国债
            cash=context.portfolio.available_cash
            order_target_value('000012.XSHG',cash)
            # 输出日志：股票名 止损
            print "\n%s 止损" % stock
    

