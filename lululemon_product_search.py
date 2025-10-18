import requests
import re
import urllib.parse
import html
from bs4 import BeautifulSoup
import streamlit as st
from product_translation import get_product_translation


def search_lululemon_products(search_query):
    """
    搜索Lululemon产品
    基于666文件夹中的搜索确定产品URL.py
    """
    try:
        # 构建搜索URL
        search_url = f"https://www.lululemon.co.kr/ko-kr/search?q={urllib.parse.quote(search_query)}&lang=ko_KR&searchType=manualSearch"
        
        # 使用ScraperAPI获取页面内容
        payload = {
            'api_key': '420b6b6ad161ba091d728cba109b8df5',
            'url': search_url
        }
        
        r = requests.get('https://api.scraperapi.com/', params=payload, timeout=10)
        r.raise_for_status()
        html_content = r.text
        
        # 提取产品信息
        pattern = r'role="link" aria-label=".+?" data-lulu-track="search-results-srp-product-link" data-lulu-attributes="\{\'type\':\'product\',\'version\':\'.+?\,\'product\':{\'name\':\'(.+?)\',\'skuID\':\'\',\'productID\':\'(.+?)\',\'categoryUnifiedID\':\'(.+?)\',\'color\':\'.+?\',\'badge\':\[.+?\],\'styleID\':\'.+?\',\'deliveryType\':\'\',\'quantity\':.+?,\'price\':(.+?)\},\'attributes\':\{\'component\':\'product-list\',\'displayType\':\'tile\'\}\}" href="(.+?)"'
        
        matches = re.findall(pattern, html_content, re.DOTALL)
        
        products = []
        for i, match in enumerate(matches, 1):
            try:
                url_encoded_name = match[0]
                product_id = match[1]
                category_unified = match[2]
                product_price = match[3]
                product_url = match[4]
                
                # 使用翻译模块获取韩文和英文名称
                translation_result = get_product_translation(url_encoded_name)
                
                # 创建产品信息字典
                product_info = {
                    'index': i,
                    'product_id': product_id,
                    'category_unified': category_unified,
                    'korean_name': translation_result['korean_name'],
                    'english_name': translation_result['english_name'],
                    'product_price': product_price,
                    'product_url': product_url,
                    'url_encoded_name': url_encoded_name
                }
                
                products.append(product_info)
                
            except Exception as e:
                print(f"处理第 {i} 个产品时出错: {e}")
                continue
        
        return products
        
    except Exception as e:
        print(f"搜索产品失败: {e}")
        return []


def get_product_details(product_url):
    """
    获取产品详细信息（颜色、尺码、SKU等）
    基于666文件夹中的确定SKU.py和10.py
    """
    try:
        # 使用ScraperAPI获取页面内容
        payload = {
            'api_key': '420b6b6ad161ba091d728cba109b8df5',
            'url': product_url
        }
        
        r = requests.get('https://api.scraperapi.com/', params=payload, timeout=10)
        r.raise_for_status()
        html_content = r.text
        
        # 提取颜色选项
        color_options = extract_color_options(html_content)
        
        # 提取颜色、价格和图片数据（新增）
        color_price_image_data = extract_color_price_image_data(html_content)
        
        # 提取尺码选项
        size_options = extract_size_options(html_content)
        
        # 提取SKU映射关系
        sku_mapping = extract_sku_mapping(html_content)
        
        # 提取完整产品信息
        product_mapping = extract_product_details_from_html(html_content)
        
        return {
            'color_options': color_options,
            'color_price_image_data': color_price_image_data,  # 新增：包含图片的颜色数据
            'size_options': size_options,
            'sku_mapping': sku_mapping,
            'product_mapping': product_mapping
        }
        
    except Exception as e:
        print(f"获取产品详情失败: {e}")
        return None


def extract_color_options(html_content):
    """提取颜色选项"""
    soup = BeautifulSoup(html_content, 'html.parser')
    color_options = []

    color_groups = soup.select('div.color-group')
    for group in color_groups:
        color_buttons = group.select('button[data-color-title]')
        for button in color_buttons:
            color_name = button.get('data-color-title', '').strip()
            if color_name:
                # 提取价格
                price_element = group.select_one('span.markdown-prices')
                price_text = price_element.get_text(strip=True) if price_element else "价格未知"
                color_options.append([color_name, price_text])  # 使用list而不是tuple

    return color_options


def extract_color_price_image_data(html_content):
    """提取颜色、价格和图片的对应关系（增强版）"""
    soup = BeautifulSoup(html_content, 'html.parser')
    color_data = []
    
    color_groups = soup.select('div.color-group')
    for group in color_groups:
        color_buttons = group.select('button[data-color-title]')
        
        for button in color_buttons:
            color_name = button.get('data-color-title', '').strip()
            color_code = button.get('data-attr-value', '')
            
            if not color_name:
                color_name = button.get('data-original-title', '').strip()
            if not color_name:
                color_name = button.get('aria-label', '').replace('swatch - ', '').strip()
            
            # 提取价格
            price_element = group.select_one('span.markdown-prices')
            current_price = None
            original_price = None
            price_text = ""
            
            if price_element:
                price_text = price_element.get_text(strip=True)
                prices = re.findall(r'[\d,]+', price_text)
                if prices:
                    current_price = int(prices[0].replace(',', ''))
                    if len(prices) > 1:
                        original_price = int(prices[1].replace(',', ''))
            
            # 提取图片URL - 多种尝试
            img_url = ""
            
            # 方法1: 检查按钮内的 img.color-swatch-bg
            img_element = button.select_one('img.color-swatch-bg')
            if img_element:
                if img_element.get('src'):
                    img_url = img_element['src']
                elif img_element.get('data-src'):
                    img_url = img_element['data-src']
                elif img_element.get('data-lazy-src'):
                    img_url = img_element['data-lazy-src']
            
            # 方法2: 检查按钮的背景图片
            if not img_url:
                style = button.get('style', '')
                if 'background-image' in style:
                    # 提取 URL 从 background-image: url(...)
                    import re as regex
                    match = regex.search(r"url\(['\"]?([^'\"()]+)['\"]?\)", style)
                    if match:
                        img_url = match.group(1)
            
            # 方法3: 检查按钮的 data-image 属性
            if not img_url:
                img_url = button.get('data-image', '')
            
            # 方法4: 检查相邻的 img 元素
            if not img_url:
                img = button.find('img')
                if img and img.get('src'):
                    img_url = img['src']
                elif img and img.get('data-src'):
                    img_url = img['data-src']
                elif img and img.get('data-lazy-src'):
                    img_url = img['data-lazy-src']
            
            # 方法5: 检查父级元素中的图片
            if not img_url:
                parent_img = button.find_parent().select_one('img')
                if parent_img:
                    img_url = parent_img.get('src') or parent_img.get('data-src') or parent_img.get('data-lazy-src')
            
            # 方法6: 检查所有可能的图片属性
            if not img_url:
                for attr in ['data-img', 'data-image-url', 'data-src', 'data-lazy-src']:
                    if button.get(attr):
                        img_url = button.get(attr)
                        break
            
            if color_name:
                color_data.append({
                    'color_name': color_name,
                    'color_code': color_code,
                    'current_price': current_price,
                    'original_price': original_price,
                    'image_url': img_url,
                    'price_text': price_text
                })
                
                # 打印调试信息
                print(f"颜色: {color_name}, 图片URL: {img_url}")
                if not img_url:
                    print(f"  - 未找到图片URL，按钮HTML: {str(button)[:200]}...")
                    # 打印所有可能的属性
                    for attr in button.attrs:
                        if 'img' in attr.lower() or 'src' in attr.lower() or 'image' in attr.lower():
                            print(f"  - 属性 {attr}: {button.get(attr)}")
    
    return color_data


def extract_size_options(html_content):
    """提取尺码选项"""
    soup = BeautifulSoup(html_content, 'html.parser')
    size_options = []

    size_labels = soup.select('span.size-btns label')
    for label in size_labels:
        size_text = label.get_text(strip=True)
        if size_text:
            # 提取纯尺码代码（去掉KR信息）
            size_code = size_text.split('(')[0].strip()
            size_options.append([size_code, size_text])  # 使用list而不是tuple

    return size_options


def extract_sku_mapping(html_content):
    """提取SKU映射关系"""
    pattern = r'{"attributes":{"stockStatus":"([^"]+)"},"productInfo":{"sku":"([^"]+)","productId":"[^"]+","productName":"[^"]+","color":"([^"]+)","size":"([^"]+)"}}'

    matches = re.findall(pattern, html_content)
    sku_mapping = {}

    for match in matches:
        stock_status, sku, color, size = match
        key = f"{color}_{size}"  # 使用字符串而不是tuple
        sku_mapping[key] = [stock_status, sku]  # 使用list而不是tuple

    return sku_mapping


def extract_product_details_from_html(html_content):
    """提取完整产品信息"""
    pattern = r'{"@type":"[^"]+","name":"[^"]+","image":"([^"]+)","sku":"([^"]+)","color":"([^"]+)","size":"([^"]+)","offers":{"@type":"[^"]+","itemCondition":"[^"]+","availability":"([^"]+)","url":"[^"]+","priceCurrency":"KRW","price":([^"]+)}}'

    matches = re.findall(pattern, html_content)
    product_mapping = {}

    for match in matches:
        image_url, sku, color, size, availability, price = match

        # 处理尺码格式（去掉KR信息）
        size_clean = size.split('(')[0].strip()

        # 处理库存状态
        if availability == "http://schema.org/InStock":
            stock_status = "有库存"
        else:
            stock_status = "无库存"

        key = f"{color}_{size_clean}"  # 使用字符串而不是tuple
        product_mapping[key] = {
            'image_url': image_url,
            'sku': sku,
            'stock_status': stock_status,
            'price': price
        }

    return product_mapping
