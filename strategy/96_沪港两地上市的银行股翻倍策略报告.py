该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/11948

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

# 导入函数库
import jqdata
import math 
import pandas as pd
from six import StringIO


#log.set_level('order', 'error')

# 初始化函数，设定要操作的股票、基准等等
def initialize(context):
    # 定义一个全局变量, 保存要操作的股票
    # 000001(股票:平安银行)
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    
   # run_monthly(handle, 1,'before_open')
    run_daily(handle)
    
    set_order_cost(OrderCost(open_tax=0, close_tax=0, open_commission=0.0003, close_commission=0.0013, close_today_commission=0, min_commission=0), type='stock')
    set_slippage(FixedSlippage(0.02))   

# 每个单位时间(如果按天回测,则每天调用一次,如果按分钟,则每分钟调用一次)调用一次
def handle(context):

    g.buylist = check_stock(context) 
    for  stock in context.portfolio.positions:
        if stock not in g.buylist:
            order_target_value(stock, 0)
            
    value = context.portfolio.total_value/len(g.buylist)
    print context.portfolio.available_cash
    for stock in g.buylist:
        
        order_target_value(stock, value )

def check_stock(context):
    date = context.current_dt.strftime('%Y-%m-%d')
    df = read_file('new1.csv')
    data = pd.read_csv(StringIO(df))
    try:
        buylist = list(data.loc[:,date])
        g.buylist = buylist
        print g.buylist
        return g.buylist
    except:
        return g.buylist
