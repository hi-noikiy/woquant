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
                data=[opts.MarkLineItem(x=9, name=""), opts.MarkLineItem(x=-9, name="")],
                linestyle_opts={'color': 'rgb(220, 20, 60)'}
            )
        )
            .set_global_opts(title_opts=opts.TitleOpts(title=title, subtitle=subtitle))
            .reversal_axis()
    )
    # make_snapshot(snapshot, bar.render(), output_path)
    return bar


def tail_zxqh():
    """
    中信期货跟踪
    :return:
    """
    df = db.read("tail_zxqh_v2").sort_values(by='day').tail(25)
    line = (
        Line(init_opts={"height": "500px", "width": "500", "theme": ThemeType.WHITE})
            .add_xaxis(df['day'].values.tolist())
            .add_yaxis("多单", df['buy_inc'].values.tolist())
            .add_yaxis("空单", df['sell_inc'].values.tolist())
            .add_yaxis("多-空", (df['buy_inc'] - df['sell_inc']).values.tolist(), is_selected=False)
            .add_yaxis("净额", (df['buy'] - df['sell']).values.tolist(), is_selected=False)
            .set_series_opts(label_opts=opts.LabelOpts(font_size=8))
            .set_global_opts(title_opts=opts.TitleOpts(title="主力跟踪-中信期货", subtitle=datetime.now().strftime("%Y%m%d")),
                             xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(font_size=8, rotate=30)))
    )
    return line


def tail_northup():
    """
    北上资金跟踪
    :return:
    """
    df = db.read("tail_northup")
    result_df = df.set_index(['day', 'name']).unstack('name')['share_ratio']
    rs_df = ((result_df - result_df.shift()).fillna(0) * 100).applymap(lambda x: round(x))
    selected = sorted(list(rs_df.iloc[-1].items()), key=lambda x: x[1], reverse=True)[0][0]

    c = Line()
    c = c.add_xaxis(rs_df.index.tolist())

    for key in rs_df:
        is_selected = key == selected
        c = c.add_yaxis(key, rs_df[key].values.tolist(), is_smooth=True, is_selected=is_selected)

    c = c.set_series_opts(
        areastyle_opts=opts.AreaStyleOpts(opacity=0.5),
        label_opts=opts.LabelOpts(is_show=False),
    )
    c = c.set_global_opts(
        title_opts=opts.TitleOpts(title="主力跟踪-北上资金", subtitle=datetime.now().strftime("%Y%m%d")),
        xaxis_opts=opts.AxisOpts(
            axistick_opts=opts.AxisTickOpts(is_align_with_label=True),
            is_scale=False,
            boundary_gap=False,
        ),
        legend_opts=opts.LegendOpts(pos_left=100, pos_top=50)
    )
    return c


def plot_all():
    chart1 = valuation_report()
    chart2 = tail_northup()
    chart3 = tail_zxqh()


    page = Page()
    page.add(chart1, chart2, chart3)
    output_path = os.path.join(PROJECT_DIR, "utils/output/统计指标.html")
    page.render(output_path)
    return "utils/output/统计指标.html"


if __name__ == '__main__':
    plot_all()
