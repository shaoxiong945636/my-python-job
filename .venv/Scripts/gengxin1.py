import time
import requests
import pandas as pd
import pandas_ta as ta
from tvDatafeed import TvDatafeed, Interval

# ------------------- Pushover 配置 -------------------
PUSHOVER_USER_KEY = "uw1pocupvep9baxufiwyq6q68ztn9h"
PUSHOVER_APP_TOKEN = "agju1zzwiidyxjsoa9rrynqqu26gje"

def send_pushover(message):
    data = {
        "token": PUSHOVER_APP_TOKEN,
        "user": PUSHOVER_USER_KEY,
        "message": message
    }
    try:
        response = requests.post("https://api.pushover.net/1/messages.json", data=data)
        if response.status_code == 200:
            print(f"[通知] {message}")
        else:
            print(f"通知发送失败: {response.text}")
    except Exception as e:
        print(f"Pushover 异常: {e}")

# ------------------- TradingView 登录 -------------------
tv = TvDatafeed(username='shaoxiong945636', password='Yanwen940307!')

# ------------------- 数据获取 -------------------
def get_data(symbol, exchange, interval=Interval.in_15_minute, n_bars=130):
    """获取最近一周15分钟K线"""
    df = tv.get_hist(symbol=symbol, exchange=exchange, interval=interval, n_bars=n_bars)
    if df is None or df.empty:
        print("⚠️ 未获取到数据")
        return pd.DataFrame()
    df.index = pd.to_datetime(df.index)
    return df

# ------------------- 指标计算 -------------------
def add_indicators(df):
    # ---- KDJ ----
    kdj = ta.kdj(df["high"], df["low"], df["close"], length=9, signal=2)
    if kdj is not None and not kdj.empty:
        df["K"] = kdj.iloc[:, 0]
        df["D"] = kdj.iloc[:, 1]
        df["J"] = kdj.iloc[:, 2]
    else:
        df["K"], df["D"], df["J"] = [None]*len(df), [None]*len(df), [None]*len(df)

    # ---- MACD ----
    macd = ta.macd(df['close'], fast=4, slow=28, signal=4, mamode='ema')
    df['MACD'] = macd.iloc[:, 0]
    df['MACD_SIGNAL'] = macd.iloc[:, 1]
    df['MACD_HIST'] = macd.iloc[:, 2]

    # ---- RSI ----
    rsi = ta.rsi(df['close'], length=14)
    df['RSI'] = rsi
    return df

# ------------------- 实时监控（无绘图版） -------------------
def realtime_monitor(symbol='SMMT', exchange='NASDAQ', interval=Interval.in_15_minute,
                     n_bars=130, refresh=60, alert_interval=300):
    last_alert_time = None
    last_index = None  # 用于判断数据是否更新

    while True:
        df = get_data(symbol, exchange, interval, n_bars)
        if df.empty:
            print("未获取到数据，请检查网络或交易所代码")
        else:
            df = add_indicators(df)

            # 判断是否有新数据（最后一根K线是否变化）
            if last_index != df.index[-1]:
                last_index = df.index[-1]

                latest_k = df["K"].iloc[-1]
                latest_d = df["D"].iloc[-1]
                latest_j = df["J"].iloc[-1]
                latest_macd = df["MACD"].iloc[-1]
                latest_signal = df["MACD_SIGNAL"].iloc[-1]
                latest_hist = df["MACD_HIST"].iloc[-1]
                latest_rsi = df["RSI"].iloc[-1]

                print(f"[更新] 时间:{last_index}")
                print(f"  KDJ -> K:{latest_k:.2f}, D:{latest_d:.2f}, J:{latest_j:.2f}")
                print(f"  MACD -> MACD:{latest_macd:.4f}, SIGNAL:{latest_signal:.4f}, HIST:{latest_hist:.4f}")
                print(f"  RSI  -> {latest_rsi:.2f}")

                # 触发推送条件：J > 95 或 J < 10
                now = pd.Timestamp.now()
                if (latest_j > 95) or (latest_j < 10):
                    if (last_alert_time is None) or ((now - last_alert_time).seconds > alert_interval):
                        if latest_j > 95:
                            send_pushover(f"{symbol} ⚠️ J={latest_j:.2f} > 95，可能超买！")
                        elif latest_j < 10:
                            send_pushover(f"{symbol} ⚠️ J={latest_j:.2f} < 10，可能超卖！")
                        last_alert_time = now

        time.sleep(refresh)

# ------------------- 启动 -------------------
realtime_monitor('SMMT', 'NASDAQ', Interval.in_15_minute, n_bars=130, refresh=60)
