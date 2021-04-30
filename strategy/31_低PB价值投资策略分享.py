该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/11549

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

'''
一 策略名称：低PB价值投资策略
二 策略概述：致力于筛选低市净率且财务指标向好的A股，做价值投资
三 策略基本内容：
    1 选股：过滤筛选A股列表，并对符合条件的股票进行排序，主要包括：
        1.1 状态过滤：过滤停盘、退市、ST及开盘涨停股；
        1.2 财务筛选：筛选流通股本小于25亿股、市净率小于0.85、且营业收入同比增长率、净利润同比增长率、净资产收益率ROE
                      都大于0的股票，对初步筛选后的股票按市净率从小到大筛选出前10只股票（最多10只）；
        1.3 排序：对选出的股票按净资产收益率ROE、市净率、净利润同比增长率、总市值四项指标所占权重比例重新排序
    2 择时：对排序第一的股票当天开盘即买入
    3 仓位管理：最多同时持有一只股票，且只做满仓买入或全仓卖出操作
    4 止盈止损：每分钟判断个股从持仓后的最大涨跌幅度及最高价回撤幅度，若超过设定阈值，则清仓
四 策略回测概述：
    1 回测周期：2014-01-01 到 2018-01-30 ，按分钟回测
    2 初始资金：100000元
    3 策略收益：1465.70% ，策略年化收益：99.19% ，Alpha：0.908 ，Beta：0.357 ，Sharpe：3.149 ，胜率：100% ，最大回测：15.860%
五 策略还需改进项：
    1 空仓时间较多，大概占了回测周期的三分之一时间，有待改善
    2 探索是否有更适合该策略的仓位管理方法
    3 引进动态量化因子，解决目前筛选参数均为常量而导致在其他回测周期收益效果并不理想的问题

版本：1.3.1.180318
日期：2018.3.18
作者：王文纲
'''

# 导入函数库
from kuanke.wizard import *
from jqdata import *
import numpy as np
import pandas as pd
import talib
import datetime

## 初始化函数，设定要操作的股票、基准等等
def initialize(context):
    # 设定基准
    set_benchmark('000300.XSHG')
    # 设定滑点(固定值0.02元)，买卖时都会加减价差的一半，比如固定值0.02元，买卖时自动加减0.01元
    set_slippage(FixedSlippage(0.02))
    # True为开启动态复权模式，使用真实价格交易（每天获得当天的除权价格，往前取前基于当天日期的前复权价格）
    set_option('use_real_price', True) 
    # 设定成交量比例为100%（根据实际行情限制每个订单的成交量，成交量不超过：每日成交量*每日成交量比例）
    set_option('order_volume_ratio', 1)
    # 股票类交易手续费是：买入时佣金万分之三，卖出时佣金万分之三加千分之一印花税, 每笔交易佣金最低扣5块钱
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    # 选股频率
    g.check_stocks_refresh_rate = 1
    # 买入频率、卖出频率
    g.buy_refresh_rate , g.sell_refresh_rate = 1 , 1
    # 最大建仓数量
    g.max_hold_stocknum = 1
    # 个股最大持仓比重
    g.security_max_proportion = 1
    # 选股频率计数器
    g.check_stocks_days = 0 
    # 买卖交易频率计数器
    g.buy_trade_days , g.sell_trade_days = 0 , 0
    # 获取未卖出的股票
    g.open_sell_securities = [] 
    # 卖出股票的dict
    g.selled_security_list={}
    # 股票筛选初始化（是否过滤停盘、是否过滤退市、是否过滤ST）
    g.filter_paused , g.filter_delisted , g.filter_st = True , True , True
    # 股票池
    g.security_universe_index = ["all_a_securities"]
    g.security_universe_user_securities = []
    # 股票筛选排序初始化（总排序准则： desc-降序、asc-升序）
    g.check_out_lists_ascending = 'desc'
    # 出场初始化(设定是否卖出buy_lists中的股票、设定固定出仓的数量或者百分比)
    g.sell_will_buy , g.sell_by_amount , g.sell_by_percent = True , None , None
    # 入场初始化（设定是否可重复买入、单只股票最大买入金额（元）或股数（股））
    g.filter_holded , g.max_buy_value , g.max_buy_amount = True , None , None

    # 关闭提示
    log.set_level('order', 'error')
    # 运行函数
    run_daily(sell_every_day,'every_bar') #卖出未卖出成功的股票
    run_daily(risk_management, 'every_bar') #风险控制
    run_daily(check_stocks, 'open') #选股并排序
    run_daily(trade, 'open') #交易（无择时）
    run_daily(selled_security_list_count, 'after_close') #卖出股票日期计数 
    

## 卖出未卖出成功的股票
def sell_every_day(context):
    open_sell_securities = [s for s in context.portfolio.positions.keys() if s in g.open_sell_securities]
    if len(open_sell_securities)>0:
        for stock in open_sell_securities:
            order_target_value(stock, 0)
    return

## 风控
def risk_management(context):
    # 判断是否卖出buy_lists中的股票
    if not g.sell_will_buy:
        sell_lists = [security for security in sell_lists if security not in buy_lists]
    # 获取 sell_lists 列表
    risk_init_sl = context.portfolio.positions.keys()
    risk_sell_lists = context.portfolio.positions.keys()
    # 止盈：收益率≥30%时坚定持有，直到最高收益回落4%时清仓该股票（特殊情况下也能起止损作用）
    if len(risk_sell_lists) > 0:
        for security in risk_sell_lists:
            # 计算单只股票股价从建仓至当前的最高价与最低价，取每分钟数据
            df_price = get_price(security, start_date=context.portfolio.positions[security].init_time, end_date=context.current_dt, frequency='1m', fields=['high','low'])
            highest_price = df_price['high'].max()
            lowest_price = df_price['low'].min()    
            # 单只股票股价从建仓至当前的最高价与最低价相差百分比≥30%且最高收益回落4%时清仓该股票，取每分钟数据
            if (highest_price - lowest_price) / lowest_price >= 0.3 \
                    and (highest_price - context.portfolio.positions[security].price) / highest_price >= 0.04:
                # 卖出该股所有股票
                order_target_value(security, 0)
    # 获取卖出的股票, 并加入到 g.selled_security_list中
    selled_security_list_dict(context,risk_init_sl)
    return

## 股票筛选并排序
def check_stocks(context):
    if g.check_stocks_days%g.check_stocks_refresh_rate != 0:
        # 计数器加一
        g.check_stocks_days += 1
        return
    # 股票池赋值
    g.check_out_lists = get_security_universe(context, g.security_universe_index, g.security_universe_user_securities)
    # 过滤ST股票
    g.check_out_lists = st_filter(context, g.check_out_lists)
    # 过滤退市股票
    g.check_out_lists = delisted_filter(context, g.check_out_lists)
    # 过滤停牌股票
    g.check_out_lists = paused_filter(context, g.check_out_lists)
    # 过滤涨停股票
    g.check_out_lists = high_limit_filter(context, g.check_out_lists)
    # 财务筛选
    g.check_out_lists = financial_statements_filter(context, g.check_out_lists)
    # 经过以上筛选后的股票根据市净率大小按升序排出前10只股票
    df_check_out_lists = get_fundamentals(query(
            valuation.code, valuation.pb_ratio
        ).filter(
            # 这里不能使用 in 操作, 要使用in_()函数
            valuation.code.in_(g.check_out_lists)
        ).order_by(
            # 按市净率升序排列，排序准则：desc-降序、asc-升序
            valuation.pb_ratio.asc()
        ).limit(
            # 最多返回10个
            10
            #前一个交易日的日期
        ), date=context.previous_date)
    # 筛选结果加入g.check_out_lists中
    g.check_out_lists = df_check_out_lists['code']
    # 排序    
    input_dict = get_check_stocks_sort_input_dict()
    g.check_out_lists = check_stocks_sort(context,g.check_out_lists,input_dict,g.check_out_lists_ascending)
    # 计数器归一
    g.check_stocks_days = 1
    return

## 交易函数
def trade(context):
    # 获取 buy_lists 列表
    buy_lists = g.check_out_lists
    # 卖出操作
    if g.sell_trade_days%g.sell_refresh_rate != 0:
        # 计数器加一
        g.sell_trade_days += 1
    else:
        # 卖出股票
        sell(context, buy_lists)
        # 计数器归一
        g.sell_trade_days = 1
    # 买入操作
    if g.buy_trade_days%g.buy_refresh_rate != 0:
        # 计数器加一
        g.buy_trade_days += 1
    else:
        # 卖出股票
        buy(context, buy_lists)
        # 计数器归一
        g.buy_trade_days = 1

## 卖出股票日期计数
def selled_security_list_count(context):
    if len(g.selled_security_list)>0:
        for stock in g.selled_security_list.keys():
            g.selled_security_list[stock] += 1

##################################  选股排序函数群 ##################################
# 获取股票股票池
def get_security_universe(context, security_universe_index, security_universe_user_securities):
    temp_index = []
    for s in security_universe_index:
        if s == 'all_a_securities':
            temp_index += list(get_all_securities(['stock'], context.current_dt.date()).index)
        else:
            temp_index += get_index_stocks(s)
    for x in security_universe_user_securities:
        temp_index += x
    return  sorted(list(set(temp_index)))

## 过滤ST股票
def st_filter(context, security_list):
    if g.filter_st:
        current_data = get_current_data()
        security_list = [stock for stock in security_list if not current_data[stock].is_st]
    # 返回结果
    return security_list

## 过滤退市股票
def delisted_filter(context, security_list):
    if g.filter_delisted:
        current_data = get_current_data()
        security_list = [stock for stock in security_list if not (('退' in current_data[stock].name) or ('*' in current_data[stock].name))]
    # 返回结果
    return security_list

## 过滤停牌股票
def paused_filter(context, security_list):
    if g.filter_paused:
        current_data = get_current_data()
        security_list = [stock for stock in security_list if not current_data[stock].paused]
    # 返回结果
    return security_list

# 过滤涨停股票
def high_limit_filter(context, security_list):
    current_data = get_current_data()
    security_list = [stock for stock in security_list if not (current_data[stock].day_open >= current_data[stock].high_limit)]
    # 返回结果
    return security_list

## 财务指标筛选函数
def financial_statements_filter(context, security_list):
    # 流通股本小于250000万股
    security_list = financial_data_filter_xiaoyu(security_list, valuation.circulating_cap, 250000)
    # 市净率小于0.85
    security_list = financial_data_filter_xiaoyu(security_list, valuation.pb_ratio, 0.85)
    # 营业收入同比增长率(%)：检验上市公司去年一年挣钱能力是否提高的标准
    security_list = financial_data_filter_dayu(security_list, indicator.inc_revenue_year_on_year, 0)
    # 净利润同比增长率：（当期的净利润-上月（上年）当期的净利润）/上月（上年）当期的净利润=净利润同比增长率
    security_list = financial_data_filter_dayu(security_list, indicator.inc_net_profit_year_on_year, 0)
    # 净资产收益率ROE：归属于母公司股东的净利润*2/（期初归属于母公司股东的净资产+期末归属于母公司股东的净资产）
    security_list = financial_data_filter_dayu(security_list, indicator.roe, 0)
    # 返回列表
    return security_list

# 获取选股排序的 input_dict
def get_check_stocks_sort_input_dict():
    #desc-降序、asc-升序
    input_dict = {
        indicator.roe:('desc',0.7), #净资产收益率ROE，从大到小，权重0.7
        valuation.pb_ratio:('asc',0.05), #市净率，从小到大，权重0.05
        indicator.inc_net_profit_year_on_year:('desc',0.2), #净利润同比增长率，从大到小，权重0.2
        valuation.market_cap:('desc',0.05), #总市值，从大到小，权重0.05
        }
    # 返回结果
    return input_dict

## 排序
def check_stocks_sort(context,security_list,input_dict,ascending='desc'):
    if (len(security_list) == 0) or (len(input_dict) == 0):
        return security_list
    else:
        # 生成 key 的 list
        idk = list(input_dict.keys())
        # 生成矩阵
        a = pd.DataFrame()
        for i in idk:
            b = get_sort_dataframe(security_list, i, input_dict[i])
            a = pd.concat([a,b],axis = 1)
        # 生成 score 列
        a['score'] = a.sum(1,False)
        # 根据 score 排序
        if ascending == 'asc':# 升序
            a = a.sort(['score'],ascending = True)
        elif ascending == 'desc':# 降序
            a = a.sort(['score'],ascending = False)
        # 返回结果
        return list(a.index)

##################################  交易函数群 ##################################
# 交易函数 - 出场
def sell(context, buy_lists):
    # 获取 sell_lists 列表
    init_sl = context.portfolio.positions.keys()
    sell_lists = context.portfolio.positions.keys()
    # 判断是否卖出buy_lists中的股票
    if not g.sell_will_buy:
        sell_lists = [security for security in sell_lists if security not in buy_lists]
    # 卖出符合条件的股票
    if len(sell_lists)>0:
        for security in sell_lists:
            # 计算单只股票股价从建仓至当前的最高价与最低价，取每分钟数据
            df_price = get_price(security, start_date=context.portfolio.positions[security].init_time, end_date=context.current_dt, frequency='1m', fields=['high','low'])
            highest_price = df_price['high'].max()
            lowest_price = df_price['low'].min() 
            #单只股票股价从建仓至当前的最高价与最低价相差百分比<30%且持有天数达到83天时，清仓该股票
            if (highest_price - lowest_price) / lowest_price < 0.3 and max_hold_days(context, security, 83): 
                sell_by_amount_or_percent_or_none(context, security, g.sell_by_amount, g.sell_by_percent, g.open_sell_securities)
    # 获取卖出的股票列表, 并加入到 g.selled_security_list 中
    selled_security_list_dict(context,init_sl)
    return

# 交易函数 - 入场
def buy(context, buy_lists):
    # 判断是否可重复买入
    buy_lists = holded_filter(context,buy_lists)
    # 获取最终的 buy_lists 列表
    Num = g.max_hold_stocknum - len(context.portfolio.positions)
    buy_lists = buy_lists[:Num]
    # 买入股票
    if len(buy_lists)>0:
        # 分配资金
        result = order_style(context,buy_lists,g.max_hold_stocknum)
        
        for stock in buy_lists:
            if len(context.portfolio.positions) < g.max_hold_stocknum:
                # 获取资金
                Cash = result[stock]
                # 判断个股最大持仓比重
                value = judge_security_max_proportion(context,stock,Cash,g.security_max_proportion)
                # 判断单只最大买入股数或金额
                amount = max_buy_value_or_amount(stock,value,g.max_buy_value,g.max_buy_amount)
                # 下单
                order(stock, amount, MarketOrderStyle())
    return

## 是否可重复买入
def holded_filter(context,security_list):
    if not g.filter_holded:
        security_list = [stock for stock in security_list if stock not in context.portfolio.positions.keys()]
    # 返回结果
    return security_list

## 卖出股票加入dict
def selled_security_list_dict(context,security_list):
    selled_sl = [s for s in security_list if s not in context.portfolio.positions.keys()]
    if len(selled_sl)>0:
        for stock in selled_sl:
            g.selled_security_list[stock] = 0

###################################  其他函数群 ##################################


'''
------------------------------  版本更新说明  ----------------------------------

更新：

2018.03.18  低PB价值投资策略_1.3.1.180318
    优化代码排版，新增策略概述
回测周期：2014-01-01 到 2018-01-30 ，按分钟回测
策略收益：1465.70% ，策略年化收益：99.19% ，Alpha：0.908 ，Beta：0.357 ，Sharpe：3.149 ，胜率：100% ，最大回测：15.860%

2018.03.11  低PB价值投资策略_1.3.0.180311 
    剔除股东权益合计大于25亿元的选股指标，
    新增营业收入同比增长率、净利润同比增长率、净资产收益率ROE都大于0的选股指标
    新增对财务筛选后的股票按市净率从小到大再次做筛选
    去除入场函数筛选
回测周期：2014-01-01 到 2018-01-30 ，按分钟回测
策略收益：1465.70% ，策略年化收益：99.19% ，Alpha：0.908 ，Beta：0.357 ，Sharpe：3.149 ，胜率：100% ，最大回测：15.860%

2018.03.09  低PB价值投资策略_1.2.0.180309
    去除个股止损条件，并将止盈条件中的最大涨幅更改为最大涨跌幅，可兼顾止损状态
回测周期：2014-01-01 到 2018-01-30 ，按分钟回测
策略收益：1068.39% ，策略年化收益：85.11% ，Alpha：0.740 ，Beta：0.578 ，Sharpe：2.705 ，胜率：93.3% ，最大回测：21.182%

2018.03.04  低PB价值投资策略_1.1.2.180304
    卖出未卖出成功的股票函数sell_every_day的调用频次由'open'改为'every_bar'
回测周期：2014-01-01 到 2018-01-30 ，按分钟回测
策略收益：1032.76% ，策略年化收益：83.68% ，Alpha：0.727 ，Beta：0.569 ，Sharpe：2.723 ，胜率：81.3% ，最大回测：21.91%

2018.03.04  低PB价值投资策略_1.1.1.180304
    添加完善注释
回测周期：2014-01-01 到 2018-01-30 ，按分钟回测
策略收益：1032.76% ，策略年化收益：83.68% ，Alpha：0.727 ，Beta：0.569 ，Sharpe：2.723 ，胜率：81.3% ，最大回测：21.91%

2018.03.04  低PB价值投资策略_1.1.0.180304
    将个股最大持仓比重由0.5调整为1，最大建仓数量由3调整为1，并添加完善注释
回测周期：2014-01-01 到 2018-01-30 ，按分钟回测
策略收益：1032.76% ，策略年化收益：83.68% ，Alpha：0.727 ，Beta：0.569 ，Sharpe：2.723 ，胜率：81.3% ，最大回测：21.91%

2018.03.04  低PB价值投资策略_1.0.0.180304
    首次脱离向导式框架，修改原个股止盈条件，调整为个股达到最大设定涨幅后坚定持有，直到低于设定的回撤幅度时止盈
回测周期：2014-01-01 到 2018-01-30 ，按分钟回测
策略收益：729.21% ，策略年化收益：69.87% ，Alpha：0.590 ，Beta：0.562 ，Sharpe：2.618 ，胜率：78.9% ，最大回测：12.994%

2018.01.31  低PB价值投资策略_0.1.5.180131
    委托买入类型由等权重买入'by_cap_mean'改为按股票总市值比例买入'by_market_cap_percent' 
回测周期：2014-01-01 到 2018-01-30 ，按分钟回测
策略收益：711.27%，策略年化收益：68.95% ，Alpha：0.582 ，Beta：0.553 ，Sharpe：2.543 ，胜率：79.4% ，最大回测：13.375%

2018.01.02  低PB价值投资策略_0.1.4.180102
    复制向导式框架生成的程序，开始研究
回测周期：2014-01-01 到 2017-12-16 ，按分钟回测
策略收益：589.68%，策略年化收益：64.75% ，Alpha：0.547 ，Beta：0.560 ，Sharpe：2.405 ，胜率：81.8% ，最大回测：12.971%

-------------------------------------------------------------------------------
'''






























