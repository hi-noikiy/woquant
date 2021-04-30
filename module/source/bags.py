# @Time : 2021/3/21 0:17
# @Author : LiuBin
# @File : bags.py
# @Description : 
# @Software: PyCharm

import pandas as pd
from typing import List, Union
from datetime import datetime
from sqlalchemy.orm.query import Query
import jqdata as jq


class BasicBag(object):

    @staticmethod
    def normalize_code(stock_code: str) -> str:
        """
        规范化为聚宽格式的代码
        :param stock_code:  000001
        :return:  000001.XSHE
        """
        return jq.normalize_code(stock_code)

    @staticmethod
    def get_name(stock_code: Union[str, List[str]]) -> str:
        """
        获得股票中文名称，返回一个字符串
        :param stock_code: list/str
        :return: str
        """
        if isinstance(stock_code, str):
            name = get_security_info(stock_code).display_name
        else:
            name = ' , '.join([get_security_info(code).display_name for code in stock_code])
        return name

    @staticmethod
    def current_minute(context=None):
        """
        当前时间戳
        :return:
        """
        return context.current_dt.now() if context else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def current_date(context=None):
        current_date = context.current_dt.date() if context else datetime.today()
        return current_date

    @staticmethod
    def get_current_tradeday(context=None, end_date=None, days: int = 0, ret_first=True):
        """
        获取最近N个交易日
        :return:
        """
        if context: end_date = context.current_dt.date()
        trade_days = jq.get_trade_days(end_date=end_date, count=days+1)
        return trade_days[0] if ret_first else trade_days

    @staticmethod
    def get_price(stock, fields: Union[str, List[str]] = 'close', start_date=None, end_date=None, count=None,
                  frequency='1d', context=None):
        """
        获得股票价格,若未指定日期,默认为当天
        :param stock:
        :param felds: ['open', 'close', 'low', 'high', 'volume', 'money',
                        'factor', 'high_limit', 'low_limit', 'avg', 'pre_close', 'paused']
        :param start_date:
        :param end_date:
        :param count:
        :param frequency: 单位时间长度, 几天或者几分钟, 现在支持'Xd','Xm'
        :return:
        """
        if isinstance(fields, str):
            fields = [fields]
        if not end_date:
            end_date = BasicBag.current_date(context)
        return get_price(stock,
                         start_date=start_date,
                         end_date=end_date,
                         count=count,
                         fields=fields,
                         frequency=frequency,
                         panel=False
                         )

    @staticmethod
    def get_realtime_price(stock, context=None):
        """
        获得股票实时(前一分钟)价格
        :param stock:
        :return:
        """
        return BasicBag.get_price(stock,
                                  end_date=BasicBag.current_minute(context),
                                  count=1,
                                  frequency='1m', context=context).iloc[0, 0]

    @staticmethod
    def get_all_stocks(context=None, date=None, drop_new=30, drop_st=True, max_circulating_market_cap=None,
                       min_circulating_market_cap=None,
                       display_name=False):
        """
        获得基础股票池
        :param date_id:
        :param drop_new:
        :param drop_st:
        :return:
        """
        if not date:
            date = BasicBag.get_current_tradeday(context)
        # 获取所有股票列表
        all_security_df = get_all_securities(date=date)
        # 过滤掉当天退市股
        all_security_df = all_security_df[all_security_df.end_date.astype(str) > str(date)]
        # 过滤掉上市30天以内的次新股，如果是负数则保留abs(drop_new)天内的次新股
        start_date = BasicBag.get_current_tradeday(context, days=abs(drop_new))
        if drop_new >= 0:
            all_security_df = all_security_df[all_security_df.start_date.astype(str) < str(start_date)]
        else:
            all_security_df = all_security_df[all_security_df.start_date.astype(str) > str(start_date)]
        # 过滤掉ST股
        if drop_st:
            is_st = get_extras("is_st", all_security_df.index.tolist(), end_date=date, count=1).T.iloc[:, 0]
            all_security_df = all_security_df[~is_st]
        if max_circulating_market_cap or min_circulating_market_cap:
            all_security_df = BasicBag.get_market_cap(all_security_df, date)
            if max_circulating_market_cap:
                all_security_df = all_security_df[
                    all_security_df['circulating_market_cap'] <= max_circulating_market_cap]
            if min_circulating_market_cap:
                all_security_df = all_security_df[
                    all_security_df['circulating_market_cap'] >= min_circulating_market_cap]
        # 获取最终股票列表
        return all_security_df.index.tolist() if not display_name else all_security_df.display_name.tolist()

    @staticmethod
    def get_market_cap(security: Union[str, List[str], pd.DataFrame], date=None, circulation=True):
        """
        获取市值(流通市值)数据
        :param security:  字符串 、 列表 、 DataFrame
        :param date:
        :param circulation: 是否流通市值
        :return:  数值 、 字典 、 DataFrame
        """
        if not date:
            date = BasicBag.get_current_tradeday()
        if isinstance(security, str):
            security_list = [security]
        elif isinstance(security, pd.DataFrame):
            security_list = security.index.tolist()
        elif isinstance(security, list):
            security_list = security
        else:
            raise TypeError("security parameter type is error")
        q = Query(jq.valuation).filter(jq.valuation.code.in_(security_list))
        df = jq.get_fundamentals(q, date)
        # 打印出总市值
        key = 'circulating_market_cap' if circulation else 'market_cap'
        if isinstance(security, pd.DataFrame):
            return pd.concat([security.reset_index(), df[key]], axis=1).set_index("index")
        elif isinstance(security, str):
            return df[key][0].item()
        else:
            return dict(zip(security, df[key].values.tolist()))


class TradeBag(object):

    @staticmethod
    def cancel_open_orders():
        """
        撤掉未成交订单
        :return:
        """
        # 得到当前未完成订单
        orders = get_open_orders()
        # 循环，撤销订单
        for _order in orders.values():
            cancel_order(_order)

    @staticmethod
    def sell_all(context, sell_stocks):
        """
        交易函数 - 卖出 (回测/模拟有效)
        :param context:
        :param sell_stocks: 待卖出股票列表
        :return:
        """
        sell_list = set(context.portfolio.positions.keys()).intersection(set(sell_stocks))
        for security in sell_list:
            order_target_value(security, 0)
            log.info('卖出股票 {}'.format(BasicBag.get_name(security)))

    @staticmethod
    def buy(context, buy_stocks, max_hold=5, min_amount=1_0000, cancel_order=True):
        """
        交易函数 - 买入 (回测/模拟有效)
        :param buy_stocks: 待买入股票DataFrame
        :param max_num: 最大买入数量，按DataFrame顺序下单
        :return:
        """
        assert context is not None
        # 持仓股票数量
        hold_len = len(context.portfolio.positions)
        # 可用现金
        cash = context.portfolio.available_cash
        # 总资产
        total_value = context.portfolio.total_value

        # 现金可买入股票数
        per_stock_amount = total_value / max_hold
        buy_num = cash // per_stock_amount
        if cash % per_stock_amount >= min_amount:
            buy_num += 1
        buy_num = min(min(max(max_hold - hold_len, 0), buy_num), len(buy_stocks))
        if isinstance(buy_stocks, pd.DataFrame):
            for security, info in buy_stocks[:buy_num].iterrows():
                amount = min(cash, per_stock_amount)
                log.info('买入 {} , 花费 {} 元 '.format(BasicBag.get_name(security), amount))
                ## 如果指定买入价格，设置限价单
                if 'buy' in buy_stocks.columns:
                    order_target_value(security, amount, LimitOrderStyle(info['buy']))
                else:
                    order_target_value(security, amount)
                cash -= amount
        else:
            for security in buy_stocks[:buy_num]:
                amount = min(cash, per_stock_amount)
                log.info('买入 {} , 花费 {} 元 '.format(BasicBag.get_name(security), amount))
                order_target_value(security, amount)
                cash -= amount

        cancel_order and TradeBag.cancel_open_orders()


class FactorBag():
    @staticmethod
    def get_continue_high_limit_stocks(stocks, end_date=None, n=1, pre_limit=False):
        """
        获得持续n天涨停板的股票（不全部是一字板）
        stocks: 考察的股票列表
        end_date: 截止日期，默认为今天
        n: 前days个交易日是涨停板
        pre_limit: 如果设置为True，则第前n+1个交易日限制必须是非涨停板
        """
        stock_name, stock_info = [], []
        start_date = BasicBag.get_current_tradeday(end_date=end_date, days=n)
        for security in stocks:
            security_df = BasicBag.get_price(security, start_date=start_date, end_date=end_date,
                                             fields=['open', 'close', 'high_limit'])
            if (security_df['high_limit'] - security_df['close']).sum() == 0 and (
                    security_df['close'] - security_df['open']).sum() > 0:
                if pre_limit:
                    pre_trade_day = BasicBag.get_current_tradeday(end_date=end_date, days=n + 1)
                    pre_trade_df = BasicBag.get_price(security, start_date=pre_trade_day, end_date=pre_trade_day,
                                                      fields=['open', 'close', 'high_limit'])
                    if len(pre_trade_df) > 0 and pre_trade_df.iloc[0]['close'] == pre_trade_df.iloc[0]['high_limit']:
                        continue
                stock_name.append(security)
                stock_info.append(security_df.iloc[-1])

        return pd.DataFrame(stock_info, index=stock_name, columns=['open', 'close', 'high_limit'])

    @staticmethod
    def is_on_moving_average(security, end_date, n=5, multi=1):
        """
        是否在N日移动平均线之上
        :param context:
        :param end_date:
        :param ma:
        :return:
        """
        start_date = BasicBag.get_current_tradeday(end_date=end_date, days=n)
        close_data = BasicBag.get_price(security, start_date=start_date, end_date=end_date, fields='close')
        ma = close_data['close'].mean()
        return close_data.iloc[-1]['close'] >= multi * ma
