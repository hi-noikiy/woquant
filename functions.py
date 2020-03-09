# coding=utf-8
from __future__ import print_function, absolute_import

from typing import List, NoReturn, Text

from gm.api import *
from gm.csdk.c_sdk import BarLikeDict2, TickLikeDict2
from gm.model import DictLikeAccountStatus, DictLikeExecRpt, DictLikeIndicator, DictLikeOrder, DictLikeParameter
from gm.pb.account_pb2 import AccountStatus, ExecRpt, Order
from gm.pb.performance_pb2 import Indicator
from gm.pb.rtconf_pb2 import Parameter
from gm.utils import gmsdklogger

"""
本示例用于说明python sdk 当前支持的回调方法示例. 
不具有业务含义, 只用于策略编写参考
注：
建议使用python3.6.x版本, gmsdk 在 python3.6下性能更高. 
"""
"""
gmsdklogger为一个标准的 logger 对象, 可用于策略细节日志.  3.0.113 后增加
区别原有的log函数，原log用于人工查看的低频日志，
"""
gmsdklogger.info('hello world')

def init(context):
    # type: (Context) -> NoReturn
    """
    策略中必须有init方法,且策略会首先运行init定义的内容，可用于
    * 获取低频数据(get_fundamentals, get_fundamentals_n, get_instruments, get_history_instruments, get_instrumentinfos,
    get_constituents, get_history_constituents, get_sector, get_industry, get_trading_dates, get_previous_trading_date,
    get_next_trading_date, get_dividend, get_continuous_contracts, history, history_n, )
    * 申明订阅的数据参数和格式(subscribe)，并附带数据事件驱动功能
    * 申明定时任务(schedule)，附带本地时间事件驱动功能
    * 读取静态的本地数据或第三方数据
    * 定义全局常量,如 context.user_data = 'balabala'
    * 最好不要在init中下单(order_volume, order_value, order_percent, order_target_volume, order_target_value, order_target_percent)
    """

    # 示例定时任务: 每天 14:50:00 调用名字为 my_schedule_task 函数
    schedule(schedule_func=my_schedule_task, date_rule='1d', time_rule='14:50:00')

    # 定义全局常量示例
    context.user_data = 'balabala'


def my_schedule_task(context):
    # type: (Context) -> NoReturn
    """
    定时任务函数
    注意: 这类的函数可以自定义函数名, 但是只能有一个context做为参数
    """
    # 打印全局变量和运行时间点
    print(context.user_data)
    print(context.now)


def on_tick(context, tick):
    # type: (Context, TickLikeDict2) -> NoReturn
    """
    tick数据推送事件
    参数 tick 为当前被推送的tick.
    tick包含的key值有下列值.
    symbol              str                   标的代码
    open                float                 开盘价
    high                float                 最高价
    low                 float                 最低价
    price               float	              最新价
    cum_volume          long                  成交总量/最新成交量,累计值
    cum_amount          float                 成交总金额/最新成交额,累计值
    trade_type          int                   交易类型 1: ‘双开’, 2: ‘双平’, 3: ‘多开’, 4: ‘空开’, 5: ‘空平’, 6: ‘多平’, 7: ‘多换’, 8: ‘空换’
    last_volume         int                   瞬时成交量
    cum_position        int                   合约持仓量(期),累计值（股票此值为0）
    last_amount         float                 瞬时成交额
    created_at          datetime.datetime     创建时间
    receive_local_time  float             收到时的本地时间秒数. 3.0.113 后增加  注意: 内部使用
    quotes              list[Dict]            股票提供买卖5档数据, list[0]~list[4]分别对应买卖一档到五档, 期货提供买卖1档数据, list[0]表示买卖一档. 目前期货的 list[1] ~ list[4] 值是没有意义的
        quotes 里每项包含的key值有:
          bid_p:  float   买价
          bid_v:  int     买量
          ask_p   float   卖价
          ask_v   int     卖量

    注: 可以使用属性访问的方式得到相应的key的值. 如要访问: symbol. 则可以使用 tick.symbol 或 tick['symbol']
    访问quote里的bid_p, 则可以使用 tick.quotes[0].bid_p  或 tick['quotes'][0]['bid_p']
    """
    pass


def on_bar(context, bars):
    # type: (Context, List[BarLikeDict2]) -> NoReturn
    """
    bar数据推送事件
    参数 bars 为当前被推送的bar列表. 在调用subscribe时指定 wait_group=True, 则返回的是到当前已准备好的bar列表; 若 wait_group=False, 则返回的是当前推送的 bar 一个对象, 放在在 list 里
    bar 对象包含的key值有下列值.
    symbol         str      标的代码
    frequency      str      频率, 支持多种频率. 要把时间转换为相应的秒数. 如 30s, 60s, 300s, 900s
    open           float    开盘价
    close          float    收盘价
    high           float    最高价
    low            float    最低价
    amount         float    成交额
    volume         long     成交量
    position       long     持仓量（仅期货）
    bob            datetime.datetime    bar开始时间
    eob            datetime.datetime    bar结束时间
    receive_local_time  float       收到时的本地时间秒数. 3.0.113 后增加  注意: 内部使用

    注: 可以使用属性访问的方式得到相应的key的值. 如要访问: symbol. 则可以使用 bar.symbol 或 bar['symbol']
    """
    pass


def on_order_status(context, order):
    # type: (Context, DictLikeOrder) -> NoReturn
    """
    委托状态更新事件. 参数order为委托信息
    响应委托状态更新事情，下单后及委托状态更新时被触发
    """
    exchange, number = order.symbol.split(".")
    pass


def on_order_status_v2(context, order):
    # type: (Context, Order) -> NoReturn
    """
    委托状态更新事件. 参数order为委托信息
    响应委托状态更新事情，下单后及委托状态更新时被触发
    3.0.113 后增加.
    与on_order_status 具有等同含义, 在二者都被定义时(当前函数返回类型为类，速度更快，推介使用), 只会调用 on_order_status_v2
    """
    pass


def on_execution_report(context, execrpt):
    # type: (Context, DictLikeExecRpt) -> NoReturn
    """
    委托执行回报事件. 参数 execrpt 为执行回报信息
    响应委托被执行事件，委托成交后被触发
    """
    pass


def on_execution_report_v2(context, execrpt):
    # type: (Context, ExecRpt) -> NoReturn
    """
    委托执行回报事件. 参数 execrpt 为执行回报信息
    响应委托被执行事件，委托成交后被触发
    3.0.113 后增加
    已 on_execution_report 具有等同含义, 在二者都被定义时(当前函数返回类型为类，速度更快，推介使用), 只会调用 on_execution_report_v2
    """
    pass


def on_account_status(context, account_status):
    # type: (Context, DictLikeAccountStatus) -> NoReturn
    """
    交易账户状态变更事件. 仅响应 已连接，已登录，已断开 和 错误 事件
    account_status: 包含account_id(账户id), account_name(账户名),ConnectionStatus(账户状态)
    """
    pass


def on_account_status_v2(context, account_status):
    # type: (Context, AccountStatus) -> NoReturn
    """
    交易账户状态变更事件. 仅响应 已连接，已登录，已断开 和 错误 事件
    account_status: 包含account_id(账户id), account_name(账户名),ConnectionStatus(账户状态)
    3.0.113 后增加
    已 on_account_status 具有同等意义, 在二者都被定义时(当前函数返回类型为类，速度更快，推介使用), 只会调用 on_account_status_v2
    """
    pass


def on_parameter(context, parameter):
    # type: (Context, DictLikeParameter) -> NoReturn
    """
    动态参数修改事件推送. 参数 parameter 为动态参数的信息
    """
    pass


def on_parameter_v2(context, parameter):
    # type: (Context, Parameter) -> NoReturn
    """
    动态参数修改事件推送. 参数 parameter 为动态参数的信息
    3.0.113 后增加
    已 on_parameter 具有同等意义, 在二者都被定义时(当前函数返回类型为类，速度更快，推介使用), 只会调用 on_parameter_v2
    """
    pass


def on_backtest_finished(context, indicator):
    # type: (Context, DictLikeIndicator) -> NoReturn
    """
    回测结束事件. 参数 indicator 为此次回测的绩效指标参数信息

    """
    pass


def on_backtest_finished_v2(context, indicator):
    # type: (Context, Indicator) -> NoReturn
    """
    回测结束事件. 参数 indicator 为此次回测的绩效指标
    3.0.113 后增加
    已 on_backtest_finished 具有同等意义, 在二者都被定义时(当前函数返回类型为类，速度更快，推介使用), 只会调用 on_backtest_finished_v2
    """
    pass


def on_error(context, code, info):
    # type: (Context, int, Text) -> NoReturn
    """
    底层sdk出错时的回调函数
    :param context:
    :param code: 错误码.  参考: https://www.myquant.cn/docs/python/71
    :param info: 错误信息描述
    """
    pass


def on_trade_data_connected(context):
    # type: (Context) -> NoReturn
    """
    交易通道网络连接成功事件
    """
    pass


def on_market_data_connected(context):
    # type: (Context) -> NoReturn
    """
    实时行情网络连接成功事件
    """
    pass


def on_market_data_disconnected(context):
    # type: (Context) -> NoReturn
    """
    实时行情网络连接断开事件
    """
    pass


def on_trade_data_disconnected(context):
    # type: (Context) -> NoReturn
    """
    交易通道网络连接断开事件
    """
    pass


def on_shutdown(context):
    # type: (Context) -> NoReturn
    """
    策略退出前回调
    """
    pass


if __name__ == '__main__':
    run(
        strategy_id='186d88ae-2ead-11ea-bd7d-00ff5cae28c7',
        filename='main.py',
        #  从 3.0.113开始支持：filename=__file__,
        mode=MODE_BACKTEST,
        token='7255e3ed8fe47c03e01be1242a0b71c5f803c376',
        backtest_start_time='2018-11-01 13:00:00',
        backtest_end_time='2018-12-03 15:00:00')


