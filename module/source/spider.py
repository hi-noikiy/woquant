from sqlalchemy.orm.query import Query
from module.source.jqdata import JQData
from jqdatasdk import finance
from utils.db import DBManager
from datetime import datetime , timedelta

jq = JQData()
db = DBManager()
for i in range(1000,-1,-1):
    date = (datetime.now() - timedelta(days=i))
    stocks = jq.get_all_stocks(date=date).reset_index()
    stocks_list = stocks['index'].values.tolist()
    stocks_price = jq.get_price(stocks_list, count=1)
    df = stocks.merge(stocks_price, left_on='index', right_on='code')
    db.write(df,"stock_daily")
