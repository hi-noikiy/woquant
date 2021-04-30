该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/13017

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

# 克隆自聚宽文章：https://www.joinquant.com/post/6596
# 标题：【新手入门教程】简单市值轮动策略
# 作者：JoinQuant-TWist

def initialize(context):
    g.stocksnum = 10 # 持有最小市值股票数
    g.period = 10 # 轮动频率
    run_daily(daily,time='every_bar')# 周期循环daily
    g.days = 1 # 记录策略进行到第几天，初始为1

def daily(context):
    # 判断策略进行天数是否能被轮动频率整除余1
    if g.days % g.period == 1:

        # 获取当前时间
        date=context.current_dt.strftime("%Y-%m-%d")
        # 获取上证指数和深证综指的成分股代码并连接，即为全A股市场所有股票
        scu = get_index_stocks('000001.XSHG')+get_index_stocks('399106.XSHE')
         # 得到是否停牌信息的dataframe，停牌的1，未停牌得0
        suspened_info_df = get_price(list(scu), start_date=context.current_dt, end_date=context.current_dt, frequency='daily', fields='paused')['paused'].T
         # 过滤停牌股票 返回dataframe
        unsuspened_index = suspened_info_df.iloc[:,0]<1
         # 得到当日未停牌股票的代码list:
        unsuspened_stocks = suspened_info_df[unsuspened_index].index
        # 选出在scu内的股票的股票代码，并按照当前时间市值从小到大排序,剔除PE为负值得股票
        df = get_fundamentals(query(
                valuation.code,valuation.market_cap,valuation.pe_ratio
            ).filter(
                valuation.code.in_(unsuspened_stocks), valuation.pe_ratio>1
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

        # 将资金分成g.stocksnum份
        position_per_stk = context.portfolio.cash/g.stocksnum
        # 用position_per_stk大小的g.stocksnum份资金去买buylist中的股票
        for stock in buylist:
            order_value(stock, position_per_stk)
    else:
        pass # 什么也不做

    g.days = g.days + 1 # 策略经过天数增加1