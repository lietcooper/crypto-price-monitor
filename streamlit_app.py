import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import json

# 页面配置
st.set_page_config(
    page_title="Crypto Price Monitor",
    page_icon="📈",
    layout="wide"
)

# CoinGecko API
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"

# 默认监控的币种
DEFAULT_COINS = {
    'bitcoin': {'symbol': 'BTC', 'name': 'Bitcoin'},
    'ethereum': {'symbol': 'ETH', 'name': 'Ethereum'},
    'binancecoin': {'symbol': 'BNB', 'name': 'Binance Coin'},
    'solana': {'symbol': 'SOL', 'name': 'Solana'},
    'cardano': {'symbol': 'ADA', 'name': 'Cardano'}
}

@st.cache_data(ttl=60)  # 缓存1分钟
def get_crypto_prices(coin_ids):
    """获取加密货币实时价格"""
    try:
        ids = ','.join(coin_ids)
        params = {
            'ids': ids,
            'vs_currencies': 'usd',
            'include_24hr_vol': 'true',
            'include_24hr_change': 'true',
            'include_last_updated_at': 'true'
        }
        
        response = requests.get(f"{COINGECKO_API_URL}/simple/price", params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"获取价格失败: {e}")
        return None

@st.cache_data(ttl=300)  # 缓存5分钟
def get_price_history(coin_id, days=7):
    """获取历史价格数据"""
    try:
        params = {
            'vs_currency': 'usd',
            'days': days,
            'interval': 'daily' if days > 1 else 'hourly'
        }
        
        response = requests.get(
            f"{COINGECKO_API_URL}/coins/{coin_id}/market_chart",
            params=params
        )
        response.raise_for_status()
        data = response.json()
        
        # 转换为DataFrame
        prices = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
        prices['timestamp'] = pd.to_datetime(prices['timestamp'], unit='ms')
        return prices
    except Exception as e:
        st.error(f"获取历史数据失败: {e}")
        return None

def create_price_chart(coin_data, coin_name):
    """创建价格图表"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=coin_data['timestamp'],
        y=coin_data['price'],
        mode='lines',
        name=coin_name,
        line=dict(color='#1f77b4', width=2),
        fill='tozeroy',
        fillcolor='rgba(31, 119, 180, 0.1)'
    ))
    
    fig.update_layout(
        title=f"{coin_name} 价格走势",
        xaxis_title="时间",
        yaxis_title="价格 (USD)",
        hovermode='x unified',
        height=400,
        template='plotly_white'
    )
    
    return fig

def main():
    # 标题和描述
    st.title("🚀 Crypto Price Monitor Dashboard")
    st.markdown("实时监控加密货币价格，设置提醒阈值")
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 配置")
        
        # 选择要监控的币种
        selected_coins = st.multiselect(
            "选择监控币种",
            options=list(DEFAULT_COINS.keys()),
            default=list(DEFAULT_COINS.keys())[:3],
            format_func=lambda x: f"{DEFAULT_COINS[x]['symbol']} - {DEFAULT_COINS[x]['name']}"
        )
        
        # 刷新间隔
        auto_refresh = st.checkbox("自动刷新", value=True)
        if auto_refresh:
            refresh_interval = st.slider("刷新间隔（秒）", 10, 300, 60)
        
        # 图表时间范围
        chart_days = st.selectbox(
            "图表时间范围",
            options=[1, 7, 30, 90],
            format_func=lambda x: f"{x}天",
            index=1
        )
        
        st.divider()
        
        # 价格提醒设置
        st.subheader("🔔 价格提醒")
        alert_enabled = st.checkbox("启用价格提醒")
        
        if alert_enabled:
            selected_alert_coin = st.selectbox(
                "选择币种",
                options=selected_coins,
                format_func=lambda x: DEFAULT_COINS[x]['symbol']
            )
            
            col1, col2 = st.columns(2)
            with col1:
                low_threshold = st.number_input(
                    "低价提醒 ($)",
                    min_value=0.0,
                    value=30000.0 if selected_alert_coin == 'bitcoin' else 100.0,
                    step=100.0
                )
            with col2:
                high_threshold = st.number_input(
                    "高价提醒 ($)",
                    min_value=0.0,
                    value=50000.0 if selected_alert_coin == 'bitcoin' else 1000.0,
                    step=100.0
                )
    
    # 主界面
    if not selected_coins:
        st.warning("请在侧边栏选择至少一个币种")
        return
    
    # 获取实时价格
    prices = get_crypto_prices(selected_coins)
    
    if prices:
        # 显示价格卡片
        st.subheader("📊 实时价格")
        
        cols = st.columns(len(selected_coins))
        for idx, coin_id in enumerate(selected_coins):
            with cols[idx]:
                if coin_id in prices:
                    coin_info = DEFAULT_COINS[coin_id]
                    price_data = prices[coin_id]
                    
                    # 价格变化指示器
                    change_24h = price_data.get('usd_24h_change', 0)
                    change_color = "🟢" if change_24h > 0 else "🔴" if change_24h < 0 else "⚪"
                    
                    # 显示价格卡片
                    st.metric(
                        label=f"{change_color} {coin_info['symbol']}",
                        value=f"${price_data['usd']:,.2f}",
                        delta=f"{change_24h:.2f}%"
                    )
                    
                    # 检查价格提醒
                    if alert_enabled and coin_id == selected_alert_coin:
                        current_price = price_data['usd']
                        if current_price <= low_threshold:
                            st.error(f"⚠️ {coin_info['symbol']} 已跌破 ${low_threshold:,.2f}!")
                        elif current_price >= high_threshold:
                            st.success(f"🎯 {coin_info['symbol']} 已突破 ${high_threshold:,.2f}!")
        
        # 更新时间
        st.caption(f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        st.divider()
        
        # 价格走势图表
        st.subheader("📈 价格走势")
        
        # 选择要显示图表的币种
        chart_coin = st.selectbox(
            "选择币种查看详细走势",
            options=selected_coins,
            format_func=lambda x: DEFAULT_COINS[x]['name'],
            label_visibility="collapsed"
        )
        
        # 获取并显示历史价格
        with st.spinner("加载历史数据..."):
            history = get_price_history(chart_coin, chart_days)
            
            if history is not None and not history.empty:
                # 创建两列布局
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # 显示图表
                    fig = create_price_chart(history, DEFAULT_COINS[chart_coin]['name'])
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # 统计信息
                    st.markdown("### 📊 统计")
                    current_price = prices[chart_coin]['usd']
                    
                    # 计算统计数据
                    max_price = history['price'].max()
                    min_price = history['price'].min()
                    avg_price = history['price'].mean()
                    
                    st.metric("当前价格", f"${current_price:,.2f}")
                    st.metric("最高价格", f"${max_price:,.2f}")
                    st.metric("最低价格", f"${min_price:,.2f}")
                    st.metric("平均价格", f"${avg_price:,.2f}")
                    
                    # 波动率
                    volatility = ((max_price - min_price) / avg_price) * 100
                    st.metric("波动率", f"{volatility:.2f}%")
        
        # 详细数据表格
        with st.expander("📋 查看详细数据"):
            # 创建数据表
            table_data = []
            for coin_id in selected_coins:
                if coin_id in prices:
                    coin_info = DEFAULT_COINS[coin_id]
                    price_data = prices[coin_id]
                    
                    table_data.append({
                        '币种': coin_info['name'],
                        '符号': coin_info['symbol'],
                        '当前价格': f"${price_data['usd']:,.2f}",
                        '24h变化': f"{price_data.get('usd_24h_change', 0):.2f}%",
                        '24h交易量': f"${price_data.get('usd_24h_vol', 0):,.0f}",
                        '最后更新': datetime.fromtimestamp(
                            price_data.get('last_updated_at', 0)
                        ).strftime('%H:%M:%S')
                    })
            
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        # 自动刷新
        if auto_refresh:
            time.sleep(refresh_interval)
            st.rerun()
    
    else:
        st.error("无法获取价格数据，请稍后重试")
    
    # 页脚
    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
            Built with ❤️ using Streamlit | Data from CoinGecko API
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()