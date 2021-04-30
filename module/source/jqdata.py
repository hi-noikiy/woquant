import os
import logging
import logging.config
import pandas as pd
from typing import Union, List
from datetime import datetime
from configparser import ConfigParser
from sqlalchemy.orm.query import Query

import jqdatasdk as jq
from jqdatasdk import finance
from config import PROJECT_DIR

# 配置文件
conf = ConfigParser()
conf.read(os.path.join(PROJECT_DIR, "config/base.conf"), encoding="utf-8")

# 日志配置
logging.config.fileConfig(os.path.join(PROJECT_DIR, "config/logging.conf"))
logger = logging.getLogger('root')


class JQData(object):
    def __init__(self, username=None, password=None):
        # 如果没有传参,使用配置文件的配置
        if not (username and password):
            username = conf.get("JQData", "username")
            password = conf.get("JQData", "password")
        jq.auth(username, password)
        if jq.is_auth():
            logger.info("JQ用户[{username}]登录成功".format(username=username))
        else:
            logger.warning("JQ用户[{username}]登录失败，请检查用户名和密码。".format(username=username))

    def get_query_count(self):
        """
        当前剩余查询量
        """
        query_count = jq.get_query_count()
        logger.info("当日剩余调用次数 {spare}/{total}".format(spare=query_count['spare'], total=query_count['total']))
        return query_count

    def normalize_code(self, stock_code: str) -> str:
        """
        规范化为聚宽格式的代码
        :param stock_code:  000001
        :return:  000001.XSHE
        """
        return jq.normalize_code(stock_code)

    def get_name(self, stock_code: Union[str, List[str]], ret_str=True) -> str:
        """
        获得股票中文名称，返回一个字符串
        :param stock_code: list/str
        :return: str
        """
        if isinstance(stock_code, str):
            name = jq.get_security_info(stock_code).display_name
        else:
            name = [jq.get_security_info(code).display_name for code in stock_code]
            if ret_str:
                name = ' , '.join(name)
        return name

    def get_concept_stocks(self, concept_code, date=None, ret_name=False):
        if not date:
            date = self.get_current_tradeday()
        if concept_code.startswith("GN"):
            stocks = jq.get_concept_stocks(concept_code, date=date)
        else:
            stocks = jq.get_industry_stocks(concept_code, date=date)
        if ret_name:
            stocks = self.get_name(stocks, ret_str=False)
        return stocks

    def current_minute(self):
        """
        当前时间戳
        :return:
        """
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def current_date(self):
        return datetime.now().date()

    def get_current_tradeday(self, end_date=None, days: int = 0, ret_first=True):
        """
        获取最近N个交易日
        :return:
        """
        trade_days = jq.get_trade_days(end_date=end_date, count=days + 1)
        return trade_days[0] if ret_first else trade_days

    def get_price(self, stock, fields: Union[str, List[str]] = 'close', start_date=None, end_date=None, count=None,
                  frequency='1d'):
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
            end_date = self.get_current_tradeday()
        return jq.get_price(stock,
                            start_date=start_date,
                            end_date=end_date,
                            count=count,
                            fields=fields,
                            frequency=frequency,
                            panel=False
                            )

    def get_realtime_price(self, stock):
        """
        获得股票实时(前一分钟)价格
        :param stock:
        :return:
        """
        return self.get_price(stock,
                              end_date=self.current_minute(),
                              count=1,
                              frequency='1m').iloc[0, 0]

    def get_all_stocks(self, date=None, drop_new=30, drop_st=True, max_circulating_market_cap=None,
                       min_circulating_market_cap=None, display_name=False):
        """
        获得股票池
        :param date:
        :param drop_new:
        :param drop_st:
        :param display_name:
        :return:
        """
        if not date:
            date = self.get_current_tradeday()
        # 获取所有股票列表
        all_security_df = jq.get_all_securities(date=date)
        # 过滤掉当天退市股
        all_security_df = all_security_df[all_security_df.end_date.astype(str) > str(date)]
        # 过滤掉上市30天以内的次新股，如果是负数则保留abs(drop_new)天内的次新股
        start_date = self.get_current_tradeday(days=abs(drop_new))
        if drop_new >= 0:
            all_security_df = all_security_df[all_security_df.start_date.astype(str) < str(start_date)]
        else:
            all_security_df = all_security_df[all_security_df.start_date.astype(str) > str(start_date)]
        # 过滤掉ST股
        if drop_st:
            is_st = jq.get_extras("is_st", all_security_df.index.tolist(), end_date=date, count=1).T.iloc[:, 0]
            all_security_df = all_security_df[~is_st]
        if max_circulating_market_cap or min_circulating_market_cap:
            all_security_df = self.get_market_cap(all_security_df, date)
            if max_circulating_market_cap:
                all_security_df = all_security_df[
                    all_security_df['circulating_market_cap'] <= max_circulating_market_cap]
            if min_circulating_market_cap:
                all_security_df = all_security_df[
                    all_security_df['circulating_market_cap'] >= max_circulating_market_cap]

        # 获取最终股票列表
        return all_security_df.index.tolist() if not display_name else all_security_df.display_name.tolist()

    def get_continue_high_limit_stocks(self, stocks, end_date=None, n=1, pre_limit=False):
        """
        获得持续n天涨停板的股票（不全部是一字板）
        stocks: 考察的股票列表
        end_date: 截止日期，默认为今天
        n: 前days个交易日是涨停板
        pre_limit: 如果设置为True，则第前n+1个交易日限制必须是非涨停板
        """
        stock_name, stock_info = [], []
        start_date = self.get_current_tradeday(end_date=end_date, days=n)
        for security in stocks:
            security_df = self.get_price(security, start_date=start_date, end_date=end_date,
                                         fields=['open', 'close', 'high_limit'])
            if (security_df['high_limit'] - security_df['close']).sum() == 0 and (
                    security_df['close'] - security_df['open']).sum() > 0:
                if pre_limit:
                    pre_trade_day = self.get_current_tradeday(end_date=end_date, days=n + 1)
                    pre_trade_df = self.get_price(security, start_date=pre_trade_day, end_date=pre_trade_day,
                                                  fields=['open', 'close', 'high_limit'])
                    if len(pre_trade_df) > 0 and pre_trade_df.iloc[0]['close'] == pre_trade_df.iloc[0]['high_limit']:
                        continue
                stock_name.append(security)
                stock_info.append(security_df.iloc[-1])

        return pd.DataFrame(stock_info, index=stock_name, columns=['open', 'close', 'high_limit'])

    def is_on_moving_average(self, security, end_date, n=5, multi=1):
        """
        是否在N日移动平均线之上
        :param context:
        :param end_date:
        :param ma:
        :return:
        """
        start_date = self.get_current_tradeday(end_date=end_date, days=n)
        close_data = self.get_price(security, start_date=start_date, end_date=end_date, fields='close')
        ma = close_data['close'].mean()
        return close_data.iloc[-1]['close'] >= multi * ma

    # def get_currency_value_topk(self,security_list, date_id=None, topk=3, context=None, max_market_cap=None,
    #                             min_market_cap=None):
    #     if not date_id:
    #         date_id = self.get_current_tradeday(context)
    #     mc = get_factor_values(security_list, factors='circulating_market_cap', end_date=date_id, count=1)[
    #         'circulating_market_cap'].iloc[0]
    #     if max_market_cap is not None:
    #         mc = mc[mc <= max_market_cap]
    #     if min_market_cap is not None:
    #         mc = mc[mc >= min_market_cap]
    #     return mc.sort_values()[:topk].index.tolist()

    def get_market_cap(self, security: Union[str, List[str], pd.DataFrame], date=None, circulation=True):
        """
        获取市值(流通市值)数据
        :param security:  字符串 、 列表 、 DataFrame
        :param date:
        :param circulation: 是否流通市值
        :return:  数值 、 字典 、 DataFrame
        """
        if not date:
            date = self.get_current_tradeday()
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


if __name__ == '__main__':
    jq_data = JQData()
    # all_stocks = jq_data.get_all_stocks(drop_new=-30, max_circulating_market_cap=10)
    # high_limit_stocks = jq_data.get_continue_high_limit_stocks(all_stocks)

    print(jq_data.get_current_tradeday(end_date="2021-02-01", days=0))
