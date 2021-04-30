该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/13213

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

# 导入函数库
import jqdata
import math
import statsmodels.api as sm
from pandas.stats.api import ols

# 初始化函数，设定基准等等
def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 输出内容到日志 log.info()
    log.info('初始函数开始运行且全局只运行一次')
    ### 股票相关设定 ###
    # 股票类每笔交易时的手续费是：买入时佣金万分之三，卖出时佣金万分之三加千分之一印花税, 每笔交易佣金最低扣5块钱
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    
    g.stock_num = 10                    # 最大持股数
    g.stock_value_ratio = 0.33          # 单支股票的价值占比不能超过1/3
    # g.overweight_threshold = 50       # 加仓时的价格阈值
    
    g.days_history = 60                 # 获取历史数据的天数
    g.days_money_flow = 5               # 获取资金流向的天数
    g.days_money_flow_threshold = 4     # 资金流向为正的天数的阈值
    g.days_money_flow_2 = 60            # 获取资金流向的天数_2
    g.price_amplitude = 0.1             # 股价振幅（最高价-最低价）/ 区间起始价
    g.mean_diff_5_30_threshold = 0.1    # 股价的均线之间的差别的阈值
    g.mean_diff_30_60_threshold = 0.05  # 股价的均线之间的差别的阈值
    g.price_increase_threshold = 0.2    # 股价涨幅阈值
    
    # 开盘前运行
    run_daily(before_market_open, time='before_open', reference_security='000300.XSHG') 
    # 开盘时运行
    run_daily(market_open, time='open', reference_security='000300.XSHG')
    # 收盘后运行
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')
 
    

    
## 开盘前运行函数     
def before_market_open(context):
    current_data = get_current_data()
    
    # 候选集
    #option_list = ['600018.XSHG']   # 上港集团
    #option_list = ['601988.XSHG']   # 中国银行
    #option_list = ['601989.XSHG']   # 中国重工
    #option_list = ['000100.XSHE']   # TCL集团
    #option_list = ['000157.XSHE']   # 中联重科
    #option_list = ['000538.XSHE']   # 云南白药
    option_list = get_index_stocks('000300.XSHG')   # 沪深300成分股
    #option_list = list(get_all_securities(['stock']).index)  # 所有股票
    
    # 看有没有股票被移除沪深300
    #for stock in context.portfolio.positions:
    #    if stock not in option_list:
    #        print '%s(%s)被移除沪深300成分股了' % (stock, current_data[stock].name)
    
    # 过滤st股票
    option_list = filter_st_stock(option_list)
    
    # 过滤停牌的股票
    option_list = filter_paused_stock(option_list)
    
    # 过滤银行股
    option_list = filter_bank_stock(option_list)
    
    # 过滤创业板
    option_list = filter_300_stock(option_list)

    g.buy_list = []
    g.sell_list = []

    today = context.current_dt.strftime("%Y-%m-%d")
    
    # 过滤符合卖出条件的股票
    for stock in context.portfolio.positions:
        if sell_check(context, stock):
            g.sell_list.append(stock)
            print '%14s%14s%14s%14s' % (stock, current_data[stock].name, today, '卖出点') 

    # 过滤出符合买入条件的股票
    for stock in option_list:
        if stock not in g.sell_list and buy_check(context, stock):
            g.buy_list.append(stock)
            print '%14s%14s%14s%14s' % (stock, current_data[stock].name, today, '买入点')

    # 按照庄估值排序
    #g.buy_list = sort_by_cow_value(context, g.buy_list)
    
    # 微信发汇总信息
    send_wx_msg(context, g.buy_list, g.sell_list)
        
## 开盘时运行函数
def market_open(context):
    current_data = get_current_data()
    
    # 卖出
    for stock in g.sell_list:
        # 已有持仓，则清仓
        if stock in context.portfolio.positions:
            order_target(stock, 0)
    
    if context.portfolio.available_cash < 5000 or g.stock_num == len(context.portfolio.positions):
        #print '可用资金不足或者持仓数已满，可用资金=%s，持仓数=%s' % (context.portfolio.available_cash, len(context.portfolio.positions))
        return
    
    # 单位资金
    cash_unit = context.portfolio.available_cash / (g.stock_num - len(context.portfolio.positions))
    
    # 买入
    for stock in g.buy_list:
        # 已有持仓，看需不需要补仓
        if stock in context.portfolio.positions:
            position = context.portfolio.positions[stock]
            if (position.value / context.portfolio.total_value) < g.stock_value_ratio:
                # 可加仓
                target_amount = int(cash_unit / (position.price * 100)) * 100
                order_target(stock, target_amount)
            else:
                print '%s(%s)的仓位已满' % (stock, current_data[stock].name)
        # 未有持仓，看有没有资金建仓
        else:
            if context.portfolio.available_cash >= cash_unit:
                target_amount = int(cash_unit / (current_data[stock].last_price * 100)) * 100
                order_target(stock, target_amount)
            else:
                print '没有足够的可用资金来买%s(%s)了' % (stock, current_data[stock].name)
 
## 收盘后运行函数  
def after_market_close(context):
    # log.info(str('函数运行时间(after_market_close):'+str(context.current_dt.time())))
    # 得到当天所有成交记录
    trades = get_trades()
    for _trade in trades.values():
        log.info('成交记录：'+str(_trade))
    # log.info('一天结束')
    # log.info('##############################################################')

# 微信发买入、卖出股票名单
def send_wx_msg(context, buy_list, sell_list):
    current_data = get_current_data()
    msg = '今天要卖出的股票:'
    if sell_list:
        for stock in sell_list:
            msg += current_data[stock].name + ' '
        msg += '。'
    else:
        msg += '无。'
    msg += '今天要买入的股票:'
    if buy_list:
        cash_unit = context.portfolio.available_cash / g.stock_num
        if g.stock_num > len(context.portfolio.positions):
            cash_unit = context.portfolio.available_cash / (g.stock_num - len(context.portfolio.positions))
        for stock in buy_list:
            target_amount = int(cash_unit / (current_data[stock].last_price * 100)) * 100
            msg += current_data[stock].name + '(' + bytes(target_amount) + '股) '
        msg += '。'
    else:
        msg += '无。'
    #print msg
    send_message(msg)

# 买入点判断
def buy_check(context, stock):
    return buy_check_volume_increase_and_price_amplitude(context, stock)
    
# 卖出点判断
def sell_check(context, stock):
    current_data = get_current_data()
    if current_data[stock].paused:
        return False
    if sell_check_mean_price(context, stock, 0.1) and sell_check_turnover_ratio(context, stock):
        return True
    if sell_check_mean_price(context, stock, 0.2):
        return True
    return False
    #return not current_data[stock].paused and sell_check_rsrs(context, stock)
    
# 买入点-60天区间价格波动小于10%
def buy_check_price_amplitude(context, stock, days = 60, threshold = 0.1):
    current_data = get_current_data()
    today = context.current_dt.strftime("%Y-%m-%d")
    h = attribute_history(stock, days, '1d', ['open', 'close', 'high', 'low', 'volume', 'money'], df=False, skip_paused=True)
    if len(h['open']) < days:
        print '%s历史数据不足%s天' % (today, days)
        return False
    amplitude = (max(h['high']) - min(h['low'])) / h['open'][0]
    # 最近X天的价格波动小于阈值
    if amplitude < threshold: 
        print '%s %s %s 买入点(区间价格波动小), price_amplitude=%s' % (stock, current_data[stock].name, today, round(amplitude, 3))
        return True
    else:
        return False
        
# 买入点-地量（连续18周成交量小于最近4年内天量的10%）
def buy_check_mean_volume_small(context, stock, weeks=18, history_weeks=150, threshold=0.1):
    current_data = get_current_data()
    today = context.current_dt.strftime("%Y-%m-%d")
    h = attribute_history(stock, history_weeks, '5d', ['open', 'close', 'high', 'low', 'volume', 'money'], df=False, skip_paused=True)
    if len(h['open']) < weeks:
        print '%s历史数据不足%s周' % (today, weeks)
        return False
    max_volume_latest = max(h['volume'][-weeks:])
    max_volume_history = max(h['volume'])
    # (底部成交量要缩至顶部最高成交量的20%以内)
    if max_volume_latest < max_volume_history * threshold: 
        print '%s %s %s 买入点(地量), max_volume_latest=%s万, max_volume_history=%s万, ratio=%s' % (stock, current_data[stock].name, today, int(max_volume_latest / 10000), int(max_volume_history / 10000), round(max_volume_latest / max_volume_history, 2))
        return True
    else:
        return False
        
# 单日成交量大于该股的前五日移动平均成交量2.5倍，大于前10日移动平均成交量3倍
def buy_check_volume_increase(context, stock):
    current_data = get_current_data()
    today = context.current_dt.strftime("%Y-%m-%d")
    h = attribute_history(stock, 11, '1d', ['open', 'close', 'high', 'low', 'volume', 'money'], df=False, skip_paused=True)
    volume = h['volume'][-1]
    volume_mean_5 = mean(h['volume'][-6:-1])
    volume_mean_10 = mean(h['volume'][-11:-1])
    if volume > volume_mean_5 * 2.5 and volume > volume_mean_10 * 3:
        print '%s %s %s 成交量放大, volume=%sw, mean_5=%sw, mean_10=%sw' % (stock, current_data[stock].name, today, round(volume / 10000, 2), round(volume_mean_5 / 10000, 2), round(volume_mean_10 / 10000, 2))
        return True
    else:
        return False
        
# 找到昨天之前成交量大于昨天的成交量（0.8倍），这个区间的天数大于30天 
# 昨天单日成交量大于该区间的平均成交量的2倍
# 区间价格波动小于10%
def buy_check_volume_increase_and_price_amplitude(context, stock):
    current_data = get_current_data()
    if current_data[stock].paused:
        return False
    today = context.current_dt.strftime("%Y-%m-%d")
    h = attribute_history(stock, 270, '1d', ['open', 'close', 'high', 'low', 'volume', 'money'], df=False, skip_paused=True)
    volume_yesterday = h['volume'][-1]
    
    # 昨日收盘价要高于开盘价
    if h['close'][-1] < h['open'][-1]:
        return False

    # 找到昨天之前成交量大于昨天的成交量（0.9倍），这个区间的天数大于30天
    start = 0
    end = -1
    for i in range(1, h['volume'].size):
        index = -(i + 1)
        if h['volume'][index] > volume_yesterday * 0.8:
            start = index + 1
            break
    if start == 0 or (end - start) < 30:
        return False
    # print 'date=%s, start=%s' % (today, start)

    # 昨天单日成交量大于该区间的平均成交量的2倍
    volume_mean = mean(h['volume'][start:end])
    volume_mean_5 = mean(h['volume'][-6:-1])
    #volume_mean_10 = mean(h['volume'][-11:-1])
    if volume_yesterday < volume_mean * 2.5 or volume_yesterday < volume_mean_5 * 2.5:
       return False
    # print 'volume_mean=%s, volume_yesterday=%s' % (volume_mean, volume_yesterday)
    
    # 区间价格波动小于10%
    price_max = max(h['high'][start:end])
    price_min = min(h['low'][start:end])
    price_amplitude = (price_max - price_min) / h['open'][start]
    # print 'min=%s, max=%s, open=%s, amplitude=%s' % (price_min, price_max, h['open'][start], price_amplitude)
    if price_amplitude > 0.1:
        return False
       
    # stock_info = get_security_info(stock)
    # print '%s %s %s 成交量放大，且之前%s天价格波动小, volume=%sw, volume_mean=%sw, price_amplitude=%s' % (stock, stock_info.display_name, today, end - start, round(volume_yesterday / 10000, 2), round(volume_mean / 10000, 2), round(price_amplitude, 2))
    return True
    
# 卖出点-均线（5日线超过10日线10%，10日线超过30日线10%）
def sell_check_mean_price(context, stock, threshold):
    current_data = get_current_data()
    # 只对在持股池中的股票判断卖出点
    if stock not in context.portfolio.positions:
        return False
    
    h = attribute_history(stock, 31, '1d', ['open', 'close', 'high', 'low', 'volume', 'money'], df=False, skip_paused=True)
        
    # 求5日线、10日线、30日线
    mean_5 = mean(h['close'][-5:])
    mean_10 = mean(h['close'][-10:])
    mean_30 = mean(h['close'][-30:])
    diff_5_10 = (mean_5 - mean_10) / mean_10
    diff_5_30 = (mean_5 - mean_30) / mean_30
    diff_10_30 = (mean_10 - mean_30) / mean_30
    
    # 求昨天的求5日线、10日线、30日线
    yes_mean_5 = mean(h['close'][-6:-1])
    yes_mean_10 = mean(h['close'][-11:-1])
    yes_mean_30 = mean(h['close'][-31:-1])
    yes_diff_5_10 = (yes_mean_5 - yes_mean_10) / yes_mean_10
    yes_diff_5_30 = (yes_mean_5 - yes_mean_30) / yes_mean_30
    yes_diff_10_30 = (yes_mean_10 - yes_mean_30) / yes_mean_30
    
    return diff_5_30 > threshold
    #return diff_5_30 > 0.15 and h['close'][-1] <= mean_5
    #return diff_5_30 > 0.15 and diff_5_30 <= yes_diff_5_30
    
    # 取上证指数
    #sh = attribute_history('000001.XSHG', 1, '1d', ['open', 'close', 'high', 'low', 'volume', 'money'], df=False)
    
    #hold_days = cal_hold_time(context, stock)
    #price_increase_pct = cal_increase_pct(context, stock)
    # 未盈利的股票不卖
    #if price_increase_pct <= 0:
    #    return False

    #ratio = math.log((hold_days / 10 + 10), 10) * math.log((price_increase_pct * 10 + 10), 10) * math.log(sh['close'][0], 10)

    #ratio = price_increase_pct / math.log(hold_days, 2)
    #pct = ratio / diff_5_30
    #pct = math.log(price_increase_pct) * diff_5_30
    #pct = diff_5_30 * ratio
    
    #if diff_5_30 > 0:
    #    print '%12s%12s%12s%12s%4s' % (current_data[stock].name, round(price_increase_pct, 5), round(diff_5_30, 5), round(pct, 3), hold_days)

    # 5日线超过10日线10%，10日线超过30日线10%
    #return diff_5_10 >= 0.1 and diff_10_30 >= 0.15
    #return diff_5_30 > 0.15 and yes_diff_5_30 > 0.15 and diff_5_30 < yes_diff_5_30
    #return diff_5_30 > 0.15 and yes_diff_5_30 > 0.15
    
# 计算股票的持仓时间
def cal_hold_time(context, stock):
    if stock not in context.portfolio.positions:
        return 0
    start = context.portfolio.positions[stock].init_time
    end = context.current_dt
    prices = get_price(stock, start_date=start, end_date = end, frequency='daily', skip_paused=True)
    return prices.iloc[:,0].size
    
# 计算股票的涨幅
def cal_increase_pct(context, stock):
    if stock not in context.portfolio.positions:
        return 0
    current_price = context.portfolio.positions[stock].price
    avg_cost = context.portfolio.positions[stock].avg_cost
    return (current_price - avg_cost) / avg_cost

# 卖出点-换手率
def sell_check_turnover_ratio(context, stock):
    yesterday = (context.current_dt + timedelta(days = -1)).strftime("%Y-%m-%d")
    q = query(
        valuation
    ).filter(
        valuation.code == stock,
        valuation.turnover_ratio > 15
    )
    df = get_fundamentals(q, yesterday)
    return not df.empty

# 卖出点-RSRS
# https://www.joinquant.com/post/10272?tag=algorithm
def sell_check_rsrs(context, stock):
    N = 18
    M = 200
    threshold = -0.7
    ans = []
    ans_rightdev= []
    prices = get_price(stock, count=M, end_date=context.current_dt, frequency='1d', fields=['high', 'low'], skip_paused=True)
    highs = prices.high
    lows = prices.low
    for i in range(len(highs))[N:]:
        data_high = highs.iloc[i-N+1:i+1]
        data_low = lows.iloc[i-N+1:i+1]
        X = sm.add_constant(data_low)
        model = sm.OLS(data_high,X)
        results = model.fit()
        ans.append(results.params[1])
        #计算r2
        ans_rightdev.append(results.rsquared)
        
    # 计算标准化的RSRS指标
    # 计算均值序列    
    section = ans[-M:]
    # 计算均值序列
    mu = np.mean(section)
    # 计算标准化RSRS指标序列
    sigma = np.std(section)
    zscore = (section[-1]-mu)/sigma  
    #计算右偏RSRS标准分
    zscore_rightdev= zscore*ans[-1]*ans_rightdev[-1]
    
    if zscore_rightdev < threshold:
        return True
    else:
        return False
    
# 按庄股值排序
def sort_by_cow_value(context, stocks):
    cow_value_dict=dict()
    for stock in stocks:
        cow_value_dict[stock] = cow_stock_value(context, stock)
    tmp = sorted(cow_value_dict.items(), key=lambda item:item[1],reverse=True)
    stock_list = []
    for t in tmp:
        stock_list.append(t[0])
    return stock_list
    
# 庄股值计算    
def cow_stock_value(context, stock) :
    today = context.current_dt.strftime("%Y-%m-%d")
    q = query(valuation).filter(valuation.code == stock)
    pb = get_fundamentals(q, today)['pb_ratio'][0]
    cap = get_fundamentals(q, today)['circulating_market_cap'][0]
    if cap > 100:
        return 0
    num_fall = fall_money_day_3line(context, stock, 120, 20, 60, 160)
    num_cross = money_5_cross_60(context, stock, 120, 5, 160)
    return (num_fall * num_cross) / (pb *(cap ** 0.5))

# 计算脉冲（1.0版本）                 
def money_5_cross_60(context, stock, n, n1 = 5, n2 = 60):
    today = context.current_dt.strftime("%Y-%m-%d")
    if  not (n2 > n1 ) : 
        log.info("fall_money_day 参数错误")
        return 0 
    stock_m = get_price(stock, count=n+n2+1, end_date=today, frequency='daily', fields=['money'], skip_paused=True)
    i=0
    count=0
    while i<n:
        money_MA60=stock_m['money'][i+1:n2+i].mean()
        money_MA60_before=stock_m['money'][i:n2-1+i].mean()
        money_MA5=stock_m['money'][i+1+n2-n1:n2+i].mean()
        money_MA5_before=stock_m['money'][i+n2-n1:n2-1+i].mean()
        if (money_MA60_before-money_MA5_before)*(money_MA60-money_MA5)<0: 
            count=count+1
        i=i+1    
    return count

# 3条移动平均线计算缩量 
def fall_money_day_3line(context, stock,n,n1=20,n2=60,n3=120):
    today = context.current_dt.strftime("%Y-%m-%d")
    if  not ( n3>n2 and n2 >n1 ) : 
        log.info("fall_money_day 参数错误")
        return 0 
    stock_m=get_price(stock,count=n+n3,end_date=today,frequency='daily', \
                      fields=['money'], skip_paused=True)
    #print(len(stock_m)) 
    i=0
    count=0
    while i<n:
        money_MA200=stock_m['money'][i:n3-1+i].mean()
        money_MA60=stock_m['money'][i+n3-n2:n3-1+i].mean()
        money_MA20=stock_m['money'][i+n3-n1:n3-1+i].mean()
        if money_MA20<=money_MA60 and money_MA60<=money_MA200:
            count=count+1
        i=i+1
    return count

# 过滤停牌股票
# https://www.joinquant.com/algorithm/apishare/get?apiId=20
def filter_paused_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].paused]
    
# 过滤涨停股票
# https://www.joinquant.com/algorithm/apishare/get?apiId=24
def filter_limit_up_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not (current_data[stock].day_open>current_data[stock].high_limit*0.985)]
    
# 过滤ST股票
# https://www.joinquant.com/algorithm/apishare/get?apiId=22
def filter_st_stock(stock_list):
    current_data = get_current_data()
    return [stock for stock in stock_list if not current_data[stock].is_st]
    
# 过滤银行股
def filter_bank_stock(stock_list):
    bank_stocks = get_index_stocks('399951.XSHE')
    return [stock for stock in stock_list if not stock in bank_stocks]

# 过滤创业板 
def filter_300_stock(stock_list):
    return [stock for stock in stock_list if not stock.upper().startswith('300')]
    
    