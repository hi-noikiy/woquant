该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/11681

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

# 导入函数库
import jqdata
import math 
import pandas as pd


log.set_level('order', 'error')

# 初始化函数，设定要操作的股票、基准等等
def initialize(context):
    # 定义一个全局变量, 保存要操作的股票
    # 000001(股票:平安银行)
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    
    run_monthly(handle, 1,'before_open')
    set_order_cost(OrderCost(open_tax=0, close_tax=0, open_commission=0.0003, close_commission=0.0013, close_today_commission=0, min_commission=0), type='stock')
    set_slippage(FixedSlippage(0.02))   

# 每个单位时间(如果按天回测,则每天调用一次,如果按分钟,则每分钟调用一次)调用一次
def handle(context):

    buylist = check_stock(context) 
   
    for  stock in context.portfolio.positions:
        if stock not in buylist:
            order_target_value(stock, 0)
   
    for stock in buylist:
        order_target_value(stock, context.portfolio.total_value/len(buylist))

def check_stock(context):
    
    stock_list =['000001.XSHE', '002142.XSHE', '002807.XSHE', '002839.XSHE', '600000.XSHG', '600015.XSHG', '600016.XSHG', '600036.XSHG', '600908.XSHG', '600919.XSHG', '600926.XSHG', '601009.XSHG', '601128.XSHG', '601166.XSHG', '601169.XSHG', '601229.XSHG', '601288.XSHG', '601328.XSHG', '601398.XSHG', '601818.XSHG', '601838.XSHG', '601939.XSHG', '601988.XSHG', '601997.XSHG', '601998.XSHG', '603323.XSHG']
    df=pd.DataFrame(index =stock_list, columns =['ROE','PB'])
    for stk1 in stock_list:
        P = get_fundamentals_continuously(query(indicator.code, valuation.pb_ratio).filter(valuation.code==stk1),count=250)
        RO = get_fundamentals_continuously(query(indicator.code, indicator.roe).filter(valuation.code==stk1),count=250)
        df['PB'][stk1]=P['pb_ratio'].values.mean()
        df['ROE'][stk1] = RO['roe'].values.mean()/100
      
    df = df[df['ROE'] > -1]
    
    
    
    df["double_time"] =  df.apply(lambda row: round(math.log(2.0 * row['PB'] , (1.0+row['ROE'])),2), axis=1)
    #翻倍期最小的银行股
    df = df.sort("double_time")

    print context.current_dt.strftime('%Y-%m-%d') +' 选股为 '+ str(df.index[:5].values)[1:-1]
    return df.index[:5]#这里的数字表示买入的标的 数量，默认是5


