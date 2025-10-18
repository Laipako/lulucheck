# exchange_rate.py
import requests
import json
from datetime import datetime, timedelta
import streamlit as st


@st.cache_data(ttl=3600)
def get_exchange_rate():
    """
    获取韩元兑人民币汇率（银联数据）
    返回格式：10000 KRW = XX.XX CNY
    """
    # 获取当前日期和前一天的日期
    today = datetime.now()
    yesterday = today - timedelta(days=1)

    date_list = [
        today.strftime("%Y%m%d"),
        yesterday.strftime("%Y%m%d")
    ]

    for date_str in date_list:
        try:
            url = f"https://www.unionpayintl.com/upload/jfimg/{date_str}.json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            # 使用正确的键名 exchangeRateJson
            for rate in data.get('exchangeRateJson', []):
                if rate.get('transCur') == 'KRW' and rate.get('baseCur') == 'CNY':
                    krw_to_cny = float(rate.get('rateData', 0))

                    # 计算优惠汇率
                    normal_rate = 10000 * krw_to_cny
                    discount_rate = normal_rate - 0.05
                    discount_rate = round(discount_rate, 2)

                    # 格式化日期
                    display_date = datetime.strptime(date_str, "%Y%m%d").strftime("%Y年%m月%d日")

                    return f"{display_date}，10000韩元={discount_rate}人民币"

        except Exception as e:
            print(f"汇率获取失败 {date_str}: {e}")
            continue

    return ""  # 失败时返回空字符串
