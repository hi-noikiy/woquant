"""
画图模块

数值类型: python原生类型
"""
from datetime import datetime
from pyecharts.charts import Bar, Page, Line
from pyecharts import options as opts  # 一切皆 Options
from pyecharts.globals import ThemeType
from utils.db import DBManager
from config import PROJECT_DIR
import os

db = DBManager()


def valuation_report():
    """
    股票池估值报告
    :return:
    """
    df = db.read("valuation_report")
    x, y = df['name'].values.tolist(), df['rate'].values.tolist()
    series_name = "高估比例"
    title = "股票池估值报告"
    subtitle = datetime.now().strftime("%Y%m%d")
    bar = (
        Bar(init_opts={"height": "700px", "bg_color": "white", "theme": ThemeType.LIGHT})
            .add_xaxis(x)
            .add_yaxis(series_name, y)
            .set_series_opts(
            label_opts=opts.LabelOpts(position="right"),
            markline_opts=opts.MarkLineOpts(
                data=[opts.MarkLineItem(x=12, name=""), opts.MarkLineItem(x=6, name="")],
                linestyle_opts={'color': 'rgb(220, 20, 60)'}
            )
        )
            .set_global_opts(title_opts=opts.TitleOpts(title=title, subtitle=subtitle))
            .reversal_axis()
    )
    # make_snapshot(snapshot, bar.render(), output_path)
    return bar


def tail_axqh():
    """
    中信期货跟踪
    :return:
    """
    df = db.read("tail_zxqh").tail(25)
    line = (

        Line(init_opts={"height": "500px", "width": "500", "theme": ThemeType.WHITE})
            .add_xaxis(df['day'].values.tolist())
            .add_yaxis("多单", df['buy_inc'].values.tolist())
            .add_yaxis("空单", df['sell_inc'].values.tolist())
            .add_yaxis("多-空", (df['buy_inc'] - df['sell_inc']).values.tolist())
            .set_series_opts(label_opts=opts.LabelOpts(font_size=8))
            .set_global_opts(title_opts=opts.TitleOpts(title="主力跟踪-中信期货", subtitle=datetime.now().strftime("%Y%m%d")),
                             xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(font_size=8, rotate=30)))
    )
    return line


def plot_all():
    chart1 = valuation_report()
    chart2 = tail_axqh()

    page = Page()
    page.add(chart1, chart2)
    output_path = os.path.join(PROJECT_DIR, "utils/output/统计指标.html")
    page.render(output_path)
    return "utils/output/统计指标.html"


if __name__ == '__main__':
    plot_all()
