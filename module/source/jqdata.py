import os
import logging
import logging.config
from configparser import ConfigParser
import jqdatasdk as jq
from config import PROJECT_DIR
from datetime import datetime

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
            logger.warning("JQ用户[{username}]登录失败".format(username=username))

    def get_query_count(self):
        query_count = jq.get_query_count()
        logger.info("当日剩余调用次数 {spare}/{total}".format(spare=query_count['spare'], total=query_count['total']))
        return query_count

    def get_price(self, stock, start_date=None, end_date=None, count=None, frequency='daily'):
        return jq.get_price(jq.normalize_code(stock),
                            start_date=start_date,
                            end_date=end_date,
                            count=count,
                            frequency=frequency)

    def current_minute(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def current_date(self):
        return datetime.now().date()

    def get_realtime_price(self, stock):
        """
        获得股票实时(前一分钟)价格
        :param stock:
        :return:
        """
        return self.get_price(stock,
                              end_date=self.current_minute(),
                              count=1,
                              frequency='minute')['close'][0]

    def get_all_price(self):
        return jq.get_trade_days(start_date=None, end_date=None, count=1)

if __name__ == '__main__':
    jq_data = JQData(conf.get("JQData", "username"), conf.get("JQData", "password"))
    # print(jq_data.get_realtime_price('600741'))
    print(jq_data.get_all_price())
