# @Time : 2021/1/29 14:53
# @Author : LiuBin
# @File : StrategyBag.py
# @Description : 
# @Software: PyCharm

# XSHE XSHG
class StrategyBag:
    from jqfactor import get_factor_values


    @staticmethod
    def is_cross_shadow_line(security, unit='1d', context=None):
        """
        【回测/模拟】是否过前一个周期bar的上影线（返回1）或下影线（返回-1），否则返回0
        :param security:
        :param unit:
        :return:
        """
        last_info = get_price(security, end_date='{} 09:45:00'.format(StrategyBag.get_current_date(context)), count=1,
                              fields=['low', 'high'], frequency=unit).iloc[0]
        # last_info = attribute_history(security, 1, unit=unit, fields=['low', 'high']).iloc[0]
        # pre_price = attribute_history(security, 1, unit='15m', fields=['low', 'high']).iloc[0]
        current_price = get_current_data()[security].last_price
        if current_price < last_info['low']:
            return -1
        elif current_price > last_info['high']:
            return 1
        else:
            return 0

    @staticmethod
    def security_accumulate_return(context, security):
        """
        计算股票累计收益率（从建仓至今）
        :param context:
        :param security:
        :return:
        """
        current_price = get_current_data()[security].last_price
        cost = context.portfolio.positions[security].avg_cost
        if cost != 0:
            return (current_price - cost) / cost

    # 计算股票前n日收益率
    @staticmethod
    def security_return(security, days):
        hist = attribute_history(security, days + 1, '1d', 'close')
        security_returns = (hist['close'][-1] - hist['close'][0]) / hist['close'][0]
        return security_returns

    @staticmethod
    def get_high_or_low_price(security, days, top_n=1):
        """
        获得近n天最高TOP-N价格或最低TOP-N价格（负数）
        """
        if top_n >= 0:
            hist = attribute_history(security, days + 1, '1d', 'high')
            security_returns = hist.sort_values(by='high', ascending=False)['high'][:top_n].values.tolist()
        else:
            hist = attribute_history(security, days + 1, '1d', 'low')
            security_returns = hist.sort_values(by='low')['low'][:abs(top_n)].values.tolist()
        return security_returns

    # @staticmethod
    # def get_his_close_price(security, days):
    #     hist = attribute_history(security, days, '1d', 'close')['close'].values.tolist()
    #     return hist

# @staticmethod
# def statistic_of_limit_up_and_down():
