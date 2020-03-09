"""
画图模块

数值类型: python原生类型
"""
import pyecharts
from pyecharts.charts import Bar
from pyecharts import options as opts  # 一切皆 Options
from pyecharts.render import make_snapshot
from snapshot_selenium import snapshot


def plot_bar(x, y, series_name, title="未命名"):
    bar = (
        Bar()
            .add_xaxis(x)
            .add_yaxis(series_name, y)
            .set_global_opts(title_opts={"text": title})
    )
    make_snapshot(snapshot, bar.render(), "{title}.png".format(title=title))


def plot_hbar(x, y, series_name, title="未命名"):
    bar = (
        Bar()
            .add_xaxis(x)
            .add_yaxis(series_name, y)
            .reversal_axis()
            .set_series_opts(label_opts={"position": "right"})
            .set_global_opts(title_opts={"text": title})
    )
    make_snapshot(snapshot, bar.render(), "{title}.png".format(title=title))
