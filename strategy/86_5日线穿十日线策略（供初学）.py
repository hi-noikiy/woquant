该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/12056

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

# 导入函数库
#5日均线大于10日均线买入
import jqdata

# 初始化函数，设定基准等等
def initialize(context):#初始化
    g.security = '601111.XSHG'# 股票名:中国国航
     # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # True为开启动态复权模式，使用真实价格交易
    #set_option('use_real_price', True) 
    
def handle_data(context, data):#每日循环
    last_price = data[g.security].close# 取得最近日收盘价
    # 取得过去二十天的平均价格
    average_price = data[g.security].mavg(20, 'close')
    #取得五天和十天的均价
    average_price5 = data[g.security].mavg(5, 'close')
    average_price10= data[g.security].mavg(10, 'close')
    
    
    cash = context.portfolio.cash# 取得当前的现金
    # 如果五日大于10日且昨日收盘价大于5日均线, 则买入，否则卖出。
    if average_price5 > average_price10:
       if last_price>average_price5:
         if cash > 100 * last_price:
           order_value(g.security, cash)# 用当前所有资金买入股票
    #昨日收盘价小于五日均价卖出       
    if last_price < average_price5:
         if context.portfolio.positions[g.security].amount > 0:
           order_target(g.security, 0)# 将股票仓位调整到0，即全卖出
