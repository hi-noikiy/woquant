该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/14203

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

# 导入函数库
from jqdata import *

#入市 20日最高值   需考虑先平仓
#离市 反向5%
#加仓 涨0.5N
#止损 跌2N

## 初始化函数，设定基准等等
def initialize(context):

## ===============================标的选择============================
    g.symbol='CU'
    set_benchmark(get_future_code(g.symbol)) 
    # set_option('futures_margin_rate', 0.06)
## ================设置：是否合约到期移仓，策略频率===================
    g.shift=True                        # 是否进行合约移仓
    g.frequency='1m'                    #【注意】分钟回测用'1m',天回测用'1d'
    
# 设定账户为金融账户
    set_subportfolios([SubPortfolioConfig(cash=context.portfolio.starting_cash, type='index_futures')])
    set_order_cost(OrderCost(open_commission=0.000023, close_commission=0.000023,close_today_commission=0.0023), type='index_futures')
    set_slippage(FixedSlippage(0))
    set_option('use_real_price', True)  # 开启动态复权模式(真实价格)
    log.set_level('order', 'error')     # 过滤掉order系列API产生的比error级别低的log

    g.N=20                     #通道长度
    g.limit=4                  #最多加4次仓
    g.position=0               #持有头寸
    g.add=0                    #加仓次数
    g.lastprice=0              #上一次成交价格
    g.markprice=0              #记录极限价格
    g.lastfuture=None
    g.contract_change=False

    run_daily(before_market_open, time='before_open', reference_security=get_future_code(g.symbol))
    run_daily(while_open, time='every_bar', reference_security=get_future_code(g.symbol))    
    
## 开盘前运行函数
def before_market_open(context):
# 得到主力合约
    g.future=get_dominant_future(g.symbol)
    price=attribute_history(g.future,g.N+1,'1d',('open','high','low','close'))
    g.upperbound=max(price['high'].iloc[1:].dropna())  #如果主力合约是下月的，换合约时，回取数据不到20天。
    g.lowerbound=min(price['low'].iloc[1:].dropna())
    g.ATR=calc_ATR(price)

    if g.lastfuture==None:
        g.lastfuture=g.future
    elif g.lastfuture!=g.future:
        g.contract_change=True
        p1=get_bars(g.future,1,'1d','close')
        p0=get_bars(g.lastfuture,1,'1d','close')
        g.adj=p1[0][0]/p0[0][0]       #由于基差的问题，用于调整g.markprice。
        
## 开盘时运行函数
def while_open(context):

##-----------------------------主力合约变动操作-------------------------    
    if g.contract_change:
        if g.position<0:
            quantity=context.portfolio.short_positions[g.lastfuture].total_amount
            order_target(g.lastfuture,0,side='short')
            print('【合约变更】平原合约 %s 的空仓 %d 手' % (g.lastfuture, quantity))
            if g.shift:
                order(g.future,quantity,side='short')
                print('【合约变更】开新合约 %s 代替原合约的空仓 %d 手' % (g.future, quantity))
                g.markprice=g.markprice*g.adj   #记录极限价格
        elif g.position>0:
            quantity=context.portfolio.long_positions[g.lastfuture].total_amount
            order_target(g.lastfuture,0,side='long')
            print('【合约变更】平原合约 %s 的多仓 %d 手' % (g.lastfuture, quantity))
            if g.shift:
                order(g.future,quantity,side='long')
                print('【合约变更】开新合约 %s 代替原合约的多仓 %d 手' % (g.future, quantity))
                g.markprice=g.markprice*g.adj   #记录极限价格
         
        # 如果不移仓的话，需要reset数据  
        if g.shift==False:
            g.position=0                    #持有头寸
            g.add=0                         #加仓次数
            g.lastprice=0                   #上一次成交价格
        
        # 更新上一次合约
        g.lastfuture=g.future
        g.contract_change=False
    
## ---------------------------------获取当前价格----------------------------------
    price=history(1,g.frequency,'close',g.future)
    #print(price)
    price=price.values[0][0]
    
## -----------------------------------突破开仓-----------------------------------------
    #计算突破唐安琪通道
    breaksignal=check_break(price)
    
    if breaksignal=='long' and g.position<=0:    #突破上通道且无多仓，那么开多仓。
       if g.position<0:
           quantity=context.portfolio.short_positions[g.future].total_amount
           order_target(g.future,0,side='short')
           print('【突破开仓】开多仓前平原来 %s 的空仓 %d 手' % (g.future,quantity))
           reset() 
       # 开多仓
       if g.position==0:
           unit = round(get_unit(context.portfolio.total_value,g.ATR,g.symbol))
           order(g.future,unit,side='long')
           print('【突破开仓】突破上通道开多仓 %s %d 手' % (g.future,unit))
           g.lastprice=price
           g.markprice=price
           g.add+=1
           g.position+=1
           
    if breaksignal=='short' and g.position>=0:    #突破下通道且无空仓，那么开空仓。  
        if g.position>0:
           quantity=context.portfolio.long_positions[g.future].total_amount
           order_target(g.future,0,side='long')
           print('【突破开仓】开空仓前平原来 %s 的多仓 %d 手' % (g.future,quantity))
           reset()
        # 开空仓 
        if g.position==0:
           unit = round(get_unit(context.portfolio.total_value,g.ATR,g.symbol))
           order(g.future,unit,side='short')
           print('【突破开仓】突破下通道开空仓 %s %d 手' % (g.future,unit))
           g.lastprice=price
           g.markprice=price
           g.add+=1
           g.position-=1
           
## -----------------------------判断是否加仓或止损--------------------------------
    # 如果有持仓，计算下加仓信号
    if g.position!=0:
        ac_signal=add_or_close(price,g.lastprice,g.ATR,g.position)
    
        # 根据信号操作   
        if ac_signal=='longclose':
            quantity=context.portfolio.long_positions[g.future].total_amount
            order_target(g.future,0,side='long')
            print('【回调止损】平多仓 %s %d 手止损' % (g.future,quantity))
            reset()
        elif ac_signal=='shortclose':
            quantity=context.portfolio.short_positions[g.future].total_amount
            order_target(g.future,0,side='short')
            print('【回调止损】平空仓 %s %d 手止损' % (g.future,quantity))
            reset()
        elif ac_signal=='longadd' and g.add<g.limit:
            unit=round(get_unit(context.portfolio.total_value,g.ATR,g.symbol))
            order(g.future,unit,side='long')
            print('【顺势加仓】加多仓 %s %d手' % (g.future,unit))
            g.lastprice=price
            g.add+=1
            g.position+=1
        elif ac_signal=='shortadd' and g.add<g.limit:
            unit=round(get_unit(context.portfolio.total_value,g.ATR,g.symbol))
            order(g.future,unit,side='short')
            print('【顺势加仓】加空仓 %s %d手' % (g.future,unit))
            g.lastprice=price
            g.add+=1
            g.position-=1
# ---------------------------------回落止盈止损-----------------------------------
    if g.position!=0:
        set_markprice(price)
        
        if check_stop(price):
            if g.position>0:
                quantity=context.portfolio.long_positions[g.future].total_amount
                order_target(g.future,0,side='long')
                print('【止盈止损】平多仓 %s %d 手结束' %(g.future,quantity))
            if g.position<0:
                quantity=context.portfolio.short_positions[g.future].total_amount
                order_target(g.future,0,side='short')
                print('【止盈止损】平空仓%s %d 手结束' %(g.future,quantity))
            reset()

def check_stop(price):
    if (g.position<0 and price>=1.05*g.markprice) or (g.position>0 and price<=0.95*g.markprice):
        return True
    return False

def set_markprice(price):
    if g.position<0:
        g.markprice=min(price,g.markprice)
    if g.position>0:
        g.markprice=max(price,g.markprice)

def add_or_close(price,lastprice,ATR,position):
    
    if position>0:   #有多头头寸
       if price>=lastprice+0.5*ATR:  #多头加仓
            return 'longadd'
       if price<=lastprice-2*ATR:    #多头平仓
            return 'longclose'
    if position<0:                   #有空头头寸
       if price<=lastprice-0.5*ATR:  #空头加仓
            return 'shortadd'
       if price>=lastprice+2*ATR:    #空头平仓
            return 'shortclose'
            
    return 0  #啥都没干洗洗睡

def check_break(price):
    if price>=g.upperbound:
        breaksignal='long'
    elif price<=g.lowerbound:
        breaksignal='short'
    else:
        breaksignal=0
    return breaksignal

def calc_ATR(price):
    T=len(price)-1
    ATR_list=[]
    for i in range(T+1):
        hml=price['high'].iloc[i]-price['low'].iloc[i]
        hmc=abs(price['high'].iloc[i]-price['close'].iloc[i-1])
        lmc=abs(price['low'].iloc[i]-price['close'].iloc[i-1])
        ATR_i=max(hml,hmc,lmc)
        ATR_list.append(ATR_i)
    ATR=mean(np.array(ATR_list))
    return ATR    

def get_unit(cash,ATR,symbol):
    future_coef_list = {'A':10, 'AG':15, 'AL':5, 'AU':1000,
                        'B':10, 'BB':500, 'BU':10, 'C':10, 
                        'CF':5, 'CS':10, 'CU':5, 'ER':10, 
                        'FB':500, 'FG':20, 'FU':50, 'GN':10, 
                        'HC':10, 'I':100, 'IC':1, 'IF':300, 
                        'IH':1, 'J':100, 'JD':5, 'JM':60, 
                        'JR':20, 'L':5, 'LR':10, 'M':10, 
                        'MA':10, 'ME':10, 'NI':1, 'OI':10, 
                        'P':10, 'PB':5, 'PM':50, 'PP':5, 
                        'RB':10, 'RI':20, 'RM':10, 'RO':10, 
                        'RS':10, 'RU':10, 'SF':5, 'SM':5, 
                        'SN':1, 'SR':10, 'T':10000, 'TA':5, 
                        'TC':100, 'TF':10000, 'V':5, 'WH':20, 
                        'WR':10, 'WS':50, 'WT':10, 'Y':10, 
                        'ZC':100, 'ZN':5}
    return (cash*0.01/ATR)/future_coef_list[symbol]

def reset():
    g.position=0    #持有头寸
    g.add=0         #加仓次数
    g.lastprice=0   #上一次成交价格
    g.markprice=0  #记录极限价格
    
########################## 获取期货合约信息，请保留 #################################
# 获取当天时间正在交易的期货主力合约
def get_future_code(symbol):
    future_code_list = {'A':'A9999.XDCE', 'AG':'AG9999.XSGE', 'AL':'AL9999.XSGE', 'AU':'AU9999.XSGE',
                        'B':'B9999.XDCE', 'BB':'BB9999.XDCE', 'BU':'BU9999.XSGE', 'C':'C9999.XDCE', 
                        'CF':'CF9999.XZCE', 'CS':'CS9999.XDCE', 'CU':'CU9999.XSGE', 'ER':'ER9999.XZCE', 
                        'FB':'FB9999.XDCE', 'FG':'FG9999.XZCE', 'FU':'FU9999.XSGE', 'GN':'GN9999.XZCE', 
                        'HC':'HC9999.XSGE', 'I':'I9999.XDCE', 'IC':'IC9999.CCFX', 'IF':'IF9999.CCFX', 
                        'IH':'IH9999.CCFX', 'J':'J9999.XDCE', 'JD':'JD9999.XDCE', 'JM':'JM9999.XDCE', 
                        'JR':'JR9999.XZCE', 'L':'L9999.XDCE', 'LR':'LR9999.XZCE', 'M':'M9999.XDCE', 
                        'MA':'MA9999.XZCE', 'ME':'ME9999.XZCE', 'NI':'NI9999.XSGE', 'OI':'OI9999.XZCE', 
                        'P':'P9999.XDCE', 'PB':'PB9999.XSGE', 'PM':'PM9999.XZCE', 'PP':'PP9999.XDCE', 
                        'RB':'RB9999.XSGE', 'RI':'RI9999.XZCE', 'RM':'RM9999.XZCE', 'RO':'RO9999.XZCE', 
                        'RS':'RS9999.XZCE', 'RU':'RU9999.XSGE', 'SF':'SF9999.XZCE', 'SM':'SM9999.XZCE', 
                        'SN':'SN9999.XSGE', 'SR':'SR9999.XZCE', 'T':'T9999.CCFX', 'TA':'TA9999.XZCE', 
                        'TC':'TC9999.XZCE', 'TF':'TF9999.CCFX', 'V':'V9999.XDCE', 'WH':'WH9999.XZCE', 
                        'WR':'WR9999.XSGE', 'WS':'WS9999.XZCE', 'WT':'WT9999.XZCE', 'Y':'Y9999.XDCE', 
                        'ZC':'ZC9999.XZCE', 'ZN':'ZN9999.XSGE','IH':'000016.XSHG','IF':'000300.XSHG','IC':'000905.XSHG'}
    try:
        return future_code_list[symbol]
    except:
        return 'WARNING: 无此合约'
     