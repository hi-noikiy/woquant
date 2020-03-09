# coding=utf-8
from __future__ import print_function, absolute_import
from gm.api import *
import datetime
from dateutil.relativedelta import relativedelta

# 策略中必须有init方法
def init(context):
    pass


import collections
print(collections.Counter(['a','a','b']).most_common(1)[0][0])
# if __name__ == '__main__':
    # run(strategy_id='strategy_id',
# #     #     filename='main.py',
# #     #     mode=MODE_BACKTEST,
# #     #     token='token_id',
# #     #     backtest_start_time='2016-06-17 13:00:00',
# #     #     backtest_end_time='2017-08-21 15:00:00')

