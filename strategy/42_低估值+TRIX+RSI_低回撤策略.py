该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/11292

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

import jqdata
# 导入talib库命名为tl
import talib as tl
# 导入numpy库命名为tl
import numpy as np
# 导入 technical_analysis 库
from jqlib.technical_analysis import *
'''
================================================================================
总体回测前
================================================================================
'''

#### 配置参数  最多持有几只股票
MAX_OWN_NUM = 2
#### 配置参数  买入单只股票,最大使用可用资金的几分之1
CASH_SP_COUNT = 2
#### 配置参数  每天开仓买入,最大使用多少可用资金额
CASH_MAX_USE  = 20000
#### 配置参数  每只股票买入最大使用多少资金额
CASH_MAX_USE_PERSTOCK = 10000

#   初始化函数，设定基准等等
def initialize(context):
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 输出内容到日志 log.info()
    log.info('初始函数开始运行且全局只运行一次')
    log.set_level('order', 'error')
    g.HighAfterEntry = {} #存放 持仓股票 买入后所创最高价
    g.holdday = {}#存放 持仓股票 买入后持仓天数
    ### 股票相关设定 ###
    #交易费率:
    set_order_cost(OrderCost(close_tax=0.001#印花税
                            , open_commission=0.0003#佣金
                            , close_commission=0.0003
                            , min_commission=5), type='stock')
    ## 运行函数
      # 盘前运行
    run_daily(before_market_open, time='before_open') 
      # 盘中运行
    run_daily(market_open, time='close-10m')
      # 盘后运行
    run_daily(after_market_close, time='after_close')
    

'''
================================================================================
每天开盘前
================================================================================
'''
#   盘前运行     
def before_market_open(context):
    g.date = context.current_dt.strftime("%Y-%m-%d")
    # 输出运行时间
    log.info('盘前运行:'+str(context.current_dt.time()))
    #设定备选股票池（中证800）
    g.codelist = get_index_stocks('000300.XSHG')
    #g.codelist = ['601231.XSHG']
    #log.info('codelist:',g.codelist)
    g.codelist = gl_tp(g.codelist)# 过滤停牌股票
    #log.info('codelist_tp:',g.codelist)
    g.codelist = gl_st(g.codelist)# 过滤ST股票
    #log.info('codelist_st:',g.codelist)
    # 开盘前更新 g.HighAfterEntry 持仓股票买入后历史最高价
    update_HighAfterEntry(context)
   
    
## 过滤停牌股票
def gl_tp(codelist):
    current_data = get_current_data()
    codelist = [code for code in codelist if not current_data[code].paused]
    return codelist
## 过滤ST股票
def gl_st(codelist):
    current_data = get_current_data()
    codelist = [code for code in codelist if not current_data[code].is_st]
    return codelist
##  更新 g.HighAfterEntry 持仓股票买入后历史最高价
def update_HighAfterEntry(context):
    if len(g.HighAfterEntry) > 0:
        for code in g.HighAfterEntry.keys():
            sj = get_bars(code, 1, unit='1d',fields=['close'],include_now=True)
            if g.HighAfterEntry[code] < sj['close'][-1]:
                g.HighAfterEntry[code] = sj['close'][-1]
            else:
                pass
            #log.info('最高价:', g.HighAfterEntry)

'''
================================================================================
================================================================================
'''
#   盘中运行
def market_open(context):
    
    log.info('盘中运行:'+str(context.current_dt.time()))
    sell_pd(context)##  卖出扫描判断
    tdsell(context)##  卖出
    
    buy_pd(context)##  买入扫描判断
    tdbuy(context)##  买入
'''
================================================================================
每天交易时 买入程序
================================================================================
'''
def Check_Stocks(context):
    security = g.codelist
    Stocks = get_fundamentals(query(
            valuation.code,
            valuation.pb_ratio,
            balance.total_assets,
            balance.total_liability,
            balance.total_current_assets,
            balance.total_current_liability
        ).filter(
            valuation.code.in_(security),
            valuation.pb_ratio < 2,
            valuation.pb_ratio > 0,
            balance.total_current_assets/balance.total_current_liability > 1.2
        ))

    Stocks['Debt_Asset'] = Stocks['total_liability']/Stocks['total_assets']
    me = Stocks['Debt_Asset'].median()
    Code = Stocks[Stocks['Debt_Asset'] > me].code
    return list(Code)
##  买入扫描判断
def buy_pd(context):
    buy = []
    own_num = len(context.portfolio.positions)#当前持仓数
    if own_num < MAX_OWN_NUM:#如果当前持仓数<最大持仓数，执行选股
        codelist = Check_Stocks(context)
        for code in codelist:
            if code in context.portfolio.positions:#剔除持仓股票
                continue#继续，作用不执行剩余代码，结束本次循环
            if  btj1(code)==False or btj2(code)==False:
                continue
            #elif btj3(code)        == False:
            #    continue
            #elif btj4(context,code)== False:
            #    continue
       
            else :
                buy.append(code)#append添加，在buy中添加股票代码
            #当达到最大持有数是，停止选股
            if len(buy) + own_num == MAX_OWN_NUM:
                break

    #set()创建一个无序不重复元素集,可以计算交集'&'、差集'-'、并集'|'运算
    g.tdbuy = list(set(buy) - set(g.tdsell))#剔除今日卖出的股票
    #log.info(' tdbuy ',g.tdbuy)#在日志中输出
    return
##  买入
def tdbuy(context):
    buylist = g.tdbuy
    if len(buylist)>0:#len=长度，如果 买入列表长度>0
        #每份资金=min(设定.最大可用现金,账户现金)/max(今日买入只数,买入单只股票,最大使用可用资金的几分之1）
        per_cash = min(CASH_MAX_USE,context.portfolio.available_cash)/max(len(buylist),CASH_SP_COUNT)
    else:#否则
        per_cash = 0
    for code in buylist:
        # 用所有 cash 买入股票
        order_value(code, per_cash)
        # 记录这次买入
        #log.info("开仓，买入 %s" % (code))    
    return
####买入条件1：
def btj1(code):
    a = bei_li(code)
    b = RS(code)
    tj = False
    if  a == -1:
        tj = True
    return tj
def btj2(code):
    a = bei_li(code)
    b = RS(code)
    tj = False
    if  b == -1:
        tj = True
    return tj
####买入条件2：
'''
================================================================================
每天交易时 卖出程序
================================================================================
'''
##  卖出扫描判断
def sell_pd(context):
    g.tdsell = []
    if len(context.portfolio.positions)>0:
        for code in context.portfolio.positions:#如果股票在持仓中
            if  stj1(code) == True :
                g.tdsell.append(code)
    #log.info('tdsell ',g.tdsell)
##  卖出
def tdsell(context):
    sell_list = g.tdsell
    
    for code in sell_list:
        # 卖出所有股票,使这只股票的最终持有量为0
        order_target(code, 0)
        # 记录这次卖出
        #log.info("平仓，卖出 %s" % (code))
    return
####卖出条件1
def stj1(code):
    a = bei_li(code)
    b = RS(code)
    tj = False
    if  b == 1 or a==1:
        tj = True
    return tj


'''
================================================================================
盘后运行
================================================================================
'''
#   收盘后运行函数  
def after_market_close(context):
    log.info(str('盘后运行:'+str(context.current_dt.time())))
    ji_lu(context)
    
    #画线
    record (a=GetCurrentPositionCount(context))
    #record ()
    #record ()
    log.info('一天结束\n══════════════════════════════════════════════════════════════════════════════════════════════════════════════════')

def ji_lu(context):
    trades = get_orders()    #得到当天所有成交记录
    for t in trades.values():
        #if t.is_buy and t.filled>0:
        if t.action == 'open' and t.filled>0:
            x = str(t.security)
            g.HighAfterEntry[x] = t.price
        #elif not t.is_buy and t.filled>0:
        elif t.action == 'close' and t.filled>0:
            xx = str(t.security)
            try:
                del g.HighAfterEntry[xx]
            except:
                g.HighAfterEntry[xx] = 0
        log.info("成交记录 \n\
                              代码：%s\n\
                              方向：%s\n\
                              价格：%s\n\
                              数量：%s\n"
                              ,t.security,t.action,t.price,t.filled)

##  获取当前持有几只股票
def GetCurrentPositionCount(context):
    c=0#初始为0只，空仓
              # context.portfolio.positions = 当前持仓
    for code in context.portfolio.positions:
        if context.portfolio.positions[code].total_amount>0:#如果仓位>0
            c+=1   #c+1     
    return c

'''
================================================================================
附属程序
================================================================================
'''


def bei_li(code):
    security=code
    check_date=g.date
    TRIX1,MATRIX1 = TRIX(security,check_date, N = 12, M = 20)
    TRIX11=TRIX1[security]
    MATRIX11=MATRIX1[security]
    dev_type = None
    if TRIX1[security]>MATRIX1[security]:
        
       
        dev_type = -1
    
    elif TRIX1[security] < MATRIX1[security]: 
        
        
        dev_type = 1
    else:  
       
        dev_type = 0
    
    return dev_type

def RS(code):
    security=code
    check_date=g.date
    RSI1 = RSI(security,check_date,  N1=6)
    RSI11=RSI1[security]
    dev_type = None
    if 80>RSI11>55 or RSI11<15:
        
       
        dev_type = -1
    
    elif 50>RSI11>20 or RSI11>85: 
       
        
        dev_type = 1
    else:  
     
        dev_type = 0
    
    return dev_type


