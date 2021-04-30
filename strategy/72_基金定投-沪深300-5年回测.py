该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/11251

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

# 导入函数库
import jqdata
import numpy as np
import pandas as pd
import bisect
# 初始化函数，设定基准等等
def initialize(context):
    #基准指数
    g.benchmark_index = '000300.XSHG'
    # 要操作的股票：（g.为全局变量）
    g.buy_index = '160706.XSHE'
    set_benchmark(g.benchmark_index)
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    # 过滤掉order系列API产生的比error级别低的log
    log.set_level('order', 'error')
    set_commission(PerTrade(buy_cost=0.0015, sell_cost=0.005))

    # 按月运行
    run_monthly(fnud_main, 1, time='open')
    run_monthly(fnud_close, 1, time='after_close')
    run_daily(fund_sell, time='every_bar')
    g.Totalmonth = 0
    g.TotalCash = 0
    g.MaxCash = 0
    g.LastCash = 1000   #每月定投额度
    g.pe_now=0
    # 输出内容到日志 log.info()
    log.info("定投指数：%s，定投基金：%s,每月定投额度：%s" %(get_security_info(g.benchmark_index).display_name , get_security_info(g.buy_index).display_name,g.LastCash))
    log.info("------------------------------------------------------")
    send_message("定投指数：%s，定投基金：%s,每月定投额度：%s" %(get_security_info(g.benchmark_index).display_name , get_security_info(g.buy_index).display_name,g.LastCash))
    
def fnud_main(context):
    g.Totalmonth += 1
    df = get_index_pes(context)
    g.pe_now = float(df.ix[0,2]) / 100 #当前PE百分比 log.info(df)
    if g.pe_now <0.4:
        g.pe_ratio = 1.5;
    elif g.pe_now < 0.6:
        g.pe_ratio = 1.0;
    elif g.pe_now < 0.8:
        g.pe_ratio = 0.5;
    else:
        g.pe_ratio = -999;
    cash = g.pe_ratio * g.LastCash
    g.LastCash = g.LastCash * 1.01
    order_value(g.buy_index, cash)    #定投5000
    # 给微信发送消息（添加模拟交易，并绑定微信生效）
    send_message("Month %d ，沪深300当前PE百分比: %.2f ，(%s)买卖金额：%.2f" %(g.Totalmonth,g.pe_now,g.buy_index, cash))
    log.info("Month %d   当前PE百分比: %.2f  " %(g.Totalmonth,g.pe_now))
    
def fund_sell(context):
    if (g.pe_now > 0.75 ) & (context.portfolio.positions_value >0):
        df = get_index_pes(context)
        g.pe_now = float(df.ix[0,2]) / 100 #当前PE百分比 log.info(df)
        if g.pe_now >= 0.8:
            order_target_value(g.buy_index, 0)  #全部卖出
            log.info("全部清仓")
            send_message("全部清仓")
    
def fnud_close(context):
    #得到当天所有订单
    orders = get_orders()
    cash = 0.0
    for _order in orders.values():
        cash = float(_order.price) * float(_order.filled)
        if _order.is_buy == False:
            cash = cash * -1.0;
        g.TotalCash += cash
        if g.MaxCash < g.TotalCash:
            g.MaxCash = g.TotalCash
        if g.TotalCash <= 0:
            g.TotalCash = 0
    # 获取账户的持仓价值
    positions_value = context.portfolio.positions_value
    available_cash = context.portfolio.available_cash
    returns = context.portfolio.returns * 100
    log.info("总投入: %d，最大投入: %d，今日买卖: %s" %(g.TotalCash , g.MaxCash,cash))
    log.info("当前持仓: %.2f，账户余额：%.2f，总权益的累计收益率：%.2f" %(positions_value , available_cash , returns))
    log.info("------------------------------------------------------")

def on_strategy_end(context):
    log.info("回测结束：总投入: %d，最大投入: %d" %(g.TotalCash , g.MaxCash))
    # 获取账户的持仓价值
    positions_value = context.portfolio.positions_value
    available_cash = context.portfolio.available_cash
    returns = context.portfolio.returns * 100
    log.info("当前持仓: %.2f，账户余额：%.2f，总权益的累计收益率：%.2f" %(positions_value , available_cash , returns))

################################### 自定义函数 ###############################
#指定日期的指数PE（等权重）
def get_index_pe_date(index_code,date):
    stocks = get_index_stocks(index_code, date)
    q = query(valuation).filter(valuation.code.in_(stocks))
    df = get_fundamentals(q, date)
    if len(df)>0:
        pe = len(df)/sum([1/p if p>0 else 0 for p in df.pe_ratio])
        return pe
    else:
        return float('NaN')
    
#指数历史PE
def get_index_pe(index_code,today):
    start= get_security_info(index_code).start_date 
    #end = pd.datetime.today();
    end = today;
    dates=[]
    pes=[]
    for d in pd.date_range(start,end,freq='M'): #频率为月
    #for d in jqdata.get_trade_days(start_date=start, end_date=end): #频率为天，交易日
        dates.append(d)
        pes.append(get_index_pe_date(index_code,d))
    return pd.Series(pes, index=dates)
#获取指数PE
def get_index_pes(context):
    today = context.current_dt
    all_index = get_all_securities(['index'])
    index_choose =[g.benchmark_index]
    df_pe = pd.DataFrame()
    for code in index_choose:
        #print(u'正在处理: ',code) 
        df_pe[code]=get_index_pe(code,today)

    #today= pd.datetime.today()
    results=[]
    for code in index_choose:
        pe = get_index_pe_date(code,today)
        q_pes = [df_pe.quantile(i/10.0)[code]  for i in range(11)]
        idx = bisect.bisect(q_pes,pe)
        quantile = idx-(q_pes[idx]-pe)/(q_pes[idx]-q_pes[idx-1])
        index_name = all_index.ix[code].display_name
        results.append([index_name,'%.2f'% pe,'%.2f'% (quantile*10)]+['%.2f'%q  for q in q_pes]+[df_pe[code].count()])
    columns=[u'名称',u'当前PE',u'分位点%',u'最小PE']+['%d%%'% (i*10) for i in range(1,10)]+[u'最大PE' , u"数据个数"]
    return pd.DataFrame(data=results,index=index_choose,columns=columns)



