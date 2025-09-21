import requests
import json
from datetime import datetime
import os

# CoinGecko免费API
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"

# Discord Webhook URL (从环境变量读取，保证安全)
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')

# 监控的币种和阈值
MONITORS = {
    'bitcoin': {
        'symbol': 'BTC',
        'low_threshold': 40000,   # 低于此价格发送提醒
        'high_threshold': 70000,  # 高于此价格发送提醒
    },
    'ethereum': {
        'symbol': 'ETH',
        'low_threshold': 2500,
        'high_threshold': 4000,
    },
    'binancecoin': {
        'symbol': 'BNB',
        'low_threshold': 300,
        'high_threshold': 500,
    }
}

def get_crypto_prices():
    """从CoinGecko获取加密货币价格"""
    try:
        # 构建请求参数
        ids = ','.join(MONITORS.keys())
        params = {
            'ids': ids,
            'vs_currencies': 'usd',
            'include_24hr_change': 'true'
        }
        
        response = requests.get(COINGECKO_API_URL, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"获取价格失败: {e}")
        return None

def send_discord_alert(message):
    """发送Discord提醒"""
    if not DISCORD_WEBHOOK_URL:
        print("未设置Discord Webhook URL")
        return
    
    try:
        # Discord消息格式
        data = {
            "content": f"🚨 **加密货币价格提醒** 🚨\n{message}",
            "username": "Crypto Price Bot"
        }
        
        response = requests.post(DISCORD_WEBHOOK_URL, json=data)
        response.raise_for_status()
        print(f"提醒已发送: {message}")
    except Exception as e:
        print(f"发送Discord提醒失败: {e}")

def check_price_thresholds(prices):
    """检查价格是否触发阈值"""
    alerts = []
    
    for coin_id, thresholds in MONITORS.items():
        if coin_id in prices:
            current_price = prices[coin_id]['usd']
            symbol = thresholds['symbol']
            change_24h = prices[coin_id].get('usd_24h_change', 0)
            
            # 检查低阈值
            if current_price <= thresholds['low_threshold']:
                alert_msg = (
                    f"📉 **{symbol}** 跌破预警线！\n"
                    f"当前价格: ${current_price:,.2f}\n"
                    f"预警线: ${thresholds['low_threshold']:,.2f}\n"
                    f"24小时变化: {change_24h:.2f}%"
                )
                alerts.append(alert_msg)
            
            # 检查高阈值
            elif current_price >= thresholds['high_threshold']:
                alert_msg = (
                    f"📈 **{symbol}** 突破预警线！\n"
                    f"当前价格: ${current_price:,.2f}\n"
                    f"预警线: ${thresholds['high_threshold']:,.2f}\n"
                    f"24小时变化: {change_24h:.2f}%"
                )
                alerts.append(alert_msg)
            
            # 打印当前价格（用于日志）
            print(f"{symbol}: ${current_price:,.2f} (24h: {change_24h:.2f}%)")
    
    return alerts

def create_summary(prices):
    """创建价格摘要"""
    summary = f"📊 **价格更新** - {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}\n\n"
    
    for coin_id, thresholds in MONITORS.items():
        if coin_id in prices:
            symbol = thresholds['symbol']
            price = prices[coin_id]['usd']
            change = prices[coin_id].get('usd_24h_change', 0)
            
            # 根据涨跌添加表情
            emoji = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
            
            summary += f"{emoji} **{symbol}**: ${price:,.2f} ({change:+.2f}%)\n"
    
    return summary

def main():
    """主函数"""
    print("="*50)
    print(f"开始监控 - {datetime.now()}")
    print("="*50)
    
    # 获取价格
    prices = get_crypto_prices()
    
    if not prices:
        print("无法获取价格数据")
        return
    
    # 检查阈值
    alerts = check_price_thresholds(prices)
    
    # 发送提醒
    if alerts:
        for alert in alerts:
            send_discord_alert(alert)
    else:
        print("没有触发任何价格阈值")
        
        # 可选：每天发送一次摘要（通过GitHub Actions控制频率）
        # summary = create_summary(prices)
        # send_discord_alert(summary)

if __name__ == "__main__":
    main()