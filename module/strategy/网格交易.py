# @Time : 2021/1/31 0:09
# @Author : LiuBin
# @File : 网格交易.py
# @Description : 
# @Software: PyCharm

import datetime
import pandas as pd

## 200-500市值 北上资金一直在买的
from jqdata import *
from collections import defaultdict

config = {
    'user_define': {
        '002594': [163, 180, 195],  # 自定义网格
    },
    'n_grid': 4,
    'window': 120,
    'auto_define': {
        '002475': (50.5, 60.6),  # 最低价,最高价
        '600438': None  # 通过 window
    }
}


# 初始化函数，设定基准等等
def initialize(context):

    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 禁用未来函数
    # set_option("avoid_future_data", True)

    # 过滤掉order系列API产生的比error级别低的log
    log.set_level('order', 'warning')
    # 输出内容到日志 log.info()
    log.info('初始函数开始运行且全局只运行一次')
    ### 股票交易相关设定 ###
    # 股票类每笔交易时的手续费是：买入时佣金万分之三，卖出时佣金万分之三加千分之一印花税, 每笔交易佣金最低扣5块钱
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.00015, close_commission=0.00015, min_commission=5),
                   type='stock')
    # 设定沪深300作为基准
    set_benchmark('002594.XSHE')
    g.stack = {'002594.XSHE': defaultdict(int)}
    ## 运行函数（reference_security为运行时间的参考标的；传入的标的只做种类区分，因此传入'000300.XSHG'或'510300.XSHG'是一样的）
    # 开盘前运行
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG')
    # 开盘时运行
    run_daily(market_open, time='every_bar', reference_security='000300.XSHG')


## 开盘前运行函数
def before_market_open(context):
    # 输出运行时间
    log.info('函数运行时间(before_market_open)：' + str(context.current_dt.time()))
    # 定义全局变量
    g.date_id = StrategyBag.get_current_date(context)
    g.last_date_id = StrategyBag.get_current_date(context, 1)
    # 给微信发送消息（添加模拟交易，并绑定微信生效）
    # send_message('美好的一天~')
    g.stocks = {'002594.XSHE': (163.59, 192.57)}
    g.per_amount = {'002594.XSHE': 200}
    g.n_grid = 3
    # 获得待买入股票池
    g.buy_stocks = GridTrade.get_grid_info(g.stocks, n_grid=g.n_grid, context=context)
    close_price = history(1, field='close', security_list=g.buy_stocks.keys()).iloc[0]
    g.state = GridTrade.check_grid_state(g.buy_stocks, close_price)

    log.info('待买入股票池：' + str(g.buy_stocks))
    log.info('当前状态' + str(g.state))


## 开盘时运行函数
def market_open(context):
    log.info('函数运行时间(market_open):' + str(context.current_dt.time()))
    buy_signal, sell_signal, new_state = GridTrade.grid_trade_signal(g.buy_stocks, g.state)
    if buy_signal:
        print(g.stack)
        for security in buy_signal:
            if g.stack[security][new_state[security]] == 0 and GridTrade.buy(context, security, g.per_amount[security]):
                g.state[security] = new_state[security]
                g.stack[security][new_state[security]] = g.per_amount[security]

    if sell_signal:
        print(g.stack)
        for security in sell_signal:
            if g.stack[security][g.state[security] - 1] >= g.per_amount[security]:
                GridTrade.sell(context, security, g.stack[security][g.state[security] - 1])
                g.state[security] = new_state[security]
                g.stack[security][g.state[security]] = 0


class GridTrade:
    @staticmethod
    def grid_generator(security, n_grid=3, window=60, max_price=None, min_price=None, context=None):
        """
        网格交易法:栅格生成器
        :param security:
        :param n_grid: 网格行数
        :param window: 如果未指定最高价或最低价,考察最高价和最低价的交易周期
        :param max_price:
        :param min_price:
        :param context:
        :return: 返回n_grid个价格，即n_grid-1个价格区间
        """

        start_date = StrategyBag.get_current_date(context, days=window - 1)
        end_date = StrategyBag.get_current_date(context)
        if max_price is None:
            max_price = get_price(security, start_date=start_date, end_date=end_date, fields=['close'])['close'].max()
        if min_price is None:
            min_price = get_price(security, start_date=start_date, end_date=end_date, fields=['close'])['close'].min()
        assert max_price > min_price, "参数异常 max_price <= min_price"
        step = (max_price - min_price) / (n_grid - 1)
        return [round(i, 2) for i in list(np.arange(min_price, max_price + 0.001, step))]

    @staticmethod
    def get_grid_info(security_list, n_grid=3, window=60, context=None):
        """
        获得股票集合的网格信息DataFrame
        :param security_list: 字典/列表
        :param n_grid:
        :param window:
        :param context:
        :return:
        """
        d = {}
        for security in security_list:
            if isinstance(security_list, dict):
                min_price, max_price = security_list[security]
                d[security] = GridTrade.grid_generator(security, n_grid=n_grid, window=window, max_price=max_price,
                                                       min_price=min_price, context=context)
            else:
                d[security] = GridTrade.grid_generator(security, n_grid=n_grid, window=window, context=context)
        return pd.DataFrame(d)

    @staticmethod
    def check_grid_state(security_grid_df, current_price=None):
        if current_price is None:
            current_price = pd.Series(
                security_grid_df.columns.map(lambda security: get_current_data()[security].last_price),
                index=security_grid_df.columns)
        state = len(security_grid_df) - (security_grid_df > current_price).sum(axis=0)
        bottom = state[state == 0].index.tolist()
        top = state[state == len(security_grid_df)].index.tolist()
        if bottom:
            print('股票已击穿网格最低价格' + str(bottom))
        if top:
            print('股票已击穿网格最高价格' + str(top))
        return state

    @staticmethod
    def grid_trade_signal(security_grid_df, state, ):
        """
        【回测/模拟】获取交易信号
        :param security_grid_df: row_index:区间索引,column_index:股票名称,value:grid_price
        :param state: index:股票名称,value:当前价格所在区间索引
        :return:
        """
        new_state = GridTrade.check_grid_state(security_grid_df)
        buy_signal = new_state[new_state < state].index.tolist()
        sell_signal = new_state[new_state > state].index.tolist()
        return buy_signal, sell_signal, new_state

    @staticmethod
    def buy(context, security, amount):
        cash = context.portfolio.available_cash
        if cash / get_current_data()[security].last_price > amount and order(security, amount):
            log.warning('买入标的 ' + security)
            return True
        else:
            log.warning('资金不足 ' + security)
            return False

    @staticmethod
    def sell(context, security, amount):
        position = context.portfolio.positions[security]
        if position.closeable_amount >= amount and order(security, -1 * amount):
            log.warning('卖出标的 ' + security)
            return True
        else:
            log.warning('无可卖仓位 ' + security)
            return False
