from sqlalchemy.orm.query import Query
from module.source.jqdata import JQData
from utils.db import DBManager
from datetime import datetime, timedelta

from jqdatasdk import finance
jq = JQData()
db = DBManager()
for i in range(1, 100):
    df = finance.run_query(
        Query(finance.FUT_MEMBER_POSITION_RANK)
            .filter(
            finance.FUT_MEMBER_POSITION_RANK.code == 'IC2003.CCFX',
            finance.FUT_MEMBER_POSITION_RANK.day == (datetime.now() + timedelta(days=-i)).strftime("%Y%m%d"),
            finance.FUT_MEMBER_POSITION_RANK.member_name == '中信期货')
    )
    if len(df) == 0:
        continue
    inc = df['indicator_increase']
    inc.index = (['total_inc', 'buy_inc', 'sell_inc'])
    vol = df['indicator']
    vol.index = (['total', 'buy', 'sell'])
    total = vol.append(inc)
    total['day'] = df.iloc[0]['day'].strftime("%Y%m%d")
    total = total.to_frame().T
    db.write(total, "tail_zxqh")
