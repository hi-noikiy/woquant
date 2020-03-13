"""
涨跌停板数量（去新股）
自然涨停板数量
连板个数（去新股）
"""
from sqlalchemy.orm.query import Query
from module.source.jqdata import JQData
from jqdatasdk import finance
from utils.db import DBManager
from datetime import datetime

jq = JQData()

stocks = jq.get_all_stocks().reset_index()
stocks_list = stocks['index'].values.tolist()
stocks_price = jq.get_price(stocks_list, count=2)
df = stocks.merge(stocks_price, left_on='index', right_on='code')
print(df.head())
print(df.columns)
