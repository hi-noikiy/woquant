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
print(jq.get_price("600555" , end_date="2020-03-11", count=1))