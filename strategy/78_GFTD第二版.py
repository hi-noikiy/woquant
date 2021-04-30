该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/11188

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

import jqdata

def initialize(context):
    g.t=0
    g.buy_init = 0      #买入启动阶段计数，直到满足g.n2为止
    g.sell_init = 0     #卖出启动阶段计数，直到满足g.n2为止
    g.buy_count = 0     #买入计数2，直到达到g.n3为止
    g.sell_count = 0    #卖出计数2，直到达到g.n3为止
    g.state = 'empty'   #仓位状态，是满仓还是空仓
    g.save_price = 0    #记录上次保存的价格状态
    g.n1 = 4            #启动阶段和此前第四天的价格进行比较
    g.n2 = 4            #启动阶段为4
    g.count_lag = 2     #计数阶段和此前第二天的价格进行比较
    g.n3 = 4            #计数阶段临界值为4
    g.line=0.0          
    g.ud = -1
    set_commission(PerTrade(buy_cost=0.002, sell_cost=0.002, min_cost=5))
    set_option('use_real_price', True)
    g.stock = '000300.XSHG' #沪深300指数作为交易对象
    set_benchmark('000300.XSHG')
    
def handle_data(context, data):
    g.t+=1
    #获取交易信号
    signal = get_signal(context)
    #根据交易信号买入卖出
    rebalance(signal, context)
    record(line=g.line)
    record(price=attribute_history(g.stock, 1, '1d', ['close']).iloc[0,0])

#获取交易信号，并判断是买入还是卖出
def get_signal(context):
    
    #如果当前仓位为空，则寻找买入启动，找到后进行买入计数
    if g.state == 'empty' or g.state == 'buy_count':
        #收盘价
        prices = list(attribute_history(g.stock, g.n1+g.n2, '1d', 'close').close)
        #最低价
        prices_low=list(attribute_history(g.stock, g.n1+g.n2, '1d', 'low').low)
        #如果收盘价继续比4天前低，则买入启动的计数增加，否则计数清零
        g.buy_init=0
        for i in range(g.n2):
            if prices[i+g.n1]<=prices[i]:
                g.buy_init = g.buy_init+1
        print ('g.buy_init',g.buy_init)
        #买入启动的计数达到n2后，进入买入计数，买入启动的计数归零
        #保存最后的收盘价作为买入计数第一个计数的价格。
        #保存最后一个最低价，作为止损下限
        #买入计数清零
        if g.buy_init == g.n2:
            g.state = 'buy_count'
            g.buy_init = 0
            g.save_price = prices[-1]
            g.low=prices_low[-1]
            g.buy_count = 0
            
    #买入计数
    if g.state == 'buy_count':
        prices = attribute_history(g.stock, g.count_lag+1, '1d', ['close','high','low'])
        closes = list(prices.close)
        highs = list(prices.high)
        lows = list(prices.low)
        #三个条件都是小于之前的值
        if closes[-1]>=highs[0] and highs[-1]>highs[-2] and closes[-1]>g.save_price:
            g.save_price = closes[-1]
            g.buy_count += 1
            
            #更新止损线
            if(g.line>lows[-1]):
                g.line=lows[-1]
           
        print ('buy counting',g.buy_count)
        #计数达到n3 就发卖出信号
        if g.buy_count == g.n3:
            g.state = 'full'
            g.buy_count = 0
            return 'buy'
    
    #如果当前仓位已满，则寻找卖出启动，找到后进行卖出计数
    if g.state == 'full' or g.state == 'sell_count':
        prices = list(attribute_history(g.stock, g.n1+g.n2, '1d', 'close').close)
        prices_low=list(attribute_history(g.stock, g.n1+g.n2, '1d', 'low').low)
        #有连续大于4天之前收盘价，卖出启动的计数加1，断掉就归零
        g.sell_init=0
        for i in range(g.n2):
            if prices[i+g.n1]>=prices[i]:
                g.sell_init = g.sell_init+1
        print ('g.sell_init',g.sell_init)
        #卖出启动的计数到n2，就卖出
        if g.sell_init == g.n2:
            g.state = 'sell_count'
            g.sell_init = 0
            g.save_price = prices[-1]
            g.sell_count = 0

    if g.state == 'sell_count':
        prices = attribute_history(g.stock, g.count_lag+1, '1d', ['close','high','low'])
        closes = list(prices.close)
        highs = list(prices.high)
        lows = list(prices.low)
        if closes[-1]<=lows[0] and lows[-1]<lows[-2] and closes[-1]<g.save_price:
            g.save_price = closes[-1]
            g.sell_count += 1
            if g.line<highs[-1]:
                g.line=highs[-1]
        print ('sell counting',g.sell_count)
        if g.sell_count == g.n3:
            g.state = 'empty'
            g.sell_count = 0
            return 'sell'
        
#根据获得的信号进行买入卖出操作，并将最低点计数归为0
def rebalance(signal, context):
    if signal=='buy':
        print 'buy'
        order_target_value(g.stock, context.portfolio.total_value)
    if signal=='sell':
        print 'sell'
        order_target(g.stock, 0)
    '''
    price = attribute_history(g.stock, 1, '1d', ['close']).iloc[0,0]
    if g.state == 'empty' and price>g.line:
        print 'buy'
        order_target_value(g.stock, context.portfolio.total_value)
        if g.state != 'sell_count':
            g.state = 'full'
        g.line=0
    if g.state == 'full' and price<g.line:
        print 'sell'
        order_target(g.stock, 0)
        if g.state != 'buy_count':
            g.state = 'empty'
        g.line=0
    '''