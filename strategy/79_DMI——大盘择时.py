该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/11101

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

import talib
import math
import numpy as np
import pandas as pd

# 初始化函数，设定要操作的股票、基准等等
def initialize(context):
    g.security = '399300.XSHE'
    set_benchmark('399300.XSHE')
    
    #设置参数
    context.OBSERVATION = 100  
    context.ADXPERIOD = 18
    

# 每个单位时间(如果按天回测,则每天调用一次,如果按分钟,则每分钟调用一次)调用一次
def handle_data(context, data):
    security = g.security  
    # 获取股票的价格信息
    price = attribute_history(security, context.OBSERVATION, '1d', ('high','low','close'))

    ADX = talib.ADX(price['high'].values,price['low'].values,price['close'].values, context.ADXPERIOD)
    PDI = talib.PLUS_DI(price['high'].values,price['low'].values,price['close'].values, context.ADXPERIOD)
    NDI = talib.MINUS_DI(price['high'].values,price['low'].values,price['close'].values, context.ADXPERIOD)
    
    current_price = data[security].close
    current_position = context.portfolio.positions[security].closeable_amount
    cash = context.portfolio.cash
    
    print(security) 
    if current_price !=0:
        shares = cash/current_price
    
    record(ADX=ADX[-1])
    record(Plus_DI=PDI[-1])
    record(Minus_DI=NDI[-1])
    
    #ADX上行，+DI>-DI，当前空仓，则全仓买入标的
    if ADX[-1]>ADX[-2] and PDI[-1]>NDI[-1] and current_position <= 0:
        order_value(security,cash)
        log.info("Buying %s" % (security))#记录交易信息
    #ADX下行，+DI<-DI，则进行清仓
    if ADX[-1]<ADX[-2] and PDI[-1]<NDI[-1] and current_position > 0:
        order_target(security, 0)
        log.info("Selling %s" % (security))
    #百度上解释说ADX大于50会发生反转，但实际效果不佳。
    # if ADX[-1]>50:
    #     order_target(security, 0)
    #     log.info("Selling %s" % (security))
    

