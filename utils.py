# utils.py
import re


def standardize_model_name(model_name):
    """标准化产品型号名称"""
    if not model_name:
        return ""
    # 转换为小写并移除多余空格
    return re.sub(r'\s+', ' ', model_name.strip().lower())


def is_duplicate(favorites, new_item):
    """检查是否重复收藏"""
    for item in favorites:
        if (standardize_model_name(item.get('product_name', '')) == standardize_model_name(new_item.get('product_name', '')) and
            item.get('color') == new_item.get('color') and
            item.get('size') == new_item.get('size')):
            return True
    return False


def format_price_krw(price):
    """格式化韩元价格"""
    if not price:
        return "0원"
    try:
        price_num = int(price)
        return f"{price_num:,}원"
    except:
        return f"{price}원"


def format_price_cny(price_cny):
    """格式化人民币价格"""
    if not price_cny:
        return "¥0"
    try:
        price_num = float(price_cny)
        return f"¥{price_num:.2f}"
    except:
        return f"¥{price_cny}"


def calculate_cny_price(krw_price, exchange_rate):
    """根据汇率计算人民币价格"""
    if not krw_price or not exchange_rate:
        return 0
    
    try:
        # 提取汇率数值（格式为 "YYYY年MM月DD日，10000韩元=XX.XX人民币"）
        # 我们需要提取 XX.XX 这个数字
        rate_match = re.search(r'=(\d+\.?\d*)', exchange_rate)
        if rate_match:
            # 这是 10000 韩元对应的人民币金额
            cny_for_10000_krw = float(rate_match.group(1))
            # 计算单个产品的人民币价格
            cny_price = (krw_price / 10000) * cny_for_10000_krw
            return round(cny_price, 2)
    except:
        pass
    
    return 0


def get_stock_status_color(status):
    """获取库存状态对应的颜色"""
    if status == "有库存":
        return "🟢"
    elif status == "少量库存":
        return "🟡"
    elif status == "无库存":
        return "🔴"
    else:
        return "⚪"


def format_string(s):
    """格式化字符串用于URL构造"""
    if not s:
        return ""
    # 替换所有非字母数字字符为连字符
    s = re.sub(r'[^a-zA-Z0-9]+', '-', s)
    # 重新组合
    return s


def format_color(s):
    """格式化颜色名称"""
    if not s:
        return ""
    
    # 替换所有非字母数字字符为连字符
    s = re.sub(r'[^a-zA-Z0-9]+', '-', s)
    
    # 分割单词并处理
    words = s.split('-')
    formatted_words = []
    
    for word in words:
        if not word:
            continue
        
        # 首字母大写，其余小写
        formatted_words.append(word.capitalize())
    
    # 重新组合
    return '-'.join(formatted_words)
