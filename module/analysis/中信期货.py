from sqlalchemy.orm.query import Query
from module.source.jqdata import JQData
from utils.db import DBManager
from datetime import datetime
import schedule, time
from jqdatasdk import finance
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
import pandas as pd

def run():
    jq = JQData()
    db = DBManager()

    total_df = pd.DataFrame()
    start_date = datetime.now().strftime("%Y%m%d")
    for i in range(1):
        date_id = datetime.strftime(parse(start_date) + relativedelta(days=i), '%Y%m%d')
        df = finance.run_query(
            Query(finance.FUT_MEMBER_POSITION_RANK)
                .filter(
                finance.FUT_MEMBER_POSITION_RANK.exchange == 'CCFX',
                finance.FUT_MEMBER_POSITION_RANK.underlying_code == 'IC',
                finance.FUT_MEMBER_POSITION_RANK.day == date_id,
                #             finance.FUT_MEMBER_POSITION_RANK.day == datetime.now().strftime("%Y%m%d"),
                finance.FUT_MEMBER_POSITION_RANK.member_name == '中信期货')
        )
        total_df = total_df.append(df, ignore_index=True)

    trans_df = \
    total_df[['day', 'code', 'indicator', 'indicator_increase', 'rank_type_ID']].groupby(['day', 'rank_type_ID'])[
        ['indicator', 'indicator_increase']].sum().unstack('rank_type_ID')
    trans_df.columns = ['total', 'buy', 'sell', 'total_inc', 'buy_inc', 'sell_inc']
    if len(trans_df) > 0:
        trans_df.reset_index(inplace=True)
        db.write(trans_df, "tail_zxqh_v2")



# 配置每天20:10执行
schedule.every().day.at("20:10").do(run)

while True:
    schedule.run_pending()
    time.sleep(1)
