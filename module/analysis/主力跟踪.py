from sqlalchemy.orm.query import Query
from module.source.jqdata import JQData
from utils.db import DBManager
from datetime import datetime
import schedule, time
from jqdatasdk import finance


def run():
    jq = JQData()
    db = DBManager()

    df = finance.run_query(
        Query(finance.FUT_MEMBER_POSITION_RANK)
            .filter(
            finance.FUT_MEMBER_POSITION_RANK.code == 'IC2003.CCFX',
            finance.FUT_MEMBER_POSITION_RANK.day == datetime.now().strftime("%Y%m%d"),
            finance.FUT_MEMBER_POSITION_RANK.member_name == '中信期货')
    )

    if len(df) == 0:
        exit(0)
    inc = df['indicator_increase']
    inc.index = (['total_inc', 'buy_inc', 'sell_inc'])
    vol = df['indicator']
    vol.index = (['total', 'buy', 'sell'])
    total = vol.append(inc)
    total['day'] = df.iloc[0]['day'].strftime("%Y%m%d")
    total = total.to_frame().T
    db.write(total, "tail_zxqh")


schedule.every().day.at("20:10").do(run)

while True:
    schedule.run_pending()
    time.sleep(1)
