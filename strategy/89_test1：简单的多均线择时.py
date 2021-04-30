该策略由聚宽用户分享，仅供学习交流使用。
原文网址：https://www.joinquant.com/post/12143

原文一般包含策略说明，如有疑问建议到原文和作者交流讨论。


原文策略源码如下：

# 克隆自聚宽文章：https://www.joinquant.com/post/570
# 标题：【简单的多均线择时策略】那个天台排队的孩子，我给你讲个故事
# 作者：陈小米。

def initialize(context):
    g.stock = ['600196.XSHG']
    set_benchmark('600196.XSHG')
    g.month = context.current_dt.month
    g.stock_grade = [0]
    g.mavg5 = [0]
    g.mavg10 = [0]
    g.mavg20 = [0]
    g.mavg30 = [0]
    g.mavg60 = [0]
    g.mavg180 = [0]
    g.cash = 20000

# 计算股票过去n个单位时间（一天）均值
def caculate_mavg(stock,n):
    return history(n, '1d', 'close', [stock],df = False)[stock].mean()

# 得到需要的多条均线
def evaluate_by_mavg(stock):
   mavg5 = caculate_mavg(stock,5)
   g.mavg5.append(mavg5)
   mavg10 = caculate_mavg(stock,10)
   g.mavg10.append(mavg10)
   mavg20 = caculate_mavg(stock,20)
   g.mavg20.append(mavg20)
   mavg30 = caculate_mavg(stock,30)
   g.mavg30.append(mavg30)
   return None

# 判断多头排列
def is_highest_point(data,stock,n):
    if len(g.mavg10)>2:
        price = data[stock].price
        if g.mavg5[n] > g.mavg10[n]\
        and g.mavg10[n] > g.mavg20[n]\
        and g.mavg20[n] > g.mavg30[n]:
            return True
    return False

# 判断空头排列——空仓
def is_lowest_point(data,stock,n):
    if len(g.mavg10)>2:
        price = data[stock].price
        if g.mavg5[n] < g.mavg10[n]\
        and g.mavg10[n] < g.mavg20[n]:
            return True
    return False
    
# 判断多头排列后的死叉——卖出
def is_crossDOWN(data,stock,mavg1,mavg2):
    if len(mavg2)>2 and is_highest_point(data,stock,-2)\
    and is_highest_point(data,stock,-3):
        if mavg1[-2] > mavg2[-2]\
        and mavg1[-1] < mavg2[-1]:
            return True
    return False

# 判断空头排列后的金叉——买入
def is_crossUP(data,stock,mavg1,mavg2):
    if len(mavg2)>2 and is_lowest_point(data,stock,-2)\
    and is_lowest_point(data,stock,-3):
        if mavg1[-2] < mavg2[-2]\
        and mavg1[-1] > mavg2[-1]:
            return True
    return False

# 判断均线纠缠
def is_struggle(mavg1,mavg2,mavg3):
    if abs((mavg1[-1]-mavg2[-1])/mavg2[-1])< 0.003\
    or abs((mavg2[-1]-mavg3[-1])/mavg3[-1])< 0.002:
        return True
    return False

def handle_data(context, data):
    for stock in g.stock:
        evaluate_by_mavg(stock)
        price = data[stock].price
        # 多头排列——满仓买入
        if is_highest_point(data,stock,-1) and context.portfolio.positions_value ==0:
            # 均线纠缠时，不进行买入操作
            if is_struggle(g.mavg10,g.mavg20,g.mavg30):
                continue
            else:
                order_target_value(stock,g.cash)
        # 空头排列——清仓卖出
        elif is_lowest_point(data,stock,-1):
            order_target_value(stock,0)
        # 多头排列后死叉——清仓卖出
        if is_crossDOWN(data,stock,g.mavg5,g.mavg10):
            order_target_value(stock,0)
        # 空头排列后金叉——满仓买入
        elif is_crossUP(data,stock,g.mavg10,g.mavg20) and context.portfolio.positions_value ==0:
            order_target_value(stock,g.cash)
    record(mavg5 = g.mavg5[-1])
    record(mavg10 = g.mavg10[-1])
    record(mavg20 = g.mavg20[-1])
    record(mavg30 = g.mavg30[-1])