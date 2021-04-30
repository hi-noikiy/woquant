该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/14986

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

# 导入函数库
from jqdata import *
from datetime import datetime, timedelta
# 初始化函数，设定基准等等
def initialize(context):
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 输出内容到日志 log.info()
    log.info('初始函数开始运行且全局只运行一次')
    # 过滤掉order系列API产生的比error级别低的log
    # log.set_level('order', 'error')
    
    ### 股票相关设定 ###
    # 股票类每笔交易时的手续费是：买入时佣金万分之三，卖出时佣金万分之三加千分之一印花税, 每笔交易佣金最低扣5块钱
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    g.security = []
    g.counter_open = 0
    run_monthly(market_open, 8, time='open', reference_security='000300.XSHG')


# # 每半年开盘去选择这些股票
def market_open(context):
    g.counter_open += 1
    if g.counter_open == 1:  
        log.info("又是半年，该做事了。counter: " + str(g.counter_open))
        sell_all()
        date = str(context.current_dt.date())
        yesterday = (datetime.strptime(date, "%Y-%m-%d").date() - timedelta(1)).strftime("%Y-%m-%d")
        # 获取当天的 PE, PB 符合要求的股票
        stock_list = get_stock_list(yesterday)
        # 按照股票代码排序股票表格
        stock_list = stock_list.sort(["code"], ascending=[True])
        # 获取对应的股息率
        # log.info("股票名单：\n" + str(stock_list))
        if stock_list.shape[0] > 0:
            stock_list["dividend_ratio"] = stock_list.apply(lambda x: DividendRatio([x[0]], yesterday), axis=1)
            stock_list = stock_list.dropna()
            stock_list = stock_list[stock_list["dividend_ratio"] > 0.03]
            # 获取 stock_list 中股票的行业代码并且合并
            industry_df = finance.run_query(
                    query(
                        finance.STK_COMPANY_INFO.code,
                        finance.STK_COMPANY_INFO.industry_id
                    ).filter(
                        finance.STK_COMPANY_INFO.code.in_(stock_list["code"].tolist())
                    )
                )
            stock_list["industry_id"] = industry_df["industry_id"].tolist()
            # PE 为重
            stock_list = stock_list.sort(["pe_ratio", "pb_ratio", "dividend_ratio"], ascending=[True, True, False])
            # 股息率为重
            # stock_list = stock_list.sort(["dividend_ratio", "pe_ratio", "pb_ratio"], ascending=[False, True, True])
            # 获取股票和对应信息
            stock_list_info, stock_list = get_stocks(stock_list, 10)
            for stock in stock_list:
                log.info('函数运行时间(before_market_open)：' + str(context.current_dt.time()) + '选择股票：' + stock)
            if len(stock_list) > 6:
                g.security = stock_list
            else:
                g.security = []
            cash = context.portfolio.available_cash
            log.info("时间：" + str(context.current_dt.date()) + " 买买买！" + "cash: " + str(cash))
            buy_stock(g.security, cash)
        else:
            log.info("未找到 PE, PB 符合要求的股票，直接返回")
            return
    else:
        log.info("非半年周期，counter: " + str(g.counter_open))
        if g.counter_open == 6:
            g.counter_open = 0
 


# 获取 0 < PE < 10, 0 < PB < 1.5 的股票
def get_stock_list(date):
    log.info('当前日期：' + date + '，获取 PE，PB 符合要求的股票')
    q = query(
        valuation.code,
        valuation.pe_ratio,
        valuation.pb_ratio
    )
    stock_list = get_fundamentals(q, date)
    # 过滤掉不符合要求的股票
    stock_list = stock_list[stock_list["pe_ratio"] > 0]
    stock_list = stock_list[stock_list["pe_ratio"] < 10]
    stock_list = stock_list[stock_list["pb_ratio"] > 0]
    stock_list = stock_list[stock_list["pb_ratio"] < 1.5]
    
    return stock_list
    
# 获取对应股票代码 list 下的股息率
def DividendRatio(security_list,end_date,count=1):
    '''查询股息率(日更新)
    输入:股票池,截止日期,获取数量
    输出:panel结构,单位:1'''
    trade_days = get_trade_days(end_date=end_date,count = count)
    security_list.sort()
    secu_list = [x[:6] for x in security_list]
    code_df = jy.run_query(query(
         jy.SecuMain.InnerCode,jy.SecuMain.SecuCode,
    #     jy.SecuMain.ChiName,jy.SecuMain.CompanyCode
        ).filter(
        jy.SecuMain.SecuCode.in_(secu_list),jy.SecuMain.SecuCategory==1).order_by(jy.SecuMain.SecuCode))
    code_df['code'] = security_list
    df = jy.run_query(query(
#         jy.LC_DIndicesForValuation    #得到整表
        jy.LC_DIndicesForValuation.InnerCode,
                jy.LC_DIndicesForValuation.TradingDay,
                 jy.LC_DIndicesForValuation.DividendRatio,
                ).filter(jy.LC_DIndicesForValuation.InnerCode.in_(code_df.InnerCode),
                        jy.LC_DIndicesForValuation.TradingDay.in_(trade_days)
                        ))
    f_df = df.merge(code_df,on='InnerCode').set_index(['TradingDay','code']).drop(['InnerCode','SecuCode'],axis=1)
    panel = f_df.to_panel()
    return panel.major_xs(panel.major_axis[0])["DividendRatio"].tolist()[0] if len(panel.major_axis) > 0 else None

# 获取股票的行业代码
def get_industry_id(code):
    df = finance.run_query(
        query(
            finance.STK_COMPANY_INFO.industry_id
        ).filter(
            finance.STK_COMPANY_INFO.code == code
        )
    )
    
    return df["industry_id"][0]

# 在备选股票中选出 10 只股票，注意同行业的占比不能超过 10%
def get_stocks(sorted_stock_list, max_stock):
    stock_list_info = []
    stock_list = []
    occur_dict = {}
    for loc in range(sorted_stock_list.shape[0]):
        field = get_industry_id(sorted_stock_list.iloc[loc]["code"])
        if field in occur_dict:
            if occur_dict[field] >= max_stock * 0.3:
                continue
            else:
                occur_dict[field] += 1
                stock_list_info.append(sorted_stock_list.iloc[loc])
                stock_list.append(sorted_stock_list.iloc[loc]["code"])
        else:
            stock_list_info.append(sorted_stock_list.iloc[loc])
            stock_list.append(sorted_stock_list.iloc[loc]["code"])
            occur_dict[field] = 1
        if len(stock_list) >= max_stock:
            break
    return stock_list_info, stock_list

def sell_all():
    log.info("股票数量：" + str(len(g.security)))
    for stock in g.security:
        # 卖出这些股票
        log.info("卖出：" + stock)

        order_target(stock, 0)

def buy_stock(stock_list, sum_price):
    if stock_list is None or len(stock_list) == 0:
        log.info("未选到合适股票，本期空仓")
        return 
    # 获取 stock_list 中股票的当日价格
    price_dict = history(1, unit='1d', field='avg', security_list=stock_list, df=False, skip_paused=False, fq='pre')
    for stock in price_dict.keys():
        price_dict[stock] = price_dict[stock][0]
    # 将 sum_price 平均分配到这些股票上
    sum_price_dict = {}
    per_price = sum_price / len(price_dict)
    for stock in price_dict.keys():
        num = math.floor(per_price / price_dict[stock] / 100)
        log.info("买入：" + stock + ", 数量：" + str(num * 100) + "股")
        order(stock, num * 100)
    #     sum_price_dict[stock] = math.floor(per_price / price_dict[stock] / 100)
    # sum_value = 0
    # for stock in sum_price_dict.keys():
    #     sum_value += sum_price_dict[stock] * price_dict[stock]*100
    # res_value = sum_price - sum_value
    # return price_dict, sum_price_dict, res_value
    

