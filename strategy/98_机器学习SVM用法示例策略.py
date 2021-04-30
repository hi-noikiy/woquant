该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/13324

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

'''
策略思路：
选择标的为同仁堂600085
选取标的的7个特征变量一年的数据作为训练集，训练支持向量机模型
训练样本的标签是后5个交易日的涨跌情况，涨了就是1，跌了就是0，
每周三进行调仓,将拟合模型进行未来5天涨跌幅预测，为1时买入，否则空仓
选取的特征值为：
收盘价/区间均收盘价均值
现量/区间均量
最高价/区间最高价均值
最低价/区间最低价均值
成交量比值（相对前一日）
区间收益率
区间标准差
注意：
示例策略只为说明思路和用法，存在特征值量纲不统一、标的单一等问题，策略开发需要再次基础上更为精细化处理。
'''
from sklearn import svm
import numpy as np

#初始化
def initialize(context):
    #设置标的
    g.stock = '600085.XSHG'
    #设置基准
    set_benchmark(g.stock)
    #过滤掉order系列API产生的比error级别低的log
    log.set_level('order', 'error')
    #设置数据长度
    g.days = 22
    #设置定时任务
    run_weekly(trade_func,3, time='open')
#定时任务函数
def trade_func(context):
    prediction = svm_prediction(context)
    if prediction == 1:
        cash  = context.portfolio.total_value
        order_target_value(g.stock,cash)
    else:
        order_target_value(g.stock,0)
        
#结果预测
def svm_prediction(context):
    #获取标的的历史数据
    stock_data = get_price(g.stock, frequency='1d',end_date=context.previous_date,count=252)
    date_value = stock_data.index
    close = stock_data['close'].values
    #用于记录日期的列表
    date_list = []
    # 获取行情日期列表
    #转换日期格式
    for i in range(len(date_value)):
        date_list.append(str(date_value[i])[0:10])
    
    x_all = []
    y_all = []
    #获取特征变量x
    for i in date_list[g.days:-5]:
        features_temp = get_features(context,date=i,count=g.days)
        x_all.append(features_temp)
    #获取特征变量y  
    for i in range(g.days,len(date_list)-5):    
        if close[i+5]>close[i]:
            label = 1
        else:
            label = 0    
        y_all.append(label)
    x_train = x_all[: -1]
    y_train = y_all[:-1]
    clf = svm.SVC()
    clf.fit(x_train, y_train)
    print('训练完成!')
    #进行预测
    prediction = clf.predict(x_all[-1])[0]
    return prediction
    
#获取特征值
def get_features(context,date,count=252):
    #获取数据
    df_price = get_price(g.stock,end_date=date,count=count,fields=['open','close','low','high','volume','money','avg','pre_close'])  
    close = df_price['close'].values
    low = df_price['low'].values
    high = df_price['high'].values
    volume = df_price['volume'].values
    #特征变量设置
    #收盘价/均值
    close_mean = close[-1]/np.mean(close)
    #现量/均量
    volume_mean = volume[-1]/np.mean(volume)
    #最高价/均价
    high_mean = high[-1]/np.mean(high)
    #最低价/均价
    low_mean = low[-1]/np.mean(low)
    #成交量比值（相对前一日）
    volume_current = volume[-1]/volume[0]
    #区间收益率
    returns = close[-1]/close[0]
    #区间标准差
    std = np.std(np.array(close),axis=0)   
    features = [close_mean,volume_mean,high_mean,low_mean,volume_current,returns,std]
    
    return features
    