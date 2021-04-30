该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/15815

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

# 期货日频多品种，MA双均线+百分比追踪止损
# 建议给予1000000元，2012年1月1日至今回测
# 导入函数库
from jqdata import * 
import talib
from math import isnan

def initialize(context):
    # 设置参数
    set_parameter(context)
    # 设定基准银华日利，在多品种的回测当中基准没有参考意义
    set_benchmark('511880.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 过滤掉order系列API产生的比error级别低的log
    log.set_level('order', 'error')
    ### 期货相关设定 ###
    # 设定账户为金融账户
    set_subportfolios([SubPortfolioConfig(cash=context.portfolio.starting_cash, type='futures')])
    # 期货类每笔交易时的手续费是：买入时万分之1,卖出时万分之1,平今仓为万分之1
    set_order_cost(OrderCost(open_commission=0.0001, close_commission=0.0001,close_today_commission=0.0001), type='index_futures')
    # 设定保证金比例
    set_option('futures_margin_rate', 0.15)
    # 设置滑点（单边万5，双边千1）
    set_slippage(PriceRelatedSlippage(0.001),type='future')
    # 开盘前运行
    run_daily( before_market_open, time='before_open', reference_security=get_future_code('RB'))
    # 开盘时运行
    run_weekly(market_open, 1,time='open', reference_security=get_future_code('RB'))
#    run_monthly(market_open, 11,time='open', reference_security=get_future_code('RB'))
    # 交易运行 
    # 交易运行 
    run_weekly(Trade, 1, time='open', reference_security=get_future_code('RB'))
#    run_monthly(Trade, 11, time='open', reference_security=get_future_code('RB'))
    # 收盘后运行
    run_daily( after_market_close, time='after_close', reference_security=get_future_code('RB'))
    
    
    

   # 参数设置函数
def set_parameter(context):
    
    #######变量设置########
    g.LastRealPrice = {} # 最新真实合约价格字典(用于吊灯止损）
    g.HighPrice = {} # 各品种最高价字典（用于吊灯止损）
    g.LowPrice = {} # 各品种最低价字典（用于吊灯止损）
    g.future_list = []  # 设置期货品种列表
    g.TradeLots = {}  # 各品种的交易手数信息
    g.PriceArray = {} # 信号计算价格字典
    g.Price_dict = {} # 各品种价格列表字典
    g.Times = {} # 计数器（用于防止止损重入）
    g.Reentry_long = False # 止损后重入标记
    g.Reentry_short = False # 止损后重入标记
    g.MappingReal = {} # 真实合约映射（key为symbol，value为主力合约）
    g.MappingIndex = {} # 指数合约映射 （key为 symbol，value为指数合约
    g.StatusTimer = {} # 当前状态计数器
    g.ATR = {}
    g.CurrentPrice = {}
    g.Price_DaysAgo = {}
    g.Momentum = {}
    g.ClosePrice = {}

    #######参数设置########
    g.BackWindow = 15 # 回溯窗口长度
    g.Range = 0.3
    # 交易的期货品种信息
    g.instruments = ['AL','NI','CU','PB','AG',
                    'RU','MA','PP','TA','L','V',
                    'M','P','Y','OI','C','CS','JD','SR',
                    'HC','J','I','SF','RB','ZC','FG']
    # 价格列表初始化
    set_future_list(context)


def set_future_list(context):
    for ins in g.instruments:
        idx = get_future_code(ins)
        dom = get_dominant_future(ins)
        # 填充映射字典
        g.MappingIndex[ins] = idx
        g.MappingReal[ins] = dom
        g.StatusTimer[ins] = 0
        #设置主力合约已上市的品种基本参数
        if dom == '':
            pass
        else:
            if dom not in g.future_list:
                g.future_list.append(dom)
                g.HighPrice[dom] = False
                g.LowPrice[dom] = False
                g.Times[dom] = 0
                

'''
换月模块逻辑（ins是期货品种的symbol（如‘RB’），dom或future指合约（如'RB1610.XSGE'）,idx指指数合约（如’RB8888.XSGE‘）
    1.在第一天开始时，将所有期货品种最初的主力合约写入MappingReal与MappingIndex当中
    2.每天开盘获取一遍ins对应的主力合约，判断是否在MappingReal中，若不在，则执行replace模块
    3.replace模块中，卖出原来持有的主力合约，等量买入新合约；修改MappingReal
'''
## 开盘前运行函数
def before_market_open(context):
    # 输出运行时间
    log.info('函数运行时间(before_market_open)：'+str(context.current_dt.time()))
    send_message('开始交易')
    
    # 过滤无主力合约的品种，传入并修改期货字典信息
    for ins in g.instruments:
        dom = get_dominant_future(ins)
        if dom == '':
            pass
        else:
            # 判断是否执行replace_old_futures
            if dom == g.MappingReal[ins]:
                pass
            else:
                replace_old_futures(context,ins,dom)
                g.future_list.append(dom)
                g.HighPrice[dom] = False
                g.LowPrice[dom] = False
                g.Times[dom] = 0
        
            g.TradeLots[dom] = get_lots(context.portfolio.starting_cash/len(g.instruments),ins)
            

## 开盘时运行函数
def market_open(context):
    # 输出函数运行时间
    #log.info('函数运行时间(market_open):'+str(context.current_dt.time()))
    # 以下是主循环
    for ins in g.instruments:
        # 过滤空主力合约品种
        if g.MappingReal[ins] != '':
            IndexFuture = g.MappingIndex[ins]
            RealFuture = g.MappingReal[ins]
            # 获取当月合约交割日期
            end_date = get_CCFX_end_date(RealFuture)
            # 当月合约交割日当天不开仓
            if (context.current_dt.date() == end_date):
                return
            else:
                g.LastRealPrice[RealFuture] = attribute_history(RealFuture,1,'1d',['close'])['close'][-1]
                # 获取价格list
                #if g.StatusTimer[ins] == 0:
                g.PriceArray[IndexFuture] = attribute_history(IndexFuture,g.BackWindow+5,'1d',['close','open','high','low'])
                
                # 如果没有数据，返回
                if len(g.PriceArray[IndexFuture]) < 1:
                    return
                else: 
                    g.ClosePrice[ins] = g.PriceArray[IndexFuture]['close']
                    g.CurrentPrice[ins] = g.ClosePrice[ins][-1]
                    g.Price_DaysAgo[ins] = g.ClosePrice[ins][-g.BackWindow]
                    
                    g.close = np.array(g.PriceArray[IndexFuture]['close'])
                    g.high = np.array(g.PriceArray[IndexFuture]['high'])
                    g.low = np.array(g.PriceArray[IndexFuture]['low'])
                    g.ATR[IndexFuture] = talib.ATR(g.high,g.low,g.close, g.BackWindow)[-1]
                    
                    # g.Momentum[ins] = g.CurrentPrice[ins]/g.Price_DaysAgo[ins] -1
                    g.Momentum[ins] = g.CurrentPrice[ins]/g.Price_DaysAgo[ins] -1

                    
                    
                    

           
## 收盘后运行函数
def after_market_close(context):
    log.info(str('函数运行时间(after_market_close):'+str(context.current_dt.time())))
    # 得到当天所有成交记录
    trades = get_trades()
    for _trade in trades.values():
        log.info('成交记录：'+str(_trade))
    log.info('一天结束')
    log.info('##############################################################')
    
## 交易模块 
def Trade(context):
    # 定义每周买卖的列表
    log.info(g.ClosePrice.keys())
    BuyList = []
    SellList = []
    # 将字典进行排序，并将数值前五品种的symbol写入列表
    a = sorted(g.Momentum.items(), key=lambda x: x[1],reverse = True)
    for i in range(int(g.Range*len(g.MappingReal.keys()))):
        BuyList.append(a[i][0])
        SellList.append(a[-i-1][0])
       
        
    for ins in g.instruments:
        RealFuture = g.MappingReal[ins]
        IndexFuture = g.MappingIndex[ins]
        if RealFuture in g.LastRealPrice.keys():
            if ins in BuyList and context.portfolio.long_positions[RealFuture].total_amount == 0:
                if context.portfolio.long_positions[RealFuture].total_amount != 0:
                    log.info('空头有持仓：%s'%(RealFuture))
                order_target(RealFuture,0,side='short')
                order_target(RealFuture,g.TradeLots[RealFuture],side='long')
                g.HighPrice[RealFuture] = g.LastRealPrice[RealFuture]
                g.LowPrice[RealFuture] = False
                log.info('正常买多合约：%s'%(RealFuture))
        
            elif ins in SellList and context.portfolio.short_positions[RealFuture].total_amount == 0:
                if context.portfolio.short_positions[RealFuture].total_amount != 0:
                    log.info('多头有持仓：%s'%(RealFuture))
                order_target(RealFuture,0,side ='long')
                order_target(RealFuture,g.TradeLots[RealFuture],side='short')
                g.LowPrice[RealFuture] = g.LastRealPrice[RealFuture]
                g.HighPrice[RealFuture] = False
                log.info('正常卖空合约：%s'%(RealFuture))
            elif ins not in BuyList and RealFuture in context.portfolio.long_positions.keys():
                order_target(RealFuture,0,side ='long')
            elif ins not in SellList and RealFuture in context.portfolio.short_positions.keys():
                order_target(RealFuture,0,side ='short')
            else:
                TrailingStop(context,RealFuture,IndexFuture)
         #防重入模块yunxi
        Dont_Re_entry(context,RealFuture,ins)     

        
        
# 追踪止损后,防止立刻重入模块
# 因为追踪止损条件领先于金叉死叉，所以在止损后，要防止系统再次高位入场
def Dont_Re_entry(context,future,ins):
    # 防重入模块：上一次止损后20根bar内不交易，但如果出现价格突破事件则20根bar的限制失效
    #设置最高价与最低价（注意：需要错一位，不能算入当前价格）
    if ins in g.ClosePrice.keys():
        g.Highest_high_2_20 = g.ClosePrice[ins][-21:-1].max()
        g.Lowest_low_2_20 = g.ClosePrice[ins][-21:-1].min()
    
        if  g.Reentry_long == True:
            if g.Times[future] > 20 or g.CurrentPrice[ins] > g.Highest_high_2_20 :
                g.Reentry_long = False
        if  g.Reentry_short == True:
            if g.Times[future] > 20 or g.CurrentPrice[ins] < g.Lowest_low_2_20 :
                g.Reentry_short = False
        

# 追踪止损模块（百分比止损）
def TrailingStop(context,RealFuture,IndexFuture):
    
    # 记录多空仓位
    long_positions = context.portfolio.long_positions
    short_positions = context.portfolio.short_positions
    
    # 通过for循环逐一平仓（多头）
    if RealFuture in long_positions.keys():
        if long_positions[RealFuture].total_amount > 0:
            if g.HighPrice[RealFuture]:
                g.HighPrice[RealFuture] = max(g.HighPrice[RealFuture], g.LastRealPrice[RealFuture])
                if g.LastRealPrice[RealFuture]  < g.HighPrice[RealFuture]-g.ATR[IndexFuture]:
                    log.info('多头止损:\t' +  RealFuture)
                    order_target(RealFuture,0,side = 'long')
                    g.Reentry_long = True
                    
    # 通过for循环逐一平仓（空头）
    if RealFuture in short_positions.keys():
        if short_positions[RealFuture].total_amount > 0:
            if g.LowPrice[RealFuture]:
                g.LowPrice[RealFuture] = min(g.LowPrice[RealFuture], g.LastRealPrice[RealFuture])
                if g.LastRealPrice[RealFuture]  > g.LowPrice[RealFuture]+g.ATR[IndexFuture]:
                    log.info('空头止损:\t' + RealFuture)
                    order_target(RealFuture,0,side = 'short')
                    g.Reentry_short = True



# 移仓模块：当主力合约更换时，平当前持仓，更换为最新主力合约        
def replace_old_futures(context,ins,dom):
    
    LastFuture = g.MappingReal[ins]
    
    if LastFuture in context.portfolio.long_positions.keys():
        lots_long = context.portfolio.long_positions[LastFuture].total_amount
        order_target(LastFuture,0,side='long')
        order_target(dom,lots_long,side='long')
        print('主力合约更换，平多仓换新仓')
    
    if LastFuture in context.portfolio.short_positions.keys():
        lots_short = context.portfolio.short_positions[dom].total_amount
        order_target(LastFuture,0,side='short')
        order_target(dom,lots_short,side='short')
        print('主力合约更换，平空仓换新仓')

    g.MappingReal[ins] = dom     
            
'''增加删除过去合约'''
        
        
# 获取当天时间正在交易的期货主力合约函数
def get_future_code(symbol):
    future_code_list = {'A':'A8888.XDCE', 'AG':'AG8888.XSGE', 'AL':'AL8888.XSGE', 'AU':'AU8888.XSGE',
                        'B':'B8888.XDCE', 'BB':'BB8888.XDCE', 'BU':'BU8888.XSGE', 'C':'C8888.XDCE', 
                        'CF':'CF8888.XZCE', 'CS':'CS8888.XDCE', 'CU':'CU8888.XSGE', 'ER':'ER8888.XZCE', 
                        'FB':'FB8888.XDCE', 'FG':'FG8888.XZCE', 'FU':'FU8888.XSGE', 'GN':'GN8888.XZCE', 
                        'HC':'HC8888.XSGE', 'I':'I8888.XDCE', 'IC':'IC8888.CCFX', 'IF':'IF8888.CCFX', 
                        'IH':'IH8888.CCFX', 'J':'J8888.XDCE', 'JD':'JD8888.XDCE', 'JM':'JM8888.XDCE', 
                        'JR':'JR8888.XZCE', 'L':'L8888.XDCE', 'LR':'LR8888.XZCE', 'M':'M8888.XDCE', 
                        'MA':'MA8888.XZCE', 'ME':'ME8888.XZCE', 'NI':'NI8888.XSGE', 'OI':'OI8888.XZCE', 
                        'P':'P8888.XDCE', 'PB':'PB8888.XSGE', 'PM':'PM8888.XZCE', 'PP':'PP8888.XDCE', 
                        'RB':'RB8888.XSGE', 'RI':'RI8888.XZCE', 'RM':'RM8888.XZCE', 'RO':'RO8888.XZCE', 
                        'RS':'RS8888.XZCE', 'RU':'RU8888.XSGE', 'SF':'SF8888.XZCE', 'SM':'SM8888.XZCE', 
                        'SN':'SN8888.XSGE', 'SR':'SR8888.XZCE', 'T':'T8888.CCFX', 'TA':'TA8888.XZCE', 
                        'TC':'TC8888.XZCE', 'TF':'TF8888.CCFX', 'V':'V8888.XDCE', 'WH':'WH8888.XZCE', 
                        'WR':'WR8888.XSGE', 'WS':'WS8888.XZCE', 'WT':'WT8888.XZCE', 'Y':'Y8888.XDCE', 
                        'ZC':'ZC8888.XZCE', 'ZN':'ZN8888.XSGE','AP':'AP8888.XZCE'}
    try:
        return future_code_list[symbol]
    except:
        return 'WARNING: 无此合约'


# 获取交易手数函数（ATR倒数头寸）
def get_lots(cash,symbol):
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
                        'ZC':100, 'ZN':5,'AP':10}
    RealFuture = get_dominant_future(symbol)
    IndexFuture = get_future_code(symbol)
    # 获取价格list
    Price_dict = attribute_history(IndexFuture,10,'1d',['open'])
    # 如果没有数据，返回
    if len(Price_dict) == 0:
        return
    else:
        open_future = Price_dict.iloc[-1]
    # 返回手数
    if IndexFuture in g.ATR.keys():
        # 每次使用10%资金开仓交易
        # 合约价值的表达式是：g.ATR[IndexFuture]*future_coef_list[symbol]
        return cash*0.1/(g.ATR[IndexFuture]*future_coef_list[symbol])
    else:# 函数运行之初会出现没将future写入ATR字典当中的情况
        return cash*0.0001/future_coef_list[symbol]


# # 获取交易手数函数(无ATR版本）
# def get_lots(cash,symbol):
#     # 获取合约规模(Contract Size)，也称交易单位
#     future_Contract_Size = {'A':10, 'AG':15, 'AL':5, 'AU':1000,
#                         'B':10, 'BB':500, 'BU':10, 'C':10,
#                         'CF':5, 'CS':10, 'CU':5, 'ER':10,
#                         'FB':500, 'FG':20, 'FU':50, 'GN':10,
#                         'HC':10, 'I':100, 'IC':200, 'IF':300,
#                         'IH':300, 'J':100, 'JD':5, 'JM':60,
#                         'JR':20, 'L':5, 'LR':10, 'M':10,
#                         'MA':10, 'ME':10, 'NI':1, 'OI':10,
#                         'P':10, 'PB':5, 'PM':50, 'PP':5,
#                         'RB':10, 'RI':20, 'RM':10, 'RO':10,
#                         'RS':10, 'RU':10, 'SF':5, 'SM':5,
#                         'SN':1, 'SR':10, 'T':10000, 'TA':5,
#                         'TC':100, 'TF':10000, 'V':5, 'WH':20,
#                         'WR':10, 'WS':50, 'WT':10, 'Y':10,
#                         'ZC':100, 'ZN':5,'AP':10}
#     future = get_dominant_future(symbol)
#     # 获取价格list
#     Price_dict = attribute_history(future,10,'1d',['open'])
#     # 如果没有数据，返回
#     if len(Price_dict) == 0:
#         return
#     else:
#         # 获得最新开盘价，计算能够下单多少手
#         open_price = Price_dict.iloc[-1]
#     # 返回手数（价格*合约规模=名义价值）
#     # 保证金使用，控制在33%
#     # 合约保证金的表达式是：open_price*future_Contract_Size[symbol]*g.MarginRate
#     return cash*0.33/(open_price*future_Contract_Size[symbol]*g.MarginRate)


# 获取金融期货合约到期日
def get_CCFX_end_date(fature_code):
    # 获取金融期货合约到期日
    return get_security_info(fature_code).end_date