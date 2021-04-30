该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/14750

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

# 导入函数库
from jqdata import *
import pandas as pd
import numpy as np
from sklearn import linear_model
from numpy import mean, std

# 初始化函数，设定要操作的股票、基准等等
def initialize(context):
    # 定义一个全局变量, 保存要操作的股票
    context.stock_id='510300.XSHG'
    context.beat_list=[]
    context.count=0
    context.z_beta_r2_list=[]
    context.n_value=18
    context.m_value=400
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)

def before_trading_start(context):
    advance_high_array=attribute_history(context.stock_id,400,'60m','high')
    advance_low_array=attribute_history(context.stock_id,400,'60m','low')
    
    for i in range(context.n_value,context.m_value):
        
        sliding_windows_high_array=advance_high_array[i-18:i]
        sliding_windows_low_array=advance_low_array[i-18:i]

        reg = linear_model.LinearRegression()
        reg.fit (sliding_windows_low_array,sliding_windows_high_array)
        beat=reg.coef_
        context.beat_list.append(beat)
        
# 每个单位时间(如果按天回测,则每天调用一次,如果按分钟,则每分钟调用一次)调用一次
def handle_data(context,data):

    context.count=context.count+1
    if context.count % 60==0:
        high_array=attribute_history(context.stock_id,18,'60m','high')
        low_array=attribute_history(context.stock_id,18,'60m','low')
        reg = linear_model.LinearRegression()
        reg.fit(low_array,high_array)
        beat=reg.coef_
        R_sq=reg.score(low_array,high_array)
    
        beat_z=R_sq*(beat-mean(context.beat_list))/std(context.beat_list)
    
        context.z_beta_r2_list.append(beat_z)
        log.info("context.z_beta_r2_list",context.z_beta_r2_list)
        cash = context.portfolio.available_cash
        print(cash)
        print("beat",beat)
        print("R_sq",R_sq)
        print("beat_z",beat_z)
        record(name=beat_z)
        if len(context.z_beta_r2_list)>2:
            if context.z_beta_r2_list[-2]<0.7 and context.z_beta_r2_list[-1]>0.7:
                log.info(" 买入 %s" % (context.stock_id))
                order_value(context.stock_id,cash)
            if context.z_beta_r2_list[-2]>-0.7 and context.z_beta_r2_list[-1]<-0.7:
                log.info(" 卖出 %s" % (context.stock_id))
                order_target_value(context.stock_id, 0)
    # record(context.z_beta_r2_list)
