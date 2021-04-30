该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/13706

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

# 导入函数库
import jqdata
from jqlib.technical_analysis import *
import datetime
import pandas as pd
import numpy as np
# 初始化函数，设定基准等等
def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 输出内容到日志 log.info()
    log.info('初始函数开始运行且全局只运行一次')
    # 过滤掉order系列API产生的比error级别低的log
    log.set_level('order', 'error')
        #send_message('推送测试')
    init_cash = 80000  # 初始资金
    set_subportfolios([SubPortfolioConfig(cash=init_cash, type='stock')])

    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)

    # 要操作的股票池：（g:global为全局变量）
    g.security = ['002241.XSHE', '000333.XSHE','002230.XSHE','002747.XSHE','002415.XSHE']
    g.holding_high_price = 0  # 持有期间最高价
    g.init_price = 0  # 股票初始价格,用于计算股票收益
    #for stk in g.security:
    # 获取股票的收盘价
    #  close_data = attribute_history(stk, 5, '1d', ['close'])
    # 取得上一时间点价格
    #  g.init_price = close_data['close'][-1]
    #history(5, security_list=['000001.XSHE', '000002.XSHE'])
    close_data = history(5,unit='1d',field='close', security_list=g.security)
    #print(close_data)
    g.init_price = close_data.iloc[-1]
    #取得初始交易日前一日所有股票收盘价格
    #print(g.init_price)
    g.maxnum = 5  # 最大持仓数
    g.lower = -2  # 下限
    g.upper = 1  # 上限
    g.zscore_window = 60  # zscore窗口
    g.ma_window = 20  # 均线窗口
    ### 股票相关设定 ###
    # 股票类每笔交易时的手续费是：买入时佣金万分之三，卖出时佣金万分之三加千分之一印花税, 每笔交易佣金最低扣5块钱
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5),
                   type='stock')
    
    ## 运行函数（reference_security为运行时间的参考标的；传入的标的只做种类区分，因此传入'000300.XSHG'或'510300.XSHG'是一样的）
      # 开盘前运行
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG') 
      # 开盘时运行
    run_daily(market_open, time='open', reference_security='000300.XSHG')
      # 收盘后运行
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')

#买入卖出信号函数
def get_buy_sell(context):
    buy, sell = [], []
    # 取得当前可用的资金
    cash = context.portfolio.available_cash
    # 设定均线窗口长度
    n1 = 5 
    #5日均线
    n2 = 10
    #10日均线
    close_data = history(5,unit='1d',field='close', security_list=g.security)
    #日交易数据
    for stk in g.security:
        # 取得上一时间点价格
        previous_price = close_data.iloc[-1][stk]
        # 画出上一时间点价格
        record(stock_price=previous_price)
        # 计算股票收益率
        stock_returns = (previous_price - g.init_price[stk]) / g.init_price[stk]
        # 画出上一时间点持股收益，方便查看，放大100倍
        record(stock_returns=stock_returns * 100)
        # 获取股票的收盘价
        close_data1 = attribute_history(stk, n2 + 2, '1d', ['close'], df=False)
        ma_n1 = close_data1['close'][-n1:].mean()
        # 取得过去 ma_n2 天的平均价格
        ma_n2 = close_data1['close'][-n2:].mean()
        hold = context.subportfolios[0].long_positions <> {}
        #print('是否持仓：')
        #print(hold)
        selladj = analysis_sell(context, stk) or ma_n1 < ma_n2
        #print('是否卖出flag：%s :' %(stk))
        #print(selladj)
        
        #判断该股是否有卖出标志位
        if hold and selladj:
            #如果有标志位则卖出
            sell.append(stk)
            print("最终判断 %s:卖出%%" % (stk))
            send_message("最终判断 %s:卖出%%" % (stk))
    #判断买入信号        
    for stk in g.security:
        
        ma_n1 = close_data1['close'][-n1:].mean()
        # 取得过去 ma_n2 天的平均价格
        ma_n2 = close_data1['close'][-n2:].mean()
        buyadj = analysis_buy(context, stk) and ma_n1 > ma_n2*0.95
        #print(analysis_buy(context, stk))
        #print(ma_n1 >= ma_n2)
        #print('是否买入flag：%s :' %(stk))
        #print(buyadj)
        if buyadj:
            buy.append(stk)
            print("最终判断 %s:买入%%" % (stk))
            send_message("最终判断 %s:买入%%" % (stk))    
    return buy, sell































## 开盘前运行函数     
def before_market_open(context):
    # 输出运行时间
    log.info('函数运行时间(before_market_open)：'+str(context.current_dt.time()))

    # 给微信发送消息（添加模拟交易，并绑定微信生效）
    print('美好的一天~')
    
    g.buy, g.sell = get_buy_sell(context)
    # 要操作的股票：平安银行（g.为全局变量）
    #g.security = '000001.XSHE'
    
## 开盘时运行函数
def market_open(context):
    log.info('函数运行时间(market_open):'+str(context.current_dt.time()))
    #security = g.security
    # 获取股票的收盘价
    #close_data = attribute_history(security, 5, '1d', ['close'])
    # 取得过去五天的平均价格
    #MA5 = close_data['close'].mean()
    # 取得上一时间点价格
    #current_price = close_data['close'][-1]
    # 取得当前的现金
    #cash = context.portfolio.available_cash
    # 先卖
    for code in g.sell:
        order_target(code, 0)
    # 再买
    
    if len(g.buy)>0 and len(context.portfolio.positions)>0:
        for stock in context.portfolio.positions:
            holdsell = context.portfolio.positions[stock].closeable_amount
            print('多股金叉卖出半仓分散持仓%s' %holdsell)
            if holdsell>100:
               order_target(stock, holdsell/2)
        
    cash_per_stock = context.portfolio.available_cash    
    if len(g.buy)>0:    
        cash_per_stock = context.portfolio.available_cash/len(g.buy) # 个股资金
    for code in g.buy:
        hold = len(context.portfolio.positions)
        # 未达到最大持仓数
        if hold < g.maxnum and cash_per_stock>8000 :
            order_target_value(code, cash_per_stock)
    print('buy: %d  sell: %d  hold: %d' % (len(g.buy), len(g.sell), len(context.portfolio.positions)))

    # 如果上一时间点价格高出五天平均价1%, 则全仓买入
    #if current_price > 1.01*MA5:
        # 记录这次买入
    #    log.info("价格高于均价 1%%, 买入 %s" % (security))
        # 用所有 cash 买入股票
    #    order_value(security, cash)
    # 如果上一时间点价格低于五天平均价, 则空仓卖出
    #elif current_price < MA5 and context.portfolio.positions[security].closeable_amount > 0:
        # 记录这次卖出
    #    log.info("价格低于均价, 卖出 %s" % (security))
        # 卖出所有股票,使这只股票的最终持有量为0
    #    order_target(security, 0)
 
## 收盘后运行函数  
def after_market_close(context):
    log.info(str('函数运行时间(after_market_close):'+str(context.current_dt.time())))
    #得到当天所有成交记录
    trades = get_trades()
    for _trade in trades.values():
        log.info('成交记录：'+str(_trade))
    log.info('一天结束')
    log.info('##############################################################')







#分析卖出函数
def analysis_sell(context, security):
    # 分析某支股票是否卖出时机
    # MACD 死叉
    # 亏损超过15%
    # 持有期间最高价下跌超过15%
    sellflag=False
    #返回值0 默认为不卖出 返回值为1则卖出该股票
    # MACD 死叉
    if isMACDDead(context, security):
        # 卖出所有股票,使这只股票的最终持有量为0
        sellflag=True 
        # 记录这次卖出
        msg_to_send = "Selling %s:macd_dead" % (security)
        log.info(msg_to_send)
        #send_message(msg_to_send, channel='weixin')

    # 亏损超过15%
    price = context.subportfolios[0].long_positions[security].price
    avg_cost = context.subportfolios[0].long_positions[security].avg_cost

    if price <> 0 and price < avg_cost * 0.93:
        # 卖出所有股票,使这只股票的最终持有量为0
        #order_target(security, 0)
        sellflag=True
        # 记录这次卖出
        msg_to_send = "Selling %s:亏损超过15%%" % (security)
        log.info(msg_to_send)
        #send_message(msg_to_send, channel='weixin')
    #均值回归Zscore卖出
    
    yesterday = context.current_dt - datetime.timedelta(1)  # 昨天
    count = g.zscore_window + g.ma_window - 1  # 2个窗口数和
    code = security
    price_df = get_price(g.security, end_date=yesterday, fields='close', count=count).close
    #if d.has_key:
    #print(price_df)
    try:
        #print('zscore断点0')
        single_df = price_df[code].to_frame('close')
        #print('zscore断点1')
        single_df['ma'] = pd.rolling_mean(single_df.close, window=g.ma_window)  # 均线
        #print('zscore断点2')
        single_df.dropna(inplace=True)
        single_df['sub'] = single_df.close - single_df.ma  # 对差值进行回归
        zscore_mean = single_df['sub'].mean(); zscore_std = single_df['sub'].std()  # 均值和标准差
        zscore_value = (single_df['sub'][-1] - zscore_mean) / zscore_std
        #print('zscore断点3')
        if zscore_value >= g.upper and price <> 0:  # 卖出
            #order_target(security, 0)# zscore值
            msg_to_send = "zscore值 %s:卖出%%" % (security)
            print('zscore值卖出')
            log.info(msg_to_send)
            sellflag=True
    except:
        pass
    # 持有期间最高价下跌超过15%
    # 先计算持有期间最高价holding_high_price
    if price == 0:
        g.holding_high_price = 0  # 无持仓
    elif price > g.holding_high_price:
        g.holding_high_price = price  # 设置股价为更高值

        if price < g.holding_high_price * 0.93:
            # 卖出所有股票,使这只股票的最终持有量为0
            #order_target(security, 0)
            # 记录这次卖出
            msg_to_send = "Selling %s:持有期间最高价下跌超过15%%" % (security)
            log.info(msg_to_send)
            sellflag=True
            #send_message(msg_to_send, channel='weixin')
    return sellflag
    # 应该卖出，但订单未成交，需要继续出售
    pass


def analysis_buy(context, security):
    # 分析某支股票是否买入时机，如是则买入
    # MACD 金叉
    buyflag=False
    #返回值0 默认为不买入 返回值为1则买入该股票
    # 取得当前可用的资金
    #cash = context.portfolio.available_cash

    # MACD 金叉
    if isMACDGold(context, security):
        buyflag=True
    # 用所有 cash 买入股票
    #    if cash > 60000:
    #        dividecash=cash/5*4
    #    else: dividecash=cash
    #    dividecash=cash    
    #    order_value(security, dividecash)
    # 记录这次买入
        msg_to_send = "Buying %s:macd_gold" % (security)
        log.info(msg_to_send)
        #send_message(msg_to_send, channel='weixin')
    return buyflag
















def isMACDGold(context, security):
    '''
    判断是否 MACD 金叉
    return True or False
    '''
    # 当天和前一个交易日的日期
    check_date = context.current_dt.strftime('%Y-%m-%d')
    previous_date = context.previous_date

    # 计算并输出 security 的 MACD 值
    macd_dif, macd_dea, macd_macd = MACD(security, check_date=check_date, SHORT=12, LONG=26, MID=9)
    previous_date_macd_dif, previous_date_macd_dea, previous_date_macd_macd = MACD(security, check_date=previous_date,
                                                                                   SHORT=12, LONG=26, MID=9)

    if previous_date_macd_macd[security] < 0 and macd_macd[security] > 0:
        return True
    else:
        return False


def isMACDDead(context, security):
    '''
    判断是否 MACD 死叉
    return True or False
    '''
    # 当天和前一个交易日的日期
    check_date = context.current_dt.strftime('%Y-%m-%d')
    previous_date = context.previous_date

    # 计算并输出 security 的 MACD 值
    macd_dif, macd_dea, macd_macd = MACD(security, check_date=check_date, SHORT=12, LONG=26, MID=9)
    previous_date_macd_dif, previous_date_macd_dea, previous_date_macd_macd = MACD(security, check_date=previous_date,
                                                                                   SHORT=12, LONG=26, MID=9)

    if previous_date_macd_macd[security] > 0 and macd_macd[security] < 0:
        return True
    else:
        return False
