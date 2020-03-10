"""
股票池估值报告
# 每晚根据收盘价定时运行
"""
import os
import pandas as pd
from module.source.jqdata import JQData
from config import PROJECT_DIR
from utils.db import DBManager
from utils.plot import plot_valuation_report

# 配置文件
jq_data = JQData()
db = DBManager()
stock_pool = pd.read_csv(os.path.join(PROJECT_DIR, "config/pool.txt"), sep=' ', names=['tag', 'name', 'code', 'price'])
stock_pool['close'] = stock_pool['code'].map(lambda x: jq_data.get_realtime_price(x))
stock_pool['rate'] = stock_pool.apply(lambda x: round((x.close - x.price) / x.price * 100, 2), axis=1)
stock_pool.sort_values(by='rate', ascending=False, inplace=True)
db.write(stock_pool[['name', 'tag', 'price', 'close', 'rate']], 'valuation_report', mode='w')

# 生成图片
plot_valuation_report()
