import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from binance.client import Client
from gate_api import SpotApi, ApiClient, Configuration

# Binance API 获取 K 线数据
def get_binance_kline_data(symbol, interval, start_time, end_time):
    api_key = 'your_api_key'
    api_secret = 'your_api_secret'
    
    client = Client(api_key, api_secret)
    
    # 将时间转换为毫秒
    start_timestamp = int(start_time.timestamp() * 1000)
    end_timestamp = int(end_time.timestamp() * 1000)
    
    klines = client.get_historical_klines(symbol, interval, start_str=start_timestamp, end_str=end_timestamp)

    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 
                                       'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 
                                       'taker_buy_quote_asset_volume', 'ignore'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['close'] = df['close'].astype(float)
    df = df[['timestamp', 'close']]
    return df

# Gate.io API 获取 K 线数据
def get_gateio_kline_data(symbol, interval, start_time, end_time):
    api_key = 'your_api_key'
    api_secret = 'your_api_secret'

    # 初始化 Gate.io API 客户端
    configuration = Configuration(key=api_key, secret=api_secret)
    api_client = ApiClient(configuration)
    spot_api = SpotApi(api_client)

    try:
        # 转换时间为 UNIX 时间戳（秒）
        start_ts = int(start_time.timestamp())
        end_ts = int(end_time.timestamp())

        # Gate.io 的时间间隔参数映射
        interval_mapping = {
            '1d': '1d',
            '1h': '1h',
            '5m': '5m',
            '1m': '1m'
        }
        gate_interval = interval_mapping.get(interval, '1d')  # 默认 1 天

        # 获取 K 线数据
        candlesticks = spot_api.list_candlesticks(symbol, _from=start_ts, to=end_ts, interval=gate_interval)

        # 正确解析 Gate.io K 线数据（8 列）
        df = pd.DataFrame(candlesticks, columns=["timestamp", "volume", "close", "high", "low", "open", "quote_volume", "trade_count"])
        
        # 转换时间戳
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
        df["close"] = df["close"].astype(float)

        # 只保留时间和收盘价
        df = df[['timestamp', 'close']]
        return df

    except Exception as e:
        st.error(f"从 Gate.io 获取 {symbol} 数据失败: {e}")
        return pd.DataFrame()

# 获取时间范围
def get_time_range(selected_time):
    end_time = pd.to_datetime('now')
    if selected_time == '2year':
        start_time = end_time - pd.DateOffset(years=2)
    elif selected_time == '1month':
        start_time = end_time - pd.DateOffset(months=1)
    elif selected_time == '1day':
        start_time = end_time - pd.DateOffset(days=1)
    return start_time, end_time

# 主函数
def main():
    st.title('Token Price Ratio Dashboard')

    # 选择时间范围
    time_choices = ['2year', '1month', '1day']
    selected_time = st.selectbox('选择时间范围', time_choices)

    # 选择时间间隔
    interval_choices = ['1d', '1h', '5m', '1m']
    selected_interval = st.selectbox('选择时间间隔', interval_choices)

    # 选择交易所
    exchange_choices = ['binance', 'gateio']
    selected_exchange = st.selectbox('选择交易所', exchange_choices)

    # 输入代币名称
    token1 = st.text_input('输入第一个代币名称 (Token 1)', 'BTC_USDT')
    token2 = st.text_input('输入第二个代币名称 (Token 2)', 'ETH_USDT')

    # 获取时间范围
    start_time, end_time = get_time_range(selected_time)

    # 获取 K 线数据
    if selected_exchange == 'binance':
        df_token1 = get_binance_kline_data(token1, selected_interval, start_time, end_time)
        df_token2 = get_binance_kline_data(token2, selected_interval, start_time, end_time)
    else:
        df_token1 = get_gateio_kline_data(token1, selected_interval, start_time, end_time)
        df_token2 = get_gateio_kline_data(token2, selected_interval, start_time, end_time)

    if df_token1.empty or df_token2.empty:
        st.error("无法获取数据，请检查代币对和交易所是否正确。")
        return

    # 合并两个 DataFrame
    df = pd.merge(df_token1[['timestamp', 'close']], df_token2[['timestamp', 'close']], on='timestamp', suffixes=('_token1', '_token2'))

    # 计算收盘价比例
    df['price_ratio'] = df['close_token1'] / df['close_token2']

    # 绘制折线图
    st.write(f"{token1} 收盘价 / {token2} 收盘价 比例")
    plt.figure(figsize=(10, 6))
    plt.plot(df['timestamp'], df['price_ratio'], label=f"{token1} / {token2}")
    plt.xlabel('time')
    plt.ylabel('ratio')
    plt.title(f"{token1} and {token2} Close Price Ratio")
    plt.xticks(rotation=45)
    plt.legend()
    st.pyplot(plt)

# 运行 Streamlit 应用
if __name__ == "__main__":
    main()
