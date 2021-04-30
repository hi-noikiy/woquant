该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/12666

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

# 克隆自聚宽文章：https://www.joinquant.com/post/1667
# 标题：二八轮动小市值优化版 v2.0.7 [更新于2016.11.16]
# 作者：Morningstar
import math
import numpy as np
import pandas as pd
from pandas import DataFrame,Series
import pickle
import time
import datetime
import jqdata
import talib as tb
import sklearn
from sklearn.decomposition import PCA
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import AdaBoostClassifier,GradientBoostingClassifier,RandomForestRegressor,RandomForestClassifier
from sklearn import cross_validation, metrics,svm,preprocessing  
from sklearn.metrics import mean_squared_error
from sklearn.cross_validation import train_test_split
from sklearn.grid_search import GridSearchCV 
from sklearn.svm import SVR  
from sklearn.externals import joblib
from sklearn.model_selection import learning_curve
from sklearn.linear_model import LinearRegression
'''
二八小市值择时买卖

配置指定频率的调仓日，在调仓日每日指定时间，计算沪深300指数和中证500指数当前的20日涨
幅，如果2个指数的20日涨幅有一个为正，则进行选股调仓，之后如此循环往复。

止损策略：

    大盘止损：(可选)
        1. 每分钟取大盘前130日的最低价和最高价，如果最高大于最低的两倍则清仓，停止交易。
        2. 每分钟判断大盘是否呈现三只黑鸦止损，如果是则当天清仓并停止交易，第二天停止交
           易一天。

    个股止损：(可选)
        每分钟判断个股是否从持仓后的最高价回撤幅度，如果超过个股回撤阈值，则平掉该股持仓

    二八止损：(必需)
        每日指定时间，计算沪深300指数和中证500指数当前的20日涨幅，如果2个指数涨幅都为负，
        则清仓，重置调仓计数，待下次调仓条件满足再操作
'''
from six import StringIO
import tradestat
#import ind
from ind import *
#from blacklist import *

# blacklist.py
# 建议在研究里建立文件blacklist.py，然后将这段代码拷贝进blacklist.py
# 模拟运行的时候只需要更新研究里的数据即可，这样可在不修改模拟运行代码的情况下
# 修改黑名单

# 配置股票黑名单
# 列出当且极不适宜购买的股票
# 注：1. 黑名单有时效性，回测的时候最好不使用，模拟交易建议使用
#     2. 用一模块或者大数据分析收集这类股票，定时更新
def get_blacklist():
    # 黑名单一览表，更新时间 2016.7.10 by 沙米
    # 科恒股份、太空板业，一旦2016年继续亏损，直接面临暂停上市风险
    blacklist = ["600656.XSHG","300372.XSHE","600403.XSHG","600421.XSHG","600733.XSHG","300399.XSHE",
                 "600145.XSHG","002679.XSHE","000020.XSHE","002330.XSHE","300117.XSHE","300135.XSHE",
                 "002566.XSHE","002119.XSHE","300208.XSHE","002237.XSHE","002608.XSHE","000691.XSHE",
                 "002694.XSHE","002715.XSHE","002211.XSHE","000788.XSHE","300380.XSHE","300028.XSHE",
                 "000668.XSHE","300033.XSHE","300126.XSHE","300340.XSHE","300344.XSHE","002473.XSHE"]
    return blacklist

def before_trading_start(context):
    cur_time = context.previous_date
    cur_time = datetime.datetime.strftime(cur_time,'%Y-%m-%d')
    
    print(g.data_.index[0],cur_time)
    print(g.data_.index[0]==cur_time)
    g.stocks = g.data_.where(g.data_==1).loc[cur_time,:].dropna(axis = 0).index.values
    

def after_trading_end(context):
    #log.info("==> after trading end @ %s", str(context.current_dt))
    g.trade_stat.report(context)

    reset_day_param()
    
    # 得到当前未完成订单
    orders = get_open_orders()
    for _order in orders.values():
        log.info("canceled uncompleted order: %s" %(_order.order_id))
    pass

def initialize(context):
    log.info("==> initialize @ %s", str(context.current_dt))
    
    # 设置手续费率
    set_commission(PerTrade(buy_cost=0.0003, sell_cost=0.0013, min_cost=5))
    # 设置基准指数：沪深300指数 '000300.XSHG'
    set_benchmark('000300.XSHG')
    # 设定滑点为百分比
    # 没有调用set_slippage函数, 系统默认的滑点是PriceRelatedSlippage(0.00246)
    #set_slippage(PriceRelatedSlippage(0.004))
    # 使用真实价格回测(模拟盘推荐如此，回测请注释)
    set_option('use_real_price', True)

    # 加载统计模块
    g.trade_stat = tradestat.trade_stat()

    # 配置策略参数
    # 此配置主要为之前的小市值策略，保证之前的收益回撤
    # 如果想要更改，最好新建个函数，调整参数测试其他策略
    set_param()
    # 调仓日计数器，单位：日
    g.day_count = 0
    # 缓存股票持仓后的最高价
    g.last_high = {}
    #定义股票池
    # 如下参数不能更改
    if g.is_market_stop_loss_by_price:
        # 记录当日是否满足大盘价格止损条件，每日盘后重置
        g.is_day_stop_loss_by_price = False

    # 缓存三黑鸦判断状态
    g.is_last_day_3_black_crows = False
    if g.is_market_stop_loss_by_3_black_crows:
        g.cur_drop_minute_count = 0

    if g.is_rank_stock:
        if g.rank_stock_count > g.pick_stock_count:
            g.rank_stock_count = g.pick_stock_count

    if g.is_stock_stop_loss or g.is_stock_stop_profit:
        # 缓存当日个股250天内最大的3日涨幅，避免当日反复获取，每日盘后清空
        g.pct_change = {}

    if g.is_market_stop_loss_by_28_index:
        g.minute_count_28index_drop = 0

    if g.is_equity_curve_protect:
        # 记录当日是否满足资金曲线保护条件，每日盘后重置
        g.is_day_curve_protect = False
    g.time1 = time.time()
    file = StringIO(read_file('pre_result_csv.csv'))
    #print(StringIO(file))
    g.data_ = pd.read_csv(file,index_col = 0)
    # 打印策略参数
    log_param()
def set_param():
    # 调仓频率，单位：日
    g.period = 3
    # 配置调仓时间（24小时分钟制）
    g.adjust_position_hour = 14
    g.adjust_position_minute = 50
    # 配置选股参数

    # 备选股票数目
    g.pick_stock_count = 100
    
    # 配置选股参数
    # 是否根据PE选股
    g.pick_by_pe = False
    # 如果根据PE选股，则配置最大和最小PE值
    if g.pick_by_pe:
        g.max_pe = 200
        g.min_pe = 0

    # 是否根据EPS选股
    g.pick_by_eps = False
    # 配置选股最小EPS值
    if g.pick_by_eps:
        g.min_eps = 0
    
    # 配置是否过滤创业板股票
    g.filter_gem = False
    # 配置是否过滤黑名单股票，回测建议关闭，模拟运行时开启
    g.filter_blacklist = False

    # 是否对股票评分
    g.is_rank_stock = False
    if g.is_rank_stock:
        # 参与评分的股票数目
        g.rank_stock_count = 20

    # 买入股票数目
    g.buy_stock_count = 5
    
    # 配置二八指数
    #g.index2 = '000300.XSHG'  # 沪深300指数，表示二，大盘股
    #g.index8 = '000905.XSHG'  # 中证500指数，表示八，小盘股
    g.index2 = '000016.XSHG'  # 上证50指数
    g.index8 = '399333.XSHE'  # 中小板R指数
    #g.index8 = '399006.XSHE'  # 创业板指数
    
    # 判定调仓的二八指数20日增幅
    #g.index_growth_rate = 0.00
    g.index_growth_rate = 0.01
    
    #设定特征参数
    g.bbands = True
    g.ema = True
    g.cci = True
    g.kd = True
    g.dif = True
    g.macd = True
    g.rsi = True
    g.bais = True
    # 配置是否根据大盘历史价格止损
    # 大盘指数前130日内最高价超过最低价2倍，则清仓止损
    # 注：关闭此止损，收益增加，但回撤会增加
    g.is_market_stop_loss_by_price = False
    if g.is_market_stop_loss_by_price:
        # 配置价格止损判定指数，默认为上证指数，可修改为其他指数
        g.index_4_stop_loss_by_price = '000001.XSHG'

    # 配置三黑鸦判定指数，默认为上证指数，可修改为其他指数
    g.index_4_stop_loss_by_3_black_crows = '000001.XSHG'

    # 配置是否开启大盘三黑鸦止损
    # 个人认为针对大盘判断三黑鸦效果并不好，首先有效三只乌鸦难以判断，准确率实际来看也不好，
    # 其次，分析历史行情看一般大盘出现三只乌鸦的时候，已经严重滞后了，使用其他止损方式可能会更好
    g.is_market_stop_loss_by_3_black_crows = False
    if g.is_market_stop_loss_by_3_black_crows:
        g.dst_drop_minute_count = 60

    # 是否根据28指数值实时进行止损
    g.is_market_stop_loss_by_28_index = False
    if g.is_market_stop_loss_by_28_index:
        # 配置当日28指数连续为跌的分钟计数达到指定值则止损
        g.dst_minute_count_28index_drop = 30

    # 配置是否个股止损
    g.is_stock_stop_loss = False
    # 配置是否个股止盈
    g.is_stock_stop_profit = False
    
    # 配置是否开启资金曲线保护
    g.is_equity_curve_protect = False
    if g.is_equity_curve_protect:
        # 配置资金曲线参数
        g.value_list = []
    
    
def log_param():
    log.info("调仓日频率: %d日" %(g.period))
    log.info("调仓时间: %s:%s" %(g.adjust_position_hour, g.adjust_position_minute))

    log.info("备选股票数目: %d" %(g.pick_stock_count))

    log.info("是否根据PE选股: %s" %(g.pick_by_pe))
    if g.pick_by_pe:
        log.info("选股最大PE: %s" %(g.max_pe))
        log.info("选股最小PE: %s" %(g.min_pe))

    log.info("是否根据EPS选股: %s" %(g.pick_by_eps))
    if g.pick_by_eps:
        log.info("选股最小EPS: %s" %(g.min_eps))
    
    log.info("是否过滤创业板股票: %s" %(g.filter_gem))
    log.info("是否过滤黑名单股票: %s" %(g.filter_blacklist))
    if g.filter_blacklist:
        log.info("当前股票黑名单：%s" %str(get_blacklist()))

    log.info("是否对股票评分选股: %s" %(g.is_rank_stock))
    if g.is_rank_stock:
        log.info("评分备选股票数目: %d" %(g.rank_stock_count))

    log.info("买入股票数目: %d" %(g.buy_stock_count))

    log.info("二八指数之二: %s - %s" %(g.index2, get_security_info(g.index2).display_name))
    log.info("二八指数之八: %s - %s" %(g.index8, get_security_info(g.index8).display_name))
    log.info("判定调仓的二八指数20日增幅: %.1f%%" %(g.index_growth_rate*100))

    log.info("是否开启大盘历史高低价格止损: %s" %(g.is_market_stop_loss_by_price))
    if g.is_market_stop_loss_by_price:
        log.info("大盘价格止损判定指数: %s - %s" %(g.index_4_stop_loss_by_price, get_security_info(g.index_4_stop_loss_by_price).display_name))

    log.info("是否开启大盘三黑鸦止损: %s" %(g.is_market_stop_loss_by_3_black_crows))
    if g.is_market_stop_loss_by_3_black_crows:
        log.info("大盘三黑鸦止损判定指数: %s - %s" %(g.index_4_stop_loss_by_3_black_crows, get_security_info(g.index_4_stop_loss_by_3_black_crows).display_name))
        log.info("三黑鸦止损开启需要当日大盘为跌的分钟计数达到: %d" %(g.dst_drop_minute_count))

    log.info("是否根据28指数值实时进行止损: %s" %(g.is_market_stop_loss_by_28_index))
    if g.is_market_stop_loss_by_28_index:
        log.info("根据28指数止损需要当日28指数连续为跌的分钟计数达到: %d" %(g.dst_minute_count_28index_drop))        

    log.info("是否开启个股止损: %s" %(g.is_stock_stop_loss))
    log.info("是否开启个股止盈: %s" %(g.is_stock_stop_profit))
    
    log.info("是否开启资金曲线保护: %s" %(g.is_equity_curve_protect))

# 重置当日参数，仅针对需要当日需要重置的参数
def reset_day_param():
    if g.is_market_stop_loss_by_price:
        # 重置当日大盘价格止损状态
        g.is_day_stop_loss_by_price = False

    # 重置三黑鸦状态
    g.is_last_day_3_black_crows = False
    if g.is_market_stop_loss_by_3_black_crows:
        g.cur_drop_minute_count = 0
        
    if g.is_market_stop_loss_by_28_index:
        g.minute_count_28index_drop = 0

    if g.is_stock_stop_loss or g.is_stock_stop_profit:
        # 清空当日个股250天内最大的3日涨幅的缓存
        g.pct_change.clear()

    # 重置资金曲线保护状态    
    if g.is_equity_curve_protect:
        g.is_day_curve_protect = False

# 按分钟回测
def handle_data(context, data):
    if g.is_market_stop_loss_by_price:
        if market_stop_loss_by_price(context, g.index_4_stop_loss_by_price):
            return

    if g.is_market_stop_loss_by_3_black_crows:
        if market_stop_loss_by_3_black_crows(context, g.index_4_stop_loss_by_3_black_crows, g.dst_drop_minute_count):
            return

    if g.is_market_stop_loss_by_28_index:
        if market_stop_loss_by_28_index(context, g.dst_minute_count_28index_drop):
            return

    if g.is_stock_stop_loss:
        stock_stop_loss(context, data)

    if g.is_stock_stop_profit:
        stock_stop_profit(context, data)
        
    if g.is_equity_curve_protect:
        if equity_curve_protect(context):
            return

    # 获得当前时间
    hour = context.current_dt.hour
    minute = context.current_dt.minute

    # 每天尾盘记录总资产
    if g.is_equity_curve_protect:
        if hour == 14 and minute == 59:
            g.value_list.append(context.portfolio.total_value)

    # 每天指定时间检查是否调仓并处理
    if hour == g.adjust_position_hour and minute == g.adjust_position_minute:
        do_handle_data(context, data)

def do_handle_data(context, data):
    log.info("调仓日计数 [%d]" %(g.day_count))
    # 回看指数前20天的涨幅
    gr_index2 = get_growth_rate(g.index2)
    gr_index8 = get_growth_rate(g.index8)
    log.info("当前%s指数的20日涨幅 [%.2f%%]" %(get_security_info(g.index2).display_name, gr_index2*100))
    log.info("当前%s指数的20日涨幅 [%.2f%%]" %(get_security_info(g.index8).display_name, gr_index8*100))

    if gr_index2 <= g.index_growth_rate and gr_index8 <= g.index_growth_rate:
        clear_position(context)
        g.day_count = 0
    else: #if  gr_index2 > g.index_growth_rate or ret_index8 > g.index_growth_rate:
        if g.day_count % g.period == 0 and g.day_count >= 0:
            log.info("==> 满足条件进行调仓")
            buy_stocks = g.stocks
            log.info("选股后可买股票: %s" %(buy_stocks))
            adjust_position(context, buy_stocks)
        g.day_count += 1

def market_stop_loss_by_price(context, index):
    # 大盘指数前130日内最高价超过最低价2倍，则清仓止损
    # 基于历史数据判定，因此若状态满足，则当天都不会变化
    # 增加此止损，回撤降低，收益降低

    if not g.is_day_stop_loss_by_price:
        h = attribute_history(index, 160, unit='1d', fields=('close', 'high', 'low'), skip_paused=True)
        low_price = h.low.min()
        high_price = h.high.max()
        #if high_price > 2 * low_price:
        if high_price > 2.2 * low_price \
            and h['close'][-1] < h['close'][-4] \
            and h['close'][-1]> h['close'][-100]:
            # 当日第一次输出日志
            log.info("==> 大盘止损，%s指数前130日内最高价超过最低价2倍, 最高价: %f, 最低价: %f" %(get_security_info(index).display_name, high_price, low_price))
            g.is_day_stop_loss_by_price = True

    if g.is_day_stop_loss_by_price:
        clear_position(context)
        g.day_count = 0

    return g.is_day_stop_loss_by_price

# 资金曲线保护  
def equity_curve_protect(context):
    if not g.is_day_curve_protect:
        cur_value = context.portfolio.total_value
        if len(g.value_list) >= 20:
            last_value = g.value_list[-20]
            #avg_value = sum(g.value_list[-20:]) / 20
            if cur_value < last_value*0.99:
                log.info("==> 启动资金曲线保护, 20日前资产: %f, 当前资产: %f" %(last_value, cur_value))
                g.is_day_curve_protect = True

    if g.is_day_curve_protect:
        clear_position(context)
        del g.value_list[:]
        g.day_count = -1

    return g.is_day_curve_protect

def market_stop_loss_by_3_black_crows(context, index, n):
    # 前日三黑鸦，累计当日大盘指数涨幅<0的分钟计数
    # 如果分钟计数超过值n，则开始进行三黑鸦止损
    # 避免无效三黑鸦乱止损
    if g.is_last_day_3_black_crows:
        if get_growth_rate(index, 1) < 0:
            g.cur_drop_minute_count += 1

        if g.cur_drop_minute_count >= n:
            if g.cur_drop_minute_count == n:
                log.info("==> 当日%s增幅 < 0 已超过%d分钟，执行三黑鸦止损" %(get_security_info(index).display_name, n))

            clear_position(context)
            g.day_count = 0
            return True

    return False

def is_3_black_crows(stock):
    # talib.CDL3BLACKCROWS

    # 三只乌鸦说明来自百度百科
    # 1. 连续出现三根阴线，每天的收盘价均低于上一日的收盘
    # 2. 三根阴线前一天的市场趋势应该为上涨
    # 3. 三根阴线必须为长的黑色实体，且长度应该大致相等
    # 4. 收盘价接近每日的最低价位
    # 5. 每日的开盘价都在上根K线的实体部分之内；
    # 6. 第一根阴线的实体部分，最好低于上日的最高价位
    #
    # 算法
    # 有效三只乌鸦描述众说纷纭，这里放宽条件，只考虑1和2
    # 根据前4日数据判断
    # 3根阴线跌幅超过4.5%（此条件忽略）

    h = attribute_history(stock, 4, '1d', ('close','open'), skip_paused=True, df=False)
    h_close = list(h['close'])
    h_open = list(h['open'])

    if len(h_close) < 4 or len(h_open) < 4:
        return False
    
    # 一阳三阴
    if h_close[-4] > h_open[-4] \
        and (h_close[-1] < h_open[-1] and h_close[-2]< h_open[-2] and h_close[-3] < h_open[-3]):
        #and (h_close[-1] < h_close[-2] and h_close[-2] < h_close[-3]) \
        #and h_close[-1] / h_close[-4] - 1 < -0.045:
        return True
    return False
    

def market_stop_loss_by_28_index(context, count):
    # 回看指数前20天的涨幅
    gr_index2 = get_growth_rate(g.index2)
    gr_index8 = get_growth_rate(g.index8)

    if gr_index2 <= g.index_growth_rate and gr_index8 <= g.index_growth_rate:
        if (g.minute_count_28index_drop == 0):
            log.info("当前二八指数的20日涨幅同时低于[%.2f%%], %s指数: [%.2f%%], %s指数: [%.2f%%]" \
                %(g.index_growth_rate*100, get_security_info(g.index2).display_name, gr_index2*100, get_security_info(g.index8).display_name, gr_index8*100))

            #log.info("当前%s指数的20日涨幅 [%.2f%%]" %(get_security_info(g.index2).display_name, gr_index2*100))
            #log.info("当前%s指数的20日涨幅 [%.2f%%]" %(get_security_info(g.index8).display_name, gr_index8*100))
        g.minute_count_28index_drop += 1
    else:
        # 不连续状态归零
        if g.minute_count_28index_drop < count:
            g.minute_count_28index_drop = 0

    if g.minute_count_28index_drop >= count:
        if g.minute_count_28index_drop == count:
            log.info("==> 当日%s指数和%s指数的20日增幅低于[%.2f%%]已超过%d分钟，执行28指数止损" \
                %(get_security_info(g.index2).display_name, get_security_info(g.index8).display_name, g.index_growth_rate*100, count))

        clear_position(context)
        g.day_count = 0
        return True
        
    return False

# 个股止损
def stock_stop_loss(context, data):
    for stock in context.portfolio.positions.keys():
        cur_price = data[stock].close

        if g.last_high[stock] < cur_price:
            g.last_high[stock] = cur_price

        threshold = get_stop_loss_threshold(stock, g.period)
        #log.debug("个股止损阈值, stock: %s, threshold: %f" %(stock, threshold))
        if cur_price < g.last_high[stock] * (1 - threshold):
            log.info("==> 个股止损, stock: %s, cur_price: %f, last_high: %f, threshold: %f" 
                %(stock, cur_price, g.last_high[stock], threshold))

            position = context.portfolio.positions[stock]
            if close_position(position):
                g.day_count = 0

# 个股止盈
def stock_stop_profit(context, data):
    for stock in context.portfolio.positions.keys():
        position = context.portfolio.positions[stock]
        cur_price = data[stock].close
        threshold = get_stop_profit_threshold(stock, g.period)
        #log.debug("个股止盈阈值, stock: %s, threshold: %f" %(stock, threshold))
        if cur_price > position.avg_cost * (1 + threshold):
            log.info("==> 个股止盈, stock: %s, cur_price: %f, avg_cost: %f, threshold: %f" 
                %(stock, cur_price, g.last_high[stock], threshold))

            position = context.portfolio.positions[stock]
            if close_position(position):
                g.day_count = 0

# 获取个股前n天的m日增幅值序列
# 增加缓存避免当日多次获取数据
def get_pct_change(security, n, m):
    pct_change = None
    if security in g.pct_change.keys():
        pct_change = g.pct_change[security]
    else:
        h = attribute_history(security, n, unit='1d', fields=('close'), skip_paused=True)
        pct_change = h['close'].pct_change(m) # 3日的百分比变比（即3日涨跌幅）
        g.pct_change[security] = pct_change
    return pct_change
        
# 计算个股回撤止损阈值
# 即个股在持仓n天内能承受的最大跌幅
# 算法：(个股250天内最大的n日跌幅 + 个股250天内平均的n日跌幅)/2
# 返回正值
def get_stop_loss_threshold(security, n = 3):
    pct_change = get_pct_change(security, 250, n)
    #log.debug("pct of security [%s]: %s", pct)
    maxd = pct_change.min()
    #maxd = pct[pct<0].min()
    avgd = pct_change.mean()
    #avgd = pct[pct<0].mean()
    # maxd和avgd可能为正，表示这段时间内一直在增长，比如新股
    bstd = (maxd + avgd) / 2

    # 数据不足时，计算的bstd为nan
    if not isnan(bstd):
        if bstd != 0:
            return abs(bstd)
        else:
            # bstd = 0，则 maxd <= 0
            if maxd < 0:
                # 此时取最大跌幅
                return abs(maxd)

    return 0.079 # 默认配置回测止损阈值最大跌幅为-9.9%，阈值高貌似回撤降低

# 计算个股止盈阈值
# 算法：个股250天内最大的n日涨幅
# 返回正值
def get_stop_profit_threshold(security, n = 3):
    pct_change = get_pct_change(security, 250, n)
    maxr = pct_change.max()
    
    # 数据不足时，计算的maxr为nan
    # 理论上maxr可能为负
    if (not isnan(maxr)) and maxr != 0:
        return abs(maxr)
    return 0.30 # 默认配置止盈阈值最大涨幅为30%

# 获取股票n日以来涨幅，根据当前价计算
# n 默认20日
def get_growth_rate(security, n=20):
    lc = get_close_price(security, n)
    #c = data[security].close
    c = get_close_price(security, 1, '1m')
    
    if not isnan(lc) and not isnan(c) and lc != 0:
        return (c - lc) / lc
    else:
        log.error("数据非法, security: %s, %d日收盘价: %f, 当前价: %f" %(security, n, lc, c))
        return 0

# 获取前n个单位时间当时的收盘价
def get_close_price(security, n, unit='1d'):
    return attribute_history(security, n, unit, ('close'), True)['close'][0]

# 开仓，买入指定价值的证券
# 报单成功并成交（包括全部成交或部分成交，此时成交量大于0），返回True
# 报单失败或者报单成功但被取消（此时成交量等于0），返回False
def open_position(security, value):
    order = order_target_value_(security, value)
    if order != None and order.filled > 0:
        # 报单成功并有成交则初始化最高价
        cur_price = get_close_price(security, 1, '1m')
        g.last_high[security] = cur_price
        return True
    return False

# 平仓，卖出指定持仓
# 平仓成功并全部成交，返回True
# 报单失败或者报单成功但被取消（此时成交量等于0），或者报单非全部成交，返回False
def close_position(position):
    security = position.security
    order = order_target_value_(security, 0) # 可能会因停牌失败
    if order != None:
        if order.filled > 0:
            # 只要有成交，无论全部成交还是部分成交，则统计盈亏
            g.trade_stat.watch(security, order.filled, position.avg_cost, position.price)

        if order.status == OrderStatus.held and order.filled == order.amount:
            # 全部成交则删除相关证券的最高价缓存
            if security in g.last_high:
                g.last_high.pop(security)
            else:
                log.warn("last high price of %s not found" %(security))
            return True

    return False

# 清空卖出所有持仓
def clear_position(context):
    if context.portfolio.positions:
        log.info("==> 清仓，卖出所有股票")
        for stock in context.portfolio.positions.keys():
            position = context.portfolio.positions[stock]
            close_position(position)

# 自定义下单
# 根据Joinquant文档，当前报单函数都是阻塞执行，报单函数（如order_target_value）返回即表示报单完成
# 报单成功返回报单（不代表一定会成交），否则返回None
def order_target_value_(security, value):
    if value == 0:
        log.debug("Selling out %s" % (security))
    else:
        log.debug("Order %s to value %f" % (security, value))
        
    # 如果股票停牌，创建报单会失败，order_target_value 返回None
    # 如果股票涨跌停，创建报单会成功，order_target_value 返回Order，但是报单会取消
    # 部成部撤的报单，聚宽状态是已撤，此时成交量>0，可通过成交量判断是否有成交
    return order_target_value(security, value)


# 过滤停牌股票
def filter_paused_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].paused]

# 过滤ST及其他具有退市标签的股票
def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list 
        if not current_data[stock].is_st 
        and 'ST' not in current_data[stock].name 
        and '*' not in current_data[stock].name 
        and '退' not in current_data[stock].name]
        
# 过滤涨停的股票
def filter_limitup_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    
    # 已存在于持仓的股票即使涨停也不过滤，避免此股票再次可买，但因被过滤而导致选择别的股票
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys() 
        or last_prices[stock][-1] < current_data[stock].high_limit]
    #return [stock for stock in stock_list if stock in context.portfolio.positions.keys() 
    #    or last_prices[stock][-1] < current_data[stock].high_limit * 0.995]

# 过滤跌停的股票
def filter_limitdown_stock(context, stock_list):
    last_prices = history(1, unit='1m', field='close', security_list=stock_list)
    current_data = get_current_data()
    
    return [stock for stock in stock_list if stock in context.portfolio.positions.keys() 
        or last_prices[stock][-1] > current_data[stock].low_limit]
    #return [stock for stock in stock_list if last_prices[stock][-1] > current_data[stock].low_limit]
    #return [stock for stock in stock_list if stock in context.portfolio.positions.keys() 
    #    or last_prices[stock][-1] > current_data[stock].low_limit * 1.005]
    
# 过滤黑名单股票
def filter_blacklist_stock(context, stock_list):
    blacklist = get_blacklist()
    return [stock for stock in stock_list if stock not in blacklist]

# 过滤创业版股票
def filter_gem_stock(context, stock_list):
    return [stock for stock in stock_list if stock[0:3] != '300']

# 过滤20日增长率为负的股票
def filter_by_growth_rate(stock_list, n):
    return [stock for stock in stock_list if get_growth_rate(stock, n) > 0]

# 股票评分
def rank_stocks(data, stock_list):
    dst_stocks = {}
    for stock in stock_list:
        h = attribute_history(stock, 130, unit='1d', fields=('close', 'high', 'low'), skip_paused=True)
        low_price_130 = h.low.min()
        high_price_130 = h.high.max()

        avg_15 = data[stock].mavg(15, field='close')
        cur_price = data[stock].close

        #avg_15 = h['close'][-15:].mean()
        #cur_price = get_close_price(stock, 1, '1m')

        score = (cur_price-low_price_130) + (cur_price-high_price_130) + (cur_price-avg_15)
        #score = ((cur_price-low_price_130) + (cur_price-high_price_130) + (cur_price-avg_15)) / cur_price
        dst_stocks[stock] = score
        
    df = pd.DataFrame(dst_stocks.values(), index=dst_stocks.keys())
    df.columns = ['score']
    df = df.sort(columns='score', ascending=True)
    return df.index


# 过滤新股
def filter_new_stock(stock_list):
    stocks = get_all_securities(['stock'])
    stocks = stocks[(context.current_dt.date() - stocks.start_date) > datetime.timedelta(90)].index
    return stocks

# 选股
# 选取指定数目的小市值股票，再进行过滤，最终挑选指定可买数目的股票
def pick_stocks(context, data):
    q = query(valuation.code)
    if g.pick_by_pe:
        q = q.filter(
            valuation.pe_ratio > g.min_pe, 
            valuation.pe_ratio < g.max_pe
            )

    if g.pick_by_eps:
        q = q.filter(
            indicator.eps > g.min_eps,
            #valuation.turnover_ratio > 3
            )

    q = q.order_by(
                valuation.market_cap.asc()
            ).limit(
                g.pick_stock_count
            )
    
    df = get_fundamentals(q)
    stock_list = list(df['code'])

    if g.filter_gem:
        stock_list = filter_gem_stock(context, stock_list)
        
    if g.filter_blacklist:
        stock_list = filter_blacklist_stock(context, stock_list)
        
    stock_list = filter_paused_stock(stock_list)
    stock_list = filter_st_stock(stock_list)
    stock_list = filter_limitup_stock(context, stock_list)
    stock_list = filter_limitdown_stock(context, stock_list)

    # 根据20日股票涨幅过滤效果不好，故注释
    #stock_list = filter_by_growth_rate(stock_list, 20)
    
    if g.is_rank_stock:
        if len(stock_list) > g.rank_stock_count:
            stock_list = stock_list[:g.rank_stock_count]

        #log.debug("评分前备选股票: %s" %(stock_list))
        if len(stock_list) > 0:
            stock_list = rank_stocks(data, stock_list)
        #log.debug("评分后备选股票: %s" %(stock_list))
    
    # 选取指定可买数目的股票
    if len(stock_list) > g.buy_stock_count:
        stock_list = stock_list[:g.buy_stock_count]
    return stock_list

# 根据待买股票创建或调整仓位
# 对于因停牌等原因没有卖出的股票则继续持有
# 始终保持持仓数目为g.buy_stock_count
def adjust_position(context, buy_stocks):
    for stock in context.portfolio.positions.keys():
        if stock not in buy_stocks:
            log.info("stock [%s] in position is not buyable" %(stock))
            position = context.portfolio.positions[stock]
            close_position(position)
        else:
            log.info("stock [%s] is already in position" %(stock))
    
    # 根据股票数量分仓
    # 此处只根据可用金额平均分配购买，不能保证每个仓位平均分配
    position_count = len(context.portfolio.positions)
    if g.buy_stock_count > position_count:
        value = context.portfolio.cash / (g.buy_stock_count - position_count)

        for stock in buy_stocks:
            if context.portfolio.positions[stock].total_amount == 0:
                if open_position(stock, value):
                    if len(context.portfolio.positions) == g.buy_stock_count:
                        break


