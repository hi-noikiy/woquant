该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/12429

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

# 克隆自聚宽文章：https://www.joinquant.com/post/9184
# 标题：商品期货策略——海龟交易法
# 作者：ScintiGimcki

# 导入函数库
import jqdata
#import statsmodels.api as sm
#from statsmodels.tsa.stattools import adfuller

## 初始化函数，设定基准等等
def initialize(context):
    # 设置参数
    set_params(context)
    # 设定基准
    set_benchmark(get_future_code(g.future_index))
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 过滤掉order系列API产生的比error级别低的log
    log.set_level('order', 'error')
    # 初始化标的
    g.future = get_future_code(g.future_index)


    ### 期货相关设定 ###
    # 设定账户为期货账户
    set_subportfolios([SubPortfolioConfig(cash=context.portfolio.starting_cash, type='futures')])
    # 期货类每笔交易时的手续费是：买入时万分之0.23,卖出时万分之0.23,平今仓为万分之23
    set_order_cost(OrderCost(open_commission=0.000023, close_commission=0.000023,close_today_commission=0.0023), type='futures')
    # 设定保证金比例
    set_option('futures_margin_rate', 0.15)

    # 运行函数（reference_security为运行时间的参考标的；传入的标的只做种类区分，因此传入'IF1512.CCFX'或'IH1602.CCFX'是一样的）
      # 开盘前运行
    run_daily( before_market_open, time='before_open', reference_security=get_future_code(g.future_index))
      # 开盘时运行
    run_daily( while_open, time='open', reference_security=get_future_code(g.future_index))
      # 收盘后运行
    run_daily( after_market_close, time='after_close', reference_security=get_future_code(g.future_index))


def set_params(context):
    # 设置唐奇安通道时间窗口
    g.window = 20
    # 最大unit数目
    g.limit_unit = 6
    # 每次交易unit数目
    g.unit = 0
    # 加仓次数
    g.add_time = 0
    # 持仓状态
    g.position = 0
    # 最高价指标，用作移动止损
    g.price_mark = 0
    # 最近一次交易的合约
    g.last_future = None
    # 上一次交易的价格
    g.last_price = 0
    # 合约
    g.future_index = 'SR'
    

    
## 开盘前运行函数     
def before_market_open(context):
    ## 获取要操作的期货(g.为全局变量)
      # 获取当月期货合约
    g.future = get_dominant_future(g.future_index)
    
    
    
        
    
    
## 开盘时运行函数
def while_open(context):
    # 如果期货标的改变，重置参数
    if g.last_future == None:
        g.last_future = g.future
    elif g.last_future != g.future:
        if g.position == -1:
            order_target(g.last_future,0,side='short')
            g.position == 0
        elif g.position == 1:
            order_target(g.last_future,0,side='long')
            g.position == 0
        g.last_future = g.future
        re_set()
        log.info("主力合约改变，平仓！")
    
    # 当月合约
    future = g.future
    # 获取当月合约交割日期
    end_date = get_CCFX_end_date(future)
    # 当月合约交割日当天不开仓
    if (context.current_dt.date() == end_date):
        return
    price_list = attribute_history(future,g.window+1,'1d',['close','high','low'])
    # 如果没有数据，返回
    if len(price_list) == 0: 
        return
    close_price = price_list['close'].iloc[-1] 
    # 计算ATR
    ATR = get_ATR(price_list,g.window)
    
    ## 判断加仓或止损
      # 先判断是否持仓
    #g.position = get_position(context)
    if g.position != 0 :   
        signal = get_next_signal(close_price,g.last_price,ATR,g.position)
        # 判断加仓且持仓没有达到上限
        if signal == 1 and g.add_time < g.limit_unit:  
            g.unit = get_unit(context.portfolio.total_value,ATR,g.future_index)
            # 多头加仓
            if g.position == 1: 
                order(future,g.unit,side='long')
                log.info( '多头加仓成功:',context.current_dt.time(),future,g.unit)
                g.last_price = close_price
                g.add_time += 1
            # 空头加仓
            elif g.position == -1: 
                order(future,g.unit,side='short')
                log.info( '空头加仓成功:',context.current_dt.time(),future,g.unit)
                g.last_price = close_price
                g.add_time += 1
        # 判断平仓止损
        elif signal == -1:
            # 多头平仓
            if g.position == 1:
                order_target(future,0,side='long')
                g.price_mark = 0
                g.position = 0
                log.info( '多头止损成功:',context.current_dt.time(),future)
                log.info('----------------------------------------------------------')
            # 空头平仓
            elif g.position == -1:  
                order_target(future,0,side='short')
                g.price_mark = 0
                g.position = 0
                log.info( '空头止损成功:',context.current_dt.time(),future)
                log.info('----------------------------------------------------------')
            # 重新初始化参数
            re_set()
    
    ## 开仓
      # 得到开仓信号
    open_signal = check_break(price_list,close_price,g.window)
    # 多头开仓
    if open_signal ==1 and g.position !=1:  
        # 检测否需要空头平仓
        if g.position == -1:
            order_target(future,0,side='short')
            if context.portfolio.short_positions[future].total_amount==0:
                g.price_mark = 0
                # 重新初始化参数
                re_set()
                log.info( '空头平仓成功:',context.current_dt.time(),future)
                log.info('----------------------------------------------------------')
        # 多头开仓
        g.unit = get_unit(context.portfolio.total_value,ATR,g.future_index)
        order(future,g.unit,side='long')
        if context.portfolio.positions[future].total_amount>0:
            g.position = 1
            g.price_mark = context.portfolio.long_positions[future].price
            log.info( '多头建仓成功:',context.current_dt.time(),future,g.unit)
            log.info('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
            g.add_time = 1
            g.last_price = close_price
            g.last_future= future
    # 空头开仓
    elif open_signal == -1 and g.position != -1:
        # 检测否需要多头平仓
        if g.position == 1:
            order_target(future,0,side='long')
            if context.portfolio.positions[future].total_amount==0:
                g.price_mark = 0
                # 重新初始化参数
                re_set()
                log.info( '多头平仓成功:',context.current_dt.time(),future)
                log.info('----------------------------------------------------------')
        # 空头开仓
        g.unit = get_unit(context.portfolio.total_value,ATR,g.future_index)
        order(future,g.unit,side='short')
        if context.portfolio.short_positions[future].total_amount > 0:
            g.position = -1
            g.price_mark = context.portfolio.short_positions[future].price
            log.info( '空头建仓成功:',context.current_dt.time(),future,g.unit)
            log.info('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
            g.add_time = 1
            g.last_price = close_price
            g.last_future= future
    
    # 判断今日是否出现最高价
    if g.position != 0:
        set_price_mark(context,future)
    # 得到止损信号
    signal = get_risk_signal(context,future)
    # 止损平仓
    if signal:
        order_target(future, 0, side='short')
        order_target(future, 0, side='long')
        if context.portfolio.positions[future].total_amount==0 and context.portfolio.short_positions[future].total_amount==0:
            log.info("止损平仓!")
            g.position = 0
            g.price_mark = 0
    return
    

        
## 收盘后运行函数  
def after_market_close(context):
    pass


########################## 自定义函数 #################################
# 重置参数
def re_set():
    # 每次交易unit数目
    g.unit = 0
    # 加仓次数
    g.add_time = 0
    # 持仓状态
    g.position = 0

def check_break(price_list,price,T):
    up = max(price_list['high'].iloc[-T-1:-2])
    down = min(price_list['low'].iloc[-T-1:-2])  
    if price>up:
        return 1
    elif price<down:
        return -1
    else:
        return 0 

def get_ATR(price_list,T):
    #原版的计算ATR公式显得繁琐，修改为较简洁的表达
    #TR_list = [max(price_list['high'].iloc[i]-price_list['low'].iloc[i],abs(price_list['high'].iloc[i]-price_list['close'].iloc[i-1]),abs(price_list['close'].iloc[i-1]-price_list['low'].iloc[i])) for i in range(1,T+1)]
    TR_list = [(max(price_list['high'].iloc[i],price_list['close'].iloc[i-1]) - min(price_list['low'].iloc[i],price_list['close'].iloc[i-1])) for i in range(1,T+1)]
    ATR = np.array(TR_list).mean()
    return ATR

def get_next_signal(price,last_price,ATR,position):# 加仓或止损
    log.info( 'price:',price,'last_price:',last_price,'ATR:',ATR,'position',position)
    if (price >= last_price + 0.5*ATR and position==1) or (price <= last_price - 0.5*ATR and position==-1): # 多头加仓或空头加仓
        return 1
    elif (price <= last_price - 2*ATR and position==1) or (price >= last_price + 2*ATR and position==-1):  # 多头止损或空头止损
        return -1
    else:
        return 0
    
def get_position(context): # 0为未持仓，1为持多，-1为持空 
    try:
        tmp = context.portfolio.positions.keys()[0]
        if not context.portfolio.long_positions[tmp].total_amount and not context.portfolio.short_positions[tmp].total_amount:
            return 0
        elif context.portfolio.long_positions[tmp].total_amount:
            return 1
        elif context.portfolio.short_positions[tmp].total_amount:
            return -1
        else:
            return 0
    except:
        return 0

def get_unit(cash,ATR,symbol):
    future_coef_list = {'A':10, 'AG':15, 'AL':5, 'AU':1000,
                        'B':10, 'BB':500, 'BU':10, 'C':10, 
                        'CF':5, 'CS':10, 'CU':5, 'ER':10, 
                        'FB':500, 'FG':20, 'FU':50, 'GN':10, 
                        'HC':10, 'I':100, 'IC':200, 'IF':300, 
                        'IH':300, 'J':100, 'JD':5, 'JM':60, 
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

def set_price_mark(context,future):
    if g.position == -1:
        g.price_mark = min(context.portfolio.short_positions[future].price,g.price_mark)
    elif g.position == 1:
        g.price_mark = max(context.portfolio.long_positions[future].price,g.price_mark)
                
def get_risk_signal(context,future):
    if g.position == -1:
        if context.portfolio.short_positions[future].price >=1.05*g.price_mark:
            log.info("空头仓位止损，时间： "+str(context.current_dt.time()))
            return True
        else:
            return False
    elif g.position == 1:
        if context.portfolio.long_positions[future].price <= 0.95*g.price_mark:
            log.info("多头仓位止损，时间： "+str(context.current_dt.time()))
            return True
        else:
            return False

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
                        'ZC':'ZC9999.XZCE', 'ZN':'ZN9999.XSGE'}
    try:
        return future_code_list[symbol]
    except:
        return 'WARNING: 无此合约'


# 获取当天时间正在交易的股指期货合约
def get_stock_index_futrue_code(context,symbol,month='current_month'):
    '''
    获取当天时间正在交易的股指期货合约。其中:
    symbol:
            'IF' #沪深300指数期货
            'IC' #中证500股指期货
            'IH' #上证50股指期货
    month:
            'current_month' #当月
            'next_month'    #隔月
            'next_quarter'  #下季
            'skip_quarter'  #隔季
    '''
    display_name_dict = {'IC':'中证500股指期货','IF':'沪深300指数期货','IH':'上证50股指期货'}
    month_dict = {'current_month':0, 'next_month':1, 'next_quarter':2, 'skip_quarter':3}

    display_name = display_name_dict[symbol]
    n = month_dict[month]
    dt = context.current_dt.date()
    a = get_all_securities(types=['futures'], date=dt)
    try:
        df = a[(a.display_name == display_name) & (a.start_date <= dt) & (a.end_date >= dt)]
        return df.index[n]
    except:
        return 'WARRING: 无此合约'

# 获取当天时间正在交易的国债期货合约
def get_treasury_futrue_code(context,symbol,month='current'):
    '''
    获取当天时间正在交易的国债期货合约。其中:
    symbol:
            'T' #10年期国债期货
            'TF' #5年期国债期货
    month:
            'current' #最近期
            'next'    #次近期
            'skip'    #最远期
    '''
    display_name_dict = {'T':'10年期国债期货','TF':'5年期国债期货'}
    month_dict = {'current':0, 'next':1, 'skip':2}

    display_name = display_name_dict[symbol]
    n = month_dict[month]
    dt = context.current_dt.date()
    a = get_all_securities(types=['futures'], date=dt)
    try:
        df = a[(a.display_name == display_name) & (a.start_date <= dt) & (a.end_date >= dt)]
        return df.index[n]
    except:
        return 'WARRING: 无此合约'

# 获取金融期货合约到期日
def get_CCFX_end_date(fature_code):
    # 获取金融期货合约到期日
    return get_security_info(fature_code).end_date
