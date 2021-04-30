该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/15426

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

import pandas as pd
import numpy as np
import math
from sklearn.svm import SVR  
from sklearn.model_selection import GridSearchCV  
from sklearn.model_selection import learning_curve
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import jqdata

#初始化函数
def initialize(context):
    set_params()
    set_backtest()
    run_daily(trade, 'every_bar')

#设置参数函数，调仓    
def set_params():
    g.days = 0
    g.refresh_rate = 10
    g.stocknum = 10

#测试函数    
def set_backtest():
    set_benchmark('000001.XSHG')#基准指数
    set_option('use_real_price', True)
    log.set_level('order', 'error')

#设置交易函数    
def trade(context):
    if g.days % 10 == 0:    #若持有10天，进行调仓
        sample = get_index_stocks('000001.XSHG', date = None)  #获得股票池
        q = query(valuation.code, valuation.market_cap, balance.total_assets - balance.total_liability,
                  balance.total_assets / balance.total_liability, income.net_profit, income.net_profit + 1, 
                  indicator.inc_revenue_year_on_year, balance.development_expenditure).filter(valuation.code.in_(sample))
        df = get_fundamentals(q, date = None)
        df.columns = ['code', 'log_mcap', 'log_NC', 'LEV', 'NI_p', 'NI_n', 'g', 'log_RD'] #回归的各因子
        
        #对因子取log
        df['log_mcap'] = np.log(df['log_mcap'])
        df['log_NC'] = np.log(df['log_NC'])
        df['NI_p'] = np.log(np.abs(df['NI_p']))
        df['NI_n'] = np.log(np.abs(df['NI_n'][df['NI_n']<0]))
        df['log_RD'] = np.log(df['log_RD'])
        df.index = df.code.values
        del df['code']
        df = df.fillna(0)
        df[df>10000] = 10000
        df[df<-10000] = -10000
        industry_set = ['801010', '801020', '801030', '801040', '801050', '801080', '801110', '801120', '801130', 
                  '801140', '801150', '801160', '801170', '801180', '801200', '801210', '801230', '801710',
                  '801720', '801730', '801740', '801750', '801760', '801770', '801780', '801790', '801880','801890'] #申万一级指数
        
        for i in range(len(industry_set)):
            industry = get_industry_stocks(industry_set[i], date = None)
            s = pd.Series([0]*len(df), index=df.index)
            s[set(industry) & set(df.index)]=1
            df[industry_set[i]] = s
            
            #回归X,Y
        X = df[['log_NC', 'LEV', 'NI_p', 'NI_n', 'g', 'log_RD','801010', '801020', '801030', '801040', '801050', 
                '801080', '801110', '801120', '801130', '801140', '801150', '801160', '801170', '801180', '801200', 
                '801210', '801230', '801710', '801720', '801730', '801740', '801750', '801760', '801770', '801780', 
                '801790', '801880', '801890']]
        Y = df[['log_mcap']]
        X = X.fillna(0)
        Y = Y.fillna(0)
        
        #支持向量回归（Support Vector Regression)
        svr = SVR(kernel='rbf', gamma=0.1) 
        model = svr.fit(X, Y)  #将XY带入SVR
        factor = Y - pd.DataFrame(svr.predict(X), index = Y.index, columns = ['log_mcap']) #获取残差值
        factor = factor.sort_index(by = 'log_mcap')
        stockset = list(factor.index[:10])     #按残差大小分成10组
        sell_list = list(context.portfolio.positions.keys())
        for stock in sell_list:
            if stock not in stockset[:g.stocknum]:    #如果股票不在该档就卖出
                stock_sell = stock
                order_target_value(stock_sell, 0)
            
        if len(context.portfolio.positions) < g.stocknum:  #如果持仓天数小于10，持仓期平均cash剩余
            num = g.stocknum - len(context.portfolio.positions)
            cash = context.portfolio.cash/num
        else:
            cash = 0
            num = 0
        for stock in stockset[:g.stocknum]:   #如果持仓股票仍在该档，则不卖出
            if stock in sell_list:
                pass
            else:
                stock_buy = stock
                order_target_value(stock_buy, cash)
                num = num - 1
                if num == 0:
                    break
        g.days += 1                            #按天进行
    else:
        g.days = g.days + 1    
            