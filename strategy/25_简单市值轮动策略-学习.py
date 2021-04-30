该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/15100

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

def initialize(context):
    """初始化函数"""
    
    # 持有最小市值股票数
    g.stocksnum = 10
    # 轮动频率
    g.period = 10
    # 记录策略进行到第几天
    g.days = 0 
    # 周期循环daily
    run_daily(daily,time='every_bar')
    

def daily(context):
    """交易函数"""
    
    # 每运行一天加一
    g.days += 1
    # 判断策略进行天数是否能被轮动频率整除余1
    if g.days % g.period != 1:
        return

    # 获取当前时间
    date=context.current_dt.strftime("%Y-%m-%d")
    # 获取上证指数和深证综指的成分股代码并连接，即为全A股市场所有股票
    # 这里股票池不放在全局中是因为总有新发型股票出现，所以要动态获取股票池
    scu = get_index_stocks('000001.XSHG') + get_index_stocks('399106.XSHE')

    # 选出在scu内的股票的股票代码，并按照当前时间市值从小到大排序
    df = get_fundamentals(query(
            valuation.code,
            valuation.market_cap
        ).filter(
            valuation.code.in_(scu)
        ).order_by(
            valuation.market_cap.asc()
        ), date=date
        )

    # 取出前g.stocksnum名的股票代码，并转成list类型，buylist为选中的股票
    buylist =list(df['code'][:g.stocksnum])

    # 对于每个当下持有的股票进行判断：现在是否已经不在buylist里，如果是则卖出
    for stock in context.portfolio.positions:
        if stock not in buylist: #如果stock不在buylist
            order_target(stock, 0) #调整stock的持仓为0，即卖出

    # 已经持仓的不会再被买入
    buy_list = list(set(buylist) - set(context.portfolio.positions.keys()))
    # 当日停牌的股票不交易
    current_data = get_current_data()
    buy_list = [stock for stock in buylist if not current_data[stock].paused]
    # 如果没有需要买进的股票，就返回
    if len(buy_list) <= 0:
        return
    # 将资金分成g.stocksnum份
    position_per_stk = context.portfolio.cash/len(buy_list)
    # 用position_per_stk大小的g.stocksnum份资金去买buylist中的股票
    for stock in buy_list:
        order_value(stock, position_per_stk)
    