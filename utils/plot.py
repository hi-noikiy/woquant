"""
画图模块

数值类型: python原生类型
"""
from datetime import datetime
from pyecharts.charts import Bar
from pyecharts import options as opts  # 一切皆 Options
from pyecharts.globals import ThemeType
from pyecharts.render import make_snapshot
from snapshot_selenium import snapshot
from utils.db import DBManager

db = DBManager()

def plot_valuation_report():
    df = db.read("valuation_report")
    x, y = df['name'].values.tolist(), df['rate'].values.tolist()
    series_name = "高估比例"
    title = "股票池估值报告"
    subtitle = datetime.now().strftime("%Y%m%d")
    bar = (
        Bar(init_opts={"height": "700px", "bg_color": "white","theme":ThemeType.LIGHT})
            .add_xaxis(x)
            .add_yaxis(series_name, y)
            .set_series_opts(
            label_opts=opts.LabelOpts(position="right"),
            markline_opts=opts.MarkLineOpts(
                data=[opts.MarkLineItem(x=12, name="科技股安全线"), opts.MarkLineItem(x=5, name="消费股安全线")],
                linestyle_opts={'color': 'rgb(220, 20, 60)'}
            )
        )
            .set_global_opts(title_opts=opts.TitleOpts(title=title, subtitle=subtitle))
            .reversal_axis()
    )
    make_snapshot(snapshot, bar.render(), "output/{title}.png".format(title=title))
    return "output/{title}.png".format(title=title)

if __name__ == '__main__':
    plot_valuation_report()
