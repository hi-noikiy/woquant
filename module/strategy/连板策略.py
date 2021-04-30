# @Time : 2021/1/26 14:54
# @Author : LiuBin
# @File : 连板策略.py
# @Description : 
# @Software: PyCharm

## 200-500市值 北上资金一直在买的

# 初始化函数，设定基准等等
def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 禁用未来函数
    # set_option("avoid_future_data", True)
    # 最大持仓股票数量
    g.max_hold = 3
    # 过滤掉order系列API产生的比error级别低的log
    log.set_level('order', 'info')
    # 输出内容到日志 log.info()
    log.info('初始函数开始运行且全局只运行一次')

    ### 股票交易相关设定 ###
    # 股票类每笔交易时的手续费是：买入时佣金万分之三，卖出时佣金万分之三加千分之一印花税, 每笔交易佣金最低扣5块钱
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.00015, close_commission=0.00015, min_commission=5),
                   type='stock')

    ## 运行函数（reference_security为运行时间的参考标的；传入的标的只做种类区分，因此传入'000300.XSHG'或'510300.XSHG'是一样的）
    # 开盘前运行
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG')
    # 开盘时运行
    run_daily(market_open, time='open', reference_security='000300.XSHG')
    run_daily(market_close, time='14:55', reference_security='000300.XSHG')
    # 收盘后运行
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')


## 开盘前运行函数
def before_market_open(context):
    # 输出运行时间
    log.info('函数运行时间(before_market_open)：' + str(context.current_dt.time()))
    # 定义全局变量
    g.date_id = BasicBag.get_current_tradeday(context)
    g.last_date_id = BasicBag.get_current_tradeday(context, 2)
    g.stocks_list = BasicBag.get_all_stocks(context, date=g.date_id, drop_new=10)
    # 给微信发送消息（添加模拟交易，并绑定微信生效）
    # send_message('美好的一天~')

    # 获得待买入股票池
    g.buy_stocks_df = FactorBag.get_continue_high_limit_stocks(g.stocks_list, end_date=g.last_date_id, n=2,
                                                                 pre_limit=True)
    # 开盘7%的价格委托
    g.buy_stocks_df['buy'] = g.buy_stocks_df['close'] * 1.07
    print(g.buy_stocks_df['buy'])
    log.info('待买入股票池：' + BasicBag.get_name(g.buy_stocks_df.index.tolist()))


## 开盘时运行函数
def market_open(context):
    log.info('函数运行时间(market_open):' + str(context.current_dt.time()))
    # 执行买入函数
    TradeBag.buy(context, g.buy_stocks_df, g.max_hold)


## 收盘前运行函数
def market_close(context):
    log.info('函数运行时间(market_close):' + str(context.current_dt.time()))
    positions = context.portfolio.positions.keys()
    sell_list = [security for security in positions if not
    FactorBag.is_on_moving_average(security, g.date_id, context=context)]
    # 执行卖出函数
    TradeBag.sell_all(context, sell_list)


## 收盘后运行函数
def after_market_close(context):
    log.info(str('函数运行时间(after_market_close):' + str(context.current_dt.time())))
    # 得到当天所有成交记录
    trades = get_trades()
    for _trade in trades.values():
        log.info('成交记录：' + str(_trade))
    log.info('##############################################################')
