该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/14603

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

def initialize(context):
    run_daily(period,time='every_bar')
    g.stocksnum=20
def period(context):
      scu=get_index_stocks('000001.XSHG')+get_index_stocks('399106.XSHE')
      q=query(valuation.code).filter(valuation.code.in_(scu)).order_by(valuation.market_cap.asc()).limit(g.stocksnum)
      df=get_fundamentals(q)
      stocklist=list(df['code'])
      m=get_current_data()
      buylist=stocklist
      for stock in context.portfolio.positions:
          if stock not in buylist: #如果stock不在buylist
              order_target(stock, 0)
      for stk in buylist:
          order_value(stk,50000)
      for stk in context.portfolio.positions:
          cost=context.portfolio.positions[stk].price
          close_data = attribute_history(stk,10, '1d', ['close'])
          close_data2 = attribute_history(stk,15, '1d', ['close'])
          close_data3 = attribute_history(stk,20, '1d', ['close'])
          MA10 = close_data['close'].mean()
          MA15 = close_data2['close'].mean()
          MA20 = close_data3['close'].mean()
          price = close_data['close'][-1]
          ret=price/cost-1
          cash=context.portfolio.cash/20
          if price<MA20:
              order_value(stk,cash*0.5)
          elif price<MA15:
              order_value(stk,cash*0.3)
          elif price<MA10:
              order_value(stk,cash*0.2)
          elif ret>0.05:
              order_value(stk,-cash*0.5)
          elif ret>0.1:
              order_value(stk,-cash*0.3)
          elif ret>0.15:
              order_value(stk,-cash*0.2)
              
          


          
          
              
          
     
              
    