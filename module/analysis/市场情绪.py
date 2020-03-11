"""
涨停板数量（去新股）
自然涨停板数量
连板个数（去新股）
"""
from sqlalchemy.orm.query import Query
from module.source.jqdata import JQData
from jqdatasdk import finance
from utils.db import DBManager
from datetime import datetime

index_list = [
    ("上证指数", "000001.XSHG"),
    ("上证50", "000016.XSHG"),
    ("深证成指", "399001.XSHE"),
    ("沪深300", "000300.XSHG"),
    ("创业板指", "399006.XSHE")
]
jq = JQData()

for index, code in index_list:
    close = jq.get_price(code, end_date=datetime.now().strftime("%Y-%m-%d"), count=1).loc[0,'close']
    print(close)
