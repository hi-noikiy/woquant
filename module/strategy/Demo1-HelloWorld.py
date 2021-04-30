# @Time : 2021/1/11 20:10
# @Author : LiuBin
# @File : Demo1-HelloWorld.py
# @Description : 
# @Software: PyCharm


def initialize(context):
    # 定义一个全局变量, 保存要操作的股票
    g.security = '000001.XSHE'
    # 运行函数
    run_daily(market_open, time='every_bar')

def market_open(context):
    if g.security not in context.portfolio.positions:
        order(g.security, 1000)
    else:
        order(g.security, -800)