from snapshot_pyppeteer import snapshot

from pyecharts.charts import Bar
from pyecharts.faker import Faker
from pyecharts import options as opts
from pyecharts.render import make_snapshot


def bar_base() -> Bar:
    c = (
        Bar()
        .add_xaxis(Faker.choose())
        .add_yaxis("商家A", Faker.values())
        .add_yaxis("商家B", Faker.values())
        .set_global_opts(title_opts=opts.TitleOpts(title="Bar-基本示例", subtitle="我是副标题"))
    )
    make_snapshot(snapshot, c.render(), "bar.png")


if __name__ == '__main__':
    bar_base()
