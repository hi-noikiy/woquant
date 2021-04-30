该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/10730

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

import pandas as pd
from jqdata import gta

def initialize(context):
    set_params(context) 
    set_variables()  
    set_backtest() 

def set_params(context):
    g.tc = 3 
    g.buy = 5
    g.hold = 10 
    # 因子等权重里1表示因子值越小越好，-1表示因子值越大越好
    g.factors_weights = [-1]
    g.factors_rank = ['dividend_rate']
    g.industries = ['801010','801020','801030','801040','801050','801080',
                    '801110','801120','801130','801140','801150','801160',
                    '801170','801180','801200','801210','801230','801710',
                    '801720','801730','801740','801750','801760','801770',
                    '801780','801790','801880','801890']
    # g.industries = ['A01','A02','A03','A04','A05','B06','B07','B08','B09','B11','C13','C14','C15','C17','C18',\
                    #  'C19','C20','C21','C22','C23','C24','C25','C26','C27','C28','C29','C30','C31','C32','C33','C34','C35',\
                    #  'C36','C37','C38','C39','C40','C41','C42','D44','D45','D46','E47','E48','E50','F51','F52','G53','G54','G55',\
                    # 'G56','G58','G59','H61','H62','I63','I64','I65','J66','J67','J68','J69','K70','L71','L72','M73','M74','N77',\
                    # 'N78','P82','Q83','R85','R86','R87','S90']
    g.factors_PTC = [[valuation.market_cap, 'market_cap', 0.8, False]]
    g.factors_industries_PTC = [[cash_flow.cash_equivalent_increase/valuation.market_cap, 'NCFP', 0.4, False], [valuation.pe_ratio, 'pe', 0.10, True]]
    g.args_div = [context.current_dt.date()-datetime.timedelta(1), context.current_dt.year-1]
    

def set_variables():
    g.t = 0  
    g.if_trade = False  
    g.buy_count = 0

def set_backtest():
    set_option('use_real_price', True) 
    log.set_level('order', 'error')

def before_trading_start(context):
    if g.t % g.tc == 0:
        g.if_trade = True
        set_slip_fee(context)
        g.all_stocks = feasible_stocks(context, list(get_all_securities().index))
    g.t += 1

# 过滤涨跌停板、停牌、次新股、ＳＴ等情况
def feasible_stocks(context, stock_list):
    current_data = get_current_data()
    stock_list = [stock for stock in stock_list if
                    stock in context.portfolio.positions.keys()
                    or (not current_data[stock].paused
                    and sum(attribute_history('000300.XSHG', 14, unit='1d',
                    fields=('paused'),skip_paused=False))[0]==0)]
                    
    stock_list = [stock for stock in stock_list
                  if not current_data[stock].is_st
                  and 'ST' not in current_data[stock].name
                  and '*' not in current_data[stock].name
                  and '退' not in current_data[stock].name]
   
    stock_list = [stock for stock in stock_list if
                  stock in context.portfolio.positions.keys()
                  or current_data[stock].low_limit<current_data[stock].day_open 
                     < current_data[stock].high_limit]
                     
    stock_list = [stock for stock in stock_list if 
                  (context.current_dt.date() - get_security_info(stock).start_date) 
                  >= datetime.timedelta(360)]
                  
    # stock_list = [stock for stock in stock_list if stock[0:3] != '300']

    return stock_list

def set_slip_fee(context):
    set_slippage(FixedSlippage(0))
    set_order_cost(OrderCost(open_tax=0, close_tax=0.001, 
                    open_commission=0.001, close_commission=0.002, 
                    close_today_commission=0, min_commission=5), type='stock')

def handle_data(context, data):
    if g.if_trade == True :
        log.info('交易前时间：',context.current_dt)
        buylist, holdlist = multifactor_stocks_select(context)
        stock_sell_and_buy(context, buylist, holdlist)
        trade_summery(context)
    g.if_trade = False

# 买入和卖出
def stock_sell_and_buy(context, buylist, holdlist):
    for stock in context.portfolio.positions:
        if stock not in holdlist:
            order_target_value(stock, 0)

    stocks_num = len(buylist) - len(context.portfolio.positions)

    if stocks_num <= 0:
        return
    else:
        position_per_stk = context.portfolio.cash / stocks_num
        for stock in buylist:
            if stock not in context.portfolio.positions:
                order_target_value(stock, position_per_stk)
                g.buy_count += 1

# 多因子选股的流程，最后输出可买入的股票池和可继续持仓的股票池
def multifactor_stocks_select(context):
    df = factors_selected(context)
    df = factors_percent(g.factors_PTC, df)
    df = factors_industries_percent(g.factors_industries_PTC, df)
    df = concat_data(context, df, dividend_rate, g.args_div)
    factors_rank, stocks_code = factors_ranked(df, g.factors_rank)
    points = np.dot(factors_rank, g.factors_weights)
    stocks_sort = points_sorted(points, stocks_code)
    buylist = stocks_sort[0:g.buy]
    holdlist = stocks_sort[0:g.hold]
    return buylist, holdlist

# 因子选择、阀值过滤
def factors_selected(context):
    factors = query(valuation.code, valuation.pe_ratio)
    factors = factors.filter(valuation.code.in_(g.all_stocks),  
            indicator.inc_net_profit_annual>0, 
            indicator.inc_net_profit_year_on_year>5, cash_flow.cash_equivalent_increase>0)
    df = get_fundamentals(factors, context.current_dt.date())
    df.index = df.code.values
    del df['code']
    df = df.dropna(axis=0)
    return df

# 因子按全市场的百分比过滤
def factors_percent(factors, df=None):
    def s_percent(factor, factor_name, percentage, ascending):
        q = query(valuation.code, factor).order_by(factor.asc() if ascending==True else factor.desc())
        df_s = get_fundamentals(q)
        df_s = df_s[0:int(len(df_s)*percentage)]
        df_s.index = df_s.code.values
        del df_s['code']
        df_s.columns = [factor_name]
        return df_s
    
    df_m = None
    for i in factors:
        df_s = s_percent(i[0], i[1], i[2], i[3])
        df_m = pd.concat([df_m, df_s], axis=1)
    df_m = df_m.dropna(axis=0)
    if df is not None:
        index_intersect = set(df.index.values)&set(df_m.index.values)
        df_m = df.loc[index_intersect,:]
    df_m = df_m.dropna(axis=0)
    return df_m

# 因子按行业的百分比过滤
def factors_industries_percent(factors, df=None):
    def s_neutral(factor, factor_name, percentage, ascending):
        df_all = None
        for aa in g.industries:
            industries_stock_list = list(get_industry_stocks(aa))
            q = query(valuation.code, factor).filter(valuation.code.in_(industries_stock_list),factor>0).order_by(factor.asc() if ascending==True else factor.desc())
            df = get_fundamentals(q)
            df = df[0:int(len(df)*percentage)]
            df.index = df.code.values
            del df['code']
            df.columns = [factor_name]
            df_all = pd.concat([df_all, df])
        return df_all
    
    df_m = None
    for i in factors:
        df_s = s_neutral(i[0], i[1], i[2], i[3])
        df_m = pd.concat([df_m, df_s], axis=1)
    df_m = df_m.dropna(axis=0)
    if df is not None:
        index_intersect = set(df.index.values)&set(df_m.index.values)
        df_m = df.loc[index_intersect,:]
    df_m = df_m.dropna(axis=0)
    return df_m

# 不同表的数据整合到一个DataFrame里，func是从另外一张表获取数据的函数，args是func需要的参数，考虑参数的多变性，设置了几种情况
def concat_data(context, df, func, args):
    stock_codes = df.index
    df_div_all = None
    for code in stock_codes:
        if len(args) == 0:
            df_div = func(code)
        elif len(args) == 1:
            df_div = func(code, args[0])
        elif len(args) == 2:
            df_div = func(code, args[0], args[1])
        elif len(args) == 3:
            df_div = func(code, args[0], args[1], args[2])    
        elif len(args) == 4:
            df_div = func(code, args[0], args[1], args[2], args[3])     
        df_div_all = pd.concat([df_div_all, df_div], axis=0)
    df_new = pd.concat([df_div_all, df], axis=1)
    df_new = df_new.dropna(axis=0)
    return df_new

# 获取股息率的函数     
def dividend_rate(stock, end_date=None, paymentdate=2015, start_date=None, count=1, date=None,  no_data_return=NaN, skip_paused=False):
    def get_div(df, paymentdate):
        df.PAYMENTDATE = pd.to_datetime(df.PAYMENTDATE)
        try:
            if len(df)>0:
                div = df[[x.year == (int(paymentdate)+1) for x in df.PAYMENTDATE]]['DIVIDENTBT'].iloc[-1]
                return float(div)
            else:
                return no_data_return
        except:
            return no_data_return
    
    symbol = stock[:6]
    df = gta.run_query(query(
            gta.STK_MKT_DIVIDENT.SYMBOL,

            gta.STK_MKT_DIVIDENT.PAYMENTDATE,
            gta.STK_MKT_DIVIDENT.DIVIDENTBT,
            ).filter(gta.STK_MKT_DIVIDENT.SYMBOL.in_([symbol])
            ).order_by(gta.STK_MKT_DIVIDENT.PAYMENTDATE))
    div = get_div(df, paymentdate)
    from math import isnan
    if isnan(div) == True:
        div = get_div(df, paymentdate-1)
    df = get_price(stock, start_date=start_date, count=count, end_date=end_date, fields=['close'], frequency='daily', fq=None)
    df['dividend_rate'] = float(div)/df['close']*100
    df['dividend_rate'] = df['dividend_rate'].round(4)
    del df['close']
    df.index = [stock]
    return df

# 多因子数据过滤好后，按指定的因子进行排序
def factors_ranked(df, factors_rank):
    df_factors = df.loc[:,factors_rank]
    df_rank = df_factors.rank(ascending=False)
    return df_rank, df.index

# 按因子总得分进行排序
def points_sorted(points, stocks):
    pd_points = pd.DataFrame(points, index=stocks, columns=['points'])
    stocks = list(pd_points.sort(columns='points', ascending=False).index)
    return stocks  
    
# 按个人偏好设置一些交易统计 
def trade_summery(context):
    log.info('买入次数=',g.buy_count)
    date = (context.previous_date-context.run_params.start_date).days
    buy_count_peryear = g.buy_count/(float(date)/365) if (float(date)/365) >0 else 0
    log.info('一年平均买入次数=',buy_count_peryear/g.buy)
