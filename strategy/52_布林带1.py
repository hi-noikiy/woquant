该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/13162

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

# 导入函数库
import jqdata
import numpy as np

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
    set_slippage(FixedSlippage(0.02))
    
    ### 股票相关设定 ###
    # 股票类每笔交易时的手续费是：买入时佣金万分之三，卖出时佣金万分之三加千分之一印花税, 每笔交易佣金最低扣5块钱
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5), type='stock')
    
    ## 运行函数（reference_security为运行时间的参考标的；传入的标的只做种类区分，因此传入'000300.XSHG'或'510300.XSHG'是一样的）
      # 开盘前运行
   
      # 开盘时运行
    run_daily(market_open, time='open', reference_security='000300.XSHG')
      # 收盘后运行
    run_daily(after_market_close, time='after_close', reference_security='000300.XSHG')
    

    
## 开盘时运行函数
def market_open(context):
    log.info('函数运行时间(market_open):'+str(context.current_dt.time()))
    security ='600519.XSHG'
    # 获取股票的收盘价
    price= attribute_history(security, 20, '1d', ['close'],skip_paused=True)
    
    #获取可以现金
    
    cash=context.portfolio.available_cash
    
    #获取当前仓位信息   
    current_position=context.portfolio.positions[security].closeable_amount
    
    # 可以运用numpy自带的函数计算过去20日的移动平均线作为中轨
    mid=np.mean(price)
    
    #可以运用numpy自带函数计算昨日20日的标准差
    std=np.std(price)
    
    #用upper保存昨日上轨线
    upper=mid+2*std
    
    #用lower保存昨日下轨线
    lower=mid-2*std
    
    #获取当前收盘价
    p=price['close'][-1]
    
    if p>upper[-1] and current_position<=0:
        order_value(security, cash)
    elif p<lower[-1] and current_position>=0:
        order_target_value(security,0)
   
 
## 收盘后运行函数  
def after_market_close(context):
    log.info(str('函数运行时间(after_market_close):'+str(context.current_dt.time())))
    #得到当天所有成交记录
    trades = get_trades()
    for _trade in trades.values():
        log.info('成交记录：'+str(_trade))
    log.info('一天结束')
    log.info('##############################################################')
