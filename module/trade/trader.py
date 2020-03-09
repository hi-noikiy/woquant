from module.source.jqdata import JQData
from real_trader.trade_bundle.live_trade import *
from real_trader.trade_order.order_api import *
from configparser import ConfigParser
from config import PROJECT_DIR
import os
import logging
import logging.config

conf = ConfigParser()
conf.read(os.path.join(PROJECT_DIR, "config/base.conf"), encoding="utf-8")

# 日志配置
logging.config.fileConfig(os.path.join(PROJECT_DIR, "config/logging.conf"))
logger = logging.getLogger('root')


class Trader(object):
    def __init__(self):
        self.jq_data = JQData()

        init_trader(g, context,
                    conf.get("Trade", 'account'),
                    conf.get("Trade", 'password'),
                    conf.getint("Trade", 'exchange'),
                    conf.get("Trade", 'path'))
        logger.info("中泰资金账户[{account}] 登陆账号成功".format(account=conf.get("Trade", 'account')))

        init_current_bundle(self.initialize,
                            self.before_trading_start,
                            self.after_trading_end,
                            self.handle_tick)

    def before_trading_start(self, context):
        logger.info('##### before_trading_start #####')

    def after_trading_end(self, context):
        logger.info('##### after_trading_end #####')
        unsubscribe_all()

    def handle_tick(self, context, tick):
        print('##### handle_tick #####')
        print(tick.current)
        # order('600519.XSHG', 100)

    def initialize(self,context):
        print('##### initialize #####')

        # 订阅多个标的
        subscribe('600519.XSHG', 'tick')
        subscribe('000858.XSHE', 'tick')

        # 测试jqdata数据
        # print(jq.get_price('000001.XSHE', start_date='2015-12-01 14:00:00', end_date='2015-12-02 12:00:00',
        #                    frequency='1m'))


if __name__ == '__main__':
    trader = Trader()
