import os, sys
from module.source.jqdata import JQData
from jqdatasdk import finance
from sqlalchemy.orm.query import Query
from datetime import datetime
import schedule, time
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
import pandas as pd
from utils.db import DBManager
from config import PROJECT_DIR
from sqlalchemy.sql import or_


def run():
    db = DBManager()
    jq = JQData()
    start_date = datetime.now().strftime("%Y%m%d")
    date_id = datetime.strftime(parse(start_date) + relativedelta(days=-30), '%Y%m%d')
    stock_pool = pd.read_csv(os.path.join(PROJECT_DIR, "config/pool.txt"), dtype=str, sep=' ',
                             names=['tag', 'name', 'code', 'price'])
    stocks = stock_pool['code'].map(lambda x: jq.normalize_code(x)).tolist()
    df = finance.run_query(Query(finance.STK_HK_HOLD_INFO).filter(
        or_(finance.STK_HK_HOLD_INFO.link_id == i for i in [310001, 310002]),
        or_(finance.STK_HK_HOLD_INFO.code == i for i in stocks),
        finance.STK_HK_HOLD_INFO.day >= date_id
    ))[['day', 'name', 'share_ratio']]
    df['day'] = df['day'].map(lambda x: datetime.strftime(x, "%Y%m%d"))

    trade_day = finance.run_query(Query(finance.STK_EXCHANGE_LINK_CALENDAR).filter(
        finance.STK_EXCHANGE_LINK_CALENDAR.day >= date_id,
        or_(finance.STK_EXCHANGE_LINK_CALENDAR.link_id == i for i in [310001, 310002]))
    )[['day', 'type']].drop_duplicates()
    trade_day['day'] = trade_day['day'].map(lambda x: datetime.strftime(x, "%Y%m%d"))

    merge_df = df.merge(trade_day, on='day', how='left')
    merge_df = merge_df[merge_df['type'] == '正常交易日']
    del merge_df['type']

    db.write(merge_df, 'tail_northup', mode='w')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '1':
        run()
        exit(0)
    # 配置每天20:10执行
    schedule.every().day.at("07:00").do(run)

    while True:
        schedule.run_pending()
        time.sleep(1)
