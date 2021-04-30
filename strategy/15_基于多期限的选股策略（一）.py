该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/12916

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

# 导入函数库
import jqdata
import numpy as np
import pandas as pd
import datetime
import time
#import statsmodels.api as sm
from sklearn import linear_model
from sklearn.preprocessing import Imputer
# 初始化函数，设定基准等等
def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    
    # 过滤掉order系列API产生的比error级别低的log
    # log.set_level('order', 'error')
    
    set_option('use_real_price',True) # 用真实价格交易
    log.set_level('order','error')    # 设置报错等级
    ### 股票相关设定 ###
    # 股票类每笔交易时的手续费是：买入时佣金万分之三，卖出时佣金万分之三加千分之一印花税, 每笔交易佣金最低扣5块钱
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    set_pas()    #1设置策略参数
    set_variables() #2设置中间变量
    
    ## 运行函数（reference_security为运行时间的参考标的；传入的标的只做种类区分，因此传入'000300.XSHG'或'510300.XSHG'是一样的）
      # 开盘前运行
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG') 
      # 开盘时运行
    run_daily(market_open, time='open', reference_security='000300.XSHG')
      # 收盘后运行
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')


def set_pas():
    g.tc = 7  # 设置调仓天数
    g.num_stocks = 5  # 设置每次调仓选取的股票数量
    # 定义股票池，上证180指数成分股
    g.index='000010.XSHG'
    g.stocks = get_index_stocks(g.index)


#设置中间变量
def set_variables():
    g.t = 0 #记录回测运行的天数
    g.if_trade = False #当天是否交易
    
#设置回测条件



def calAt(stock,date,n):
    #计算股票stock的n日均线因子
    #用于计算当期因子值
    #输入参数：stock：股票代码；date:计算日期；n:计算日期前n天
    price = get_price(stock,end_date=date, frequency='daily', fields='close', skip_paused=True, fq='pre', count=n)
    At = mean(price)
    Atadjust = At/price.tail(1)
    Atadjust = Atadjust.iloc[0,0]
    return Atadjust
#返回值

def calAtevery(stock,flagDate,n):
    #计算股票stock的n日均线因子
    #用于计算 训练集 的函数
    date = flagDate
    price = get_price(stock,end_date=flagDate, frequency='daily', fields='close', skip_paused=True, fq='pre', count=n)
    At = mean(price)
    Atadjust = At/price.tail(1)
    return Atadjust
#返回pandas对象

#计算训练集
def calATlist(stock,date,n):
    lastDate = date
    #lastDate = datetime.datetime.strptime(date, '%Y-%m-%d')
    #输入时间为date
    delta = datetime.timedelta(days=7)
    lastDate = lastDate - delta
    #往前推一周 计算训练用 AT因子，（因为要用前一周的因子和当周的收益率回归）
    At = []
    for i in range(25):
        temp = calAtevery(stock,lastDate,n)
        At.append(temp.iloc[0,0])
        lastDate = lastDate - delta
    return At
 
def calEstYeild(stock,date):
    k = [3, 5, 10, 20, 30, 60,90,120, 180, 240, 270, 300]
    ATlist=[]
    #计算 前25个单位时间内各长度的均线因子 以及 收益率
    df = pd.DataFrame()
    for item in k:
        df['%s'%item]=calATlist(stock,date,item)
    #将收益率序列添加到最后一列    
        df['rflist']=calRFlist(stock,date)
        
    #计算用于 预测输入的因子值
    st = [1,2,3,4,5,6,7,8,9,10,11,12]
    for i,item in enumerate(k):
        st[i] = calAt(stock,date,item)
        
        #线性回归部分
    
    #imp = Imputer(missing_values='NaN',strategy='mean',axis=0,verbose=0,copy=True)
    #df = imp.fit_transform(df)
    #df = pd.DataFrame(df)
    #df.columns = ['3','5','10','20','30','60','90','120','180','240','270','300','rflist']
    
    #log.info(df)
    
    y = df['rflist']
    x = df[['3','5','10','20','30','60','90','120','180','240','270','300']]
    clf = linear_model.LinearRegression()
    clf.fit(x,y)
    yhat = clf.predict(st)
    #x = sm.add_constant(x)#添加截距项
    #est = sm.OLS(y,x).fit()
    #est.summary() #看统计量结果
    #est.params #查看回归参数
    #预测收益率
    #yhat = est.predict(st)
    return yhat
   
def calRFlist(stock,date):
    #计算收益率序列
    nowDate = date
    #nowDate = datetime.datetime.strptime(date, '%Y-%m-%d')
    delta = datetime.timedelta(days=7)
    rflist = []
    for i in range(25):
        weekprice = get_price(stock,end_date=nowDate,frequency='daily',fields=['close','open'],count=5,skip_paused=True)
        cp = weekprice.iloc[1,-1]
        op = weekprice.iloc[2,1]
        rf = (cp-op)/op
        rflist.append(rf)
        nowDate = nowDate - delta
    return rflist   

def SortStockList(stocks,date):
    df = pd.DataFrame()
    for stock in stocks:
        df['%s'%stock] = calEstYeild(stock,date)
    df = df.T
    stockListSorted = df.sort(columns=0)
    return stockListSorted

def set_slip_fee(context):
    # 将滑点设置为0
    set_slippage(FixedSlippage(0)) 
    # 根据不同的时间段设置手续费
    dt=context.current_dt
    log.info(type(context.current_dt))
    
    if dt>datetime.datetime(2013,1, 1):
        set_commission(PerTrade(buy_cost=0.0003, sell_cost=0.0003, min_cost=5)) 
        
    elif dt>datetime.datetime(2011,1, 1):
        set_commission(PerTrade(buy_cost=0.001, sell_cost=0.002, min_cost=5))
            
    elif dt>datetime.datetime(2009,1, 1):
        set_commission(PerTrade(buy_cost=0.002, sell_cost=0.003, min_cost=5))
                
    else:
        set_commission(PerTrade(buy_cost=0.003, sell_cost=0.004, min_cost=5))    


## 开盘前运行函数     
def before_market_open(context):
    if g.t%g.tc==0:
        #每g.tc天，交易一次行
        g.if_trade=True 
        # 设置手续费与手续费
        # set_slip_fee(context)
    
## 开盘时运行函数
def market_open(context):
    log.info(g.t, g.tc, g.if_trade)
    date = context.current_dt
    if g.if_trade == True:
        # 依本策略的买入信号，得到应该买的股票列表
        MS_should_buy = SortStockList(g.stocks,date).tail(5).index
        log.info(MS_should_buy)
        # 计算现在的总资产，以分配资金，这里是等额权重分配 返回一个数
        MonPerStock=context.portfolio.portfolio_value/g.num_stocks
        # 得到当前持仓中可卖出的股票
        if len(context.portfolio.positions)>0:
            #当持仓不为零时，剔除持仓股票中停牌股即可 返回list
            holding = context.portfolio.positions
        else:
            # 当持仓为0时，可卖出股票为0 返回list
            holding = []
        # 对于不需要持仓的股票，全仓卖出
        for stock in holding:
            if stock not in MS_should_buy:
                order_target_value(stock, 0)
        # 对于需要持仓的股票，按分配到的份额买入
        for stock in MS_should_buy:
            order_target_value(stock, MonPerStock)
    g.if_trade = False
    
## 收盘后运行函数  
def after_market_close(context):
    g.t+=1
    log.info(str('函数运行时间(after_market_close):'+str(context.current_dt.time())))
    #得到当天所有成交记录
    trades = get_trades()
    for _trade in trades.values():
        log.info('成交记录：'+str(_trade))
    log.info('一天结束')
    log.info('##############################################################')

    pass
