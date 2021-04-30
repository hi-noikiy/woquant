该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/14860

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

# 导入函数库
import jqdata
import talib_real,bot_seller
from jqlib.technical_analysis import *

# 初始化函数，设定基准等等
def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 输出内容到日志 log.info()
    log.info('初始函数开始运行且全局只运行一次')
    # 过滤掉order系列API产生的比error级别低的log
    # log.set_level('order', 'error')
    
    ### 股票相关设定 ###
    # 股票类每笔交易时的手续费是：买入时佣金万分之三，卖出时佣金万分之三加千分之一印花税, 每笔交易佣金最低扣5块钱
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    
    g.security = '600887.XSHG'
    subscribe(g.security, 'tick')
    g.N=5
    g.QF=talib_real.QuantFactory()
    g.QF.add(talib_real.KD_Real(g.security,N=g.N,M1=3,M2=3))
    # g.QF.add(talib_real.SKDJ_Real(g.security,N=5,M=3))
    g.seller=None
    g.ready_to_buy=True
    
    
## 开盘前运行函数     
def before_trading_start(context):
    # 输出运行时间
    # log.info('函数运行时间(before_market_open)：'+str(context.current_dt.time()))
    g.QF.before_market_open(context)
    if g.seller is not None:
        g.seller.before_market_open(context)

 
## 收盘后运行函数  
def after_trading_end(context):
    log.info(str('函数运行时间(after_market_close):'+str(context.current_dt.time())))
    g.QF.after_market_close(context)
    # log.info(g.real_check.to_string())
    
    if not g.ready_to_buy:
        orders = get_orders()
        order_successful=False
        for order in orders.values():
            if order.security == g.security and order.is_buy and order.status in [OrderStatus.filled,OrderStatus.canceled,OrderStatus.rejected,OrderStatus.held] and order.filled>0:
                g.seller = bot_seller.MonkeySeller(g.security, order.price, order.filled,stop_loss=0.03,moving_stop_loss=0.03)
                order_successful=True
        if not order_successful:
            g.ready_to_buy=True
            
    if g.seller is not None:
        g.seller.after_market_close(context)
    
def handle_tick(context, tick):
    g.QF.handle_tick(context,tick)
    if g.ready_to_buy:
        buy(context)
    if g.seller is not None and g.seller.handle_tick(context,tick):
        sell(context)
        
def buy(context):
    if g.QF.check():
        accer=ACCER(g.security, check_date=context.previous_date.strftime('%Y-%m-%d'), N = g.N*2)
        if accer[g.security]<-0.005:
            # 记录这次买入
            log.info(str('买入下单时间:' + str(context.current_dt)))
            # 用所有 cash 买入股票
            order_value(g.security, context.portfolio.available_cash)
    
            g.ready_to_buy=False


def sell(context):
    # 记录这次卖出
    log.info(str('卖出下单时间:' + str(context.current_dt)+'    卖出理由：'+g.seller.sell_reason()))
    # 卖出所有股票,使这只股票的最终持有量为0
    order_target(g.security, 0)
    g.ready_to_buy=True
    g.seller=None    
    
    
    