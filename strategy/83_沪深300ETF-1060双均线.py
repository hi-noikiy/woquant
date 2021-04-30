# 该策略由聚宽用户分享，仅供学习交流使用。
# 原文网址：https://www.joinquant.com/post/15265
#
# 原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。
#
#
# 原文策略源码如下：

from jqdata import *

def initialize(context):
    
##### 修改股票 #####
    g.security = '510310.XSHG'
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True) 
    set_option('order_volume_ratio', 1)
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, \
                             open_commission=0.00015, close_commission=0.00015,\
                             close_today_commission=0, min_commission=5), type='stock')
    run_daily(trade, 'every_bar')


def trade(context):
    
    ##### 修改参数 #####
    security = g.security
    close_data = attribute_history(security,10, '1d', ['close'],df=False)
    ma1 = close_data['close'].mean()
    close_data = attribute_history(security,60,'1d', ['close'],df=False)
    ma2 = close_data['close'].mean()
    close_price=close_data['close'][-1]
    cash = context.portfolio.cash
    
    ##### 修改条件 #####
    if ma1 > ma2:
        order_value(security, cash)
    elif ma1 < ma2 and context.portfolio.positions[security].closeable_amount > 0:
        order_target(security, 0)

