该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/11764

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

# 克隆自聚宽文章：https://www.joinquant.com/post/11736
# 标题：招行_海天配对策略（学习招行伊利配对）
# 作者：维络

# 克隆自聚宽文章：https://www.joinquant.com/post/1810
# 标题：【量化课堂】基于协整的搬砖策略
# 作者：JoinQuant量化课堂

import numpy as np
import pandas as pd

#===========================================

def initialize(context):
    set_params()
    set_variables()
    set_backtest()

# ---代码块1. 设置参数
def set_params():
    # 股票1
    g.security1 = '510220.XSHG' 
    # 股票2
    g.security2 = '510500.XSHG'
    # 基准
    g.benchmark = '510500.XSHG'
    # 回归系数
    g.regression_ratio = 1#0.9574#0.9938
    # 股票1默认仓位
    g.p = 0.5
    # 股票2默认仓位
    g.q = 0.5
    # 算z-score天数
    g.test_days = 120

# ---代码块2. 设置变量
def set_variables():
    # 现在状态
    g.state = 'empty'

# ---代码块3. 设置回测
def set_backtest():
    # 设置基准
    set_benchmark(g.benchmark)
    # 只报错
    log.set_level('order', 'error')
    # 真实价格
    set_option('use_real_price', True) 
    # 无滑点
    set_slippage(FixedSlippage(0.))

#==============================================
    
# 每个单位时间(如果按天回测,则每天调用一次,如果按分钟,则每分钟调用一次)调用一次
def handle_data(context, data):
    new_state = get_signal()
    change_positions(get_signal(),context)

# ---代码块4.计算z-score
def z_test():
    # 获取两支股票历史价格
    prices1 = np.array(attribute_history(g.security1, g.test_days, '1d', 'close'))
    prices2 = np.array(attribute_history(g.security2, g.test_days, '1d', 'close'))
    # 根据回归比例算它们的平稳序列 Y-a.X
    stable_series = prices2 - g.regression_ratio*prices1
    # 算均值
    series_mean = mean(stable_series)
    # 算标准差
    sigma = np.std(stable_series)
    # 算序列现值离均值差距多少
    diff = stable_series[-1] - series_mean
    # 返回z值
    return(diff/sigma)#理论上上 这个值服从标准正太分布

# ---代码块5.获取信号
# 返回新的状态，是一个string
def get_signal():
    z_score = z_test()
    if z_score > 2.1:#海天/招行0.82
        # 状态为全仓第一支
        return('buy1')
    # 如果小于负标准差
    if z_score < -2.1:
        # 状态为全仓第二支
        return('buy2')
    # 如果在正负标准差之间
    if -1.95<= z_score <= 1.95:
        return('mid')
            
# ---代码块6.根据信号调换仓位
# 输入是目标状态，输入为一个string
def change_positions(current_state,context):
    # 总值产价值
    total_value = context.portfolio.portfolio_value
    # 如果新状态是全仓股票1
    if  current_state== 'buy1':
        # 全卖股票2
        #order_target(g.security2, 0)
        marginsec_open(g.security2, 100000, style=None, pindex=0)
        # 全买股票1
        order_value(g.security1, total_value)
        # 旧状态更改
        g.state = 'buy1'
    # 如果新状态是全仓股票2
    if  current_state == 'buy2':
        # 全卖股票1
        #order_target(g.security1, 0)
        marginsec_open(g.security1, total_value, style=None, pindex=0)
        # 全买股票2
        order_value(g.security2, total_value)
        # 旧状态更改
        g.state = 'buy2'
    # 如果处于全仓一股票状态，但是z-score交叉0点
    if (current_state== 'mid'):
        if(g.state=='buy1'):
            marginsec_close(g.security2, 100000, style=None, pindex=0)
            order_target_value(g.security1, 0)
        if(g.state=='buy2'):
            marginsec_close(g.security1, 100000, style=None, pindex=0)
            order_target_value(g.security2, 0)
        g.state = 'even'


#止损策略