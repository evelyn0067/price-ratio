import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# 从 Binance 获取 K线数据的函数
from binance.client import Client

def get_binance_kline_data(symbol, interval, start_time, end_time):
    # 使用您的 API 密钥
    api_key = 'your_api_key'
    api_secret = 'your_api_secret'
    
    client = Client(api_key, api_secret)
    
    # 将 start_time 和 end_time 转换为时间戳（毫秒）
    start_timestamp = int(start_time.timestamp() * 1000)  # 转换为毫秒
    end_timestamp = int(end_time.timestamp() * 1000)      # 转换为毫秒
    
    # 获取历史K线数据
    klines = client.get_historical_klines(symbol, interval, start_str=start_timestamp, end_str=end_timestamp)
    
    # 转换为 DataFrame
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['close'] = df['close'].astype(float)
    df = df[['timestamp', 'close']]
    return df

# 从 Gate.io 获取 K线数据的函数
#from gate_api import ApiClient, GateApiException
#from gate_api.models import Ticker

def get_gateio_kline_data(symbol, interval, start_time, end_time):
    api_key = 'your_api_key'
    api_secret = 'your_api_secret'
    
    client = ApiClient(api_key, api_secret)
    
    # Gate.io 获取K线数据的API不直接支持获取历史K线
    # Gate.io并没有提供直接获取K线数据的API，而是通过其他API间接获取历史数据
    # 因此我们需要额外使用外部服务进行数据获取。
    st.warning("Gate.io 暂时不支持直接通过 Python 库获取历史K线数据, 请考虑其他数据源。")
    return pd.DataFrame()

# 获取时间范围
def get_time_range(selected_time):
    end_time = pd.to_datetime('now')
    if selected_time == '1year':
        start_time = end_time - pd.DateOffset(years=1)
    elif selected_time == '1month':
        start_time = end_time - pd.DateOffset(months=1)
    elif selected_time == '1day':
        start_time = end_time - pd.DateOffset(days=1)
    return start_time, end_time

# 主函数
def main():
    st.title('Token Price Ratio Dashboard')

    # 创建选择时间范围的控件
    time_choices = ['1year', '1month', '1day']
    selected_time = st.selectbox('选择时间范围', time_choices)

    # 创建选择数据间隔的控件
    interval_choices = ['1d', '1h']
    selected_interval = st.selectbox('选择时间间隔', interval_choices)

    # 创建选择交易所的控件
    exchange_choices = ['binance', 'gateio']
    selected_exchange = st.selectbox('选择交易所', exchange_choices)

    # 输入代币名称
    token1 = st.text_input('输入第一个代币名称 (Token 1)', 'BTCUSDT')
    token2 = st.text_input('输入第二个代币名称 (Token 2)', 'ETHUSDT')

    # 获取时间范围
    start_time, end_time = get_time_range(selected_time)

    # 获取K线数据
    if selected_exchange == 'binance':
        df_token1 = get_binance_kline_data(token1, selected_interval, start_time, end_time)
        df_token2 = get_binance_kline_data(token2, selected_interval, start_time, end_time)
    else:
        df_token1 = get_gateio_kline_data(token1, selected_interval, start_time, end_time)
        df_token2 = get_gateio_kline_data(token2, selected_interval, start_time, end_time)

    if df_token1.empty or df_token2.empty:
        st.error("无法获取数据，请检查代币对和交易所是否正确。")
        return

    # 对齐两个 DataFrame 的时间戳
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
