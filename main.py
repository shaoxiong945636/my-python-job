from tvDatafeed import TvDatafeed, Interval
import pandas as pd
import numpy as np
from datetime import datetime

# 连接 TradingView（guest 模式也可以）
tv = TvDatafeed()

# 获取 ETH/USDT 日线，最多 5000 根
data = tv.get_hist(symbol='ETHUSDT', exchange='BINANCE', 
                   interval=Interval.in_daily, n_bars=5000)

# 计算对数收益率
data['log_ret'] = np.log(data['close'] / data['close'].shift(1))

# 计算 20 日历史波动率（年化）
data['hv20'] = data['log_ret'].rolling(20).std() * np.sqrt(252)

# 保存 CSV 文件，带日期
today = datetime.utcnow().strftime('%Y-%m-%d')
filename = f'eth_data_{today}.csv'
data.to_csv(filename)

print(f"ETH 数据抓取完成，保存为 {filename}")
