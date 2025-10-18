import time
import streamlit as st
from discount_config import DISCOUNT_CONFIG
import pandas as pd
from lululemon_product_search import search_lululemon_products, get_product_details
from lululemon_inventory_check import (
    query_stock_by_sku, calculate_enhanced_inventory_stats, calculate_product_depth_stats, 
    calculate_key_store_analysis, calculate_stock_status_distribution, calculate_region_heatmap,
    calculate_product_depth_stats_by_region, calculate_enhanced_inventory_stats_combined
)
from lululemon_favorites_manager import load_favorites, add_to_favorites, remove_from_favorites, batch_check_favorites_inventory, calculate_favorites_summary, clear_favorites
from utils import standardize_model_name, format_price_krw, format_price_cny, calculate_cny_price, get_stock_status_color
from exchange_rate import get_exchange_rate
import re
import json
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib
# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
# import seaborn as sns

# 缓存配置
CACHE_DIR = "cache"
CACHE_EXPIRY_HOURS = 24  # 缓存24小时过期
INVENTORY_CACHE_HOURS = 2  # 库存缓存2小时过期
PRODUCT_CACHE_HOURS = 12  # 产品详情缓存12小时过期

def ensure_cache_dir():
    """确保缓存目录存在"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def get_cache_file_path(query):
    """获取缓存文件路径"""
    ensure_cache_dir()
    # 使用查询的hash作为文件名
    import hashlib
    query_hash = hashlib.md5(query.encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"search_{query_hash}.json")

def is_cache_valid(cache_file, cache_type="search"):
    """检查缓存是否有效"""
    if not os.path.exists(cache_file):
        return False
    
    # 根据缓存类型设置不同的过期时间
    if cache_type == "inventory":
        expiry_hours = INVENTORY_CACHE_HOURS
    elif cache_type == "product":
        expiry_hours = PRODUCT_CACHE_HOURS
    else:
        expiry_hours = CACHE_EXPIRY_HOURS
    
    # 检查文件修改时间
    file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
    expiry_time = file_time + timedelta(hours=expiry_hours)
    return datetime.now() < expiry_time

@st.cache_data(ttl=3600)  # 1小时内存缓存
def get_cached_exchange_rate():
    """获取缓存的汇率"""
    return get_exchange_rate()

@st.cache_data(ttl=7200)  # 2小时内存缓存
def get_cached_product_search(query):
    """获取缓存的产品搜索结果"""
    cache_file = get_cache_file_path(query)
    if is_cache_valid(cache_file, "search"):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('search_results', [])
        except Exception as e:
            print(f"缓存加载失败: {e}")
    return None

@st.cache_data(ttl=1800)  # 30分钟内存缓存
def get_cached_inventory(sku, region):
    """获取缓存的库存数据"""
    cache_key = f"inventory_{sku}_{region}"
    cache_file = get_cache_file_path(cache_key)
    if is_cache_valid(cache_file, "inventory"):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('stores', [])
        except Exception as e:
            print(f"库存缓存加载失败: {e}")
    return None

def save_inventory_cache(sku, region, stores):
    """保存库存数据到缓存"""
    cache_key = f"inventory_{sku}_{region}"
    cache_file = get_cache_file_path(cache_key)
    try:
        cache_data = {
            'stores': stores,
            'cached_at': datetime.now().isoformat(),
            'sku': sku,
            'region': region
        }
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        print(f"库存数据已缓存: {cache_key}")
    except Exception as e:
        print(f"库存缓存保存失败: {e}")

def load_from_cache(query):
    """从缓存加载数据"""
    cache_file = get_cache_file_path(query)
    if is_cache_valid(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 处理数据中的字符串键，转换回tuple
                def convert_string_keys_back(obj):
                    if isinstance(obj, dict):
                        new_dict = {}
                        for key, value in obj.items():
                            if isinstance(key, str) and '|' in key and not key.startswith('http'):
                                # 尝试将字符串键转换回tuple
                                try:
                                    parts = key.split('|')
                                    if len(parts) == 2:
                                        new_key = (parts[0], parts[1])
                                        new_dict[new_key] = convert_string_keys_back(value)
                                    else:
                                        new_dict[key] = convert_string_keys_back(value)
                                except:
                                    new_dict[key] = convert_string_keys_back(value)
                            else:
                                new_dict[key] = convert_string_keys_back(value)
                        return new_dict
                    elif isinstance(obj, list):
                        return [convert_string_keys_back(item) for item in obj]
                    else:
                        return obj
                
                return convert_string_keys_back(data)
        except Exception as e:
            print(f"缓存加载失败: {e}")
    return None

def save_to_cache(query, data):
    """保存数据到缓存"""
    cache_file = get_cache_file_path(query)
    try:
        # 处理数据中的tuple键，转换为字符串
        def convert_tuple_keys(obj):
            if isinstance(obj, dict):
                new_dict = {}
                for key, value in obj.items():
                    if isinstance(key, tuple):
                        # 将tuple键转换为字符串
                        new_key = f"{key[0]}|{key[1]}" if len(key) == 2 else str(key)
                        new_dict[new_key] = convert_tuple_keys(value)
                    else:
                        new_dict[key] = convert_tuple_keys(value)
                return new_dict
            elif isinstance(obj, list):
                return [convert_tuple_keys(item) for item in obj]
            else:
                return obj
        
        # 转换数据中的tuple键
        converted_data = convert_tuple_keys(data)
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(converted_data, f, ensure_ascii=False, indent=2)
        print(f"数据已缓存到: {cache_file}")
    except Exception as e:
        print(f"缓存保存失败: {e}")

def preload_soft_jersey_data():
    """预加载soft jersey产品数据"""
    query = "soft jersey"
    cache_file = get_cache_file_path(query)
    
    # 如果缓存不存在或已过期，则搜索并缓存
    if not is_cache_valid(cache_file):
        print("正在预加载soft jersey数据...")
        try:
            # 搜索soft jersey产品
            results = search_lululemon_products(query)
            if results and len(results) > 0:
                # 获取第一个产品的详细信息
                first_product = results[0]
                product_details = get_product_details(first_product['product_url'])
                
                # 保存到缓存
                cache_data = {
                    'search_results': results,
                    'product_details': product_details,
                    'cached_at': datetime.now().isoformat(),
                    'query': query
                }
                save_to_cache(query, cache_data)
                print(f"Soft jersey数据已预加载到缓存")
            else:
                print("未找到soft jersey产品")
        except Exception as e:
            print(f"预加载soft jersey数据失败: {e}")
    else:
        print("Soft jersey数据已在缓存中")

def get_cache_stats():
    """获取缓存统计信息"""
    if not os.path.exists(CACHE_DIR):
        return {"total_files": 0, "total_size": 0, "search_files": 0, "inventory_files": 0, "product_files": 0}
    
    total_files = 0
    total_size = 0
    search_files = 0
    inventory_files = 0
    product_files = 0
    
    for filename in os.listdir(CACHE_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(CACHE_DIR, filename)
            total_files += 1
            total_size += os.path.getsize(filepath)
            
            if filename.startswith('search_'):
                search_files += 1
            elif filename.startswith('inventory_'):
                inventory_files += 1
            elif filename.startswith('product_details_'):
                product_files += 1
    
    return {
        "total_files": total_files,
        "total_size": total_size,
        "search_files": search_files,
        "inventory_files": inventory_files,
        "product_files": product_files
    }

def clear_cache_by_type(cache_type="all"):
    """清理指定类型的缓存"""
    if not os.path.exists(CACHE_DIR):
        return 0
    
    deleted_count = 0
    
    for filename in os.listdir(CACHE_DIR):
        if filename.endswith('.json'):
            should_delete = False
            
            if cache_type == "all":
                should_delete = True
            elif cache_type == "search" and filename.startswith('search_'):
                should_delete = True
            elif cache_type == "inventory" and filename.startswith('inventory_'):
                should_delete = True
            elif cache_type == "product" and filename.startswith('product_details_'):
                should_delete = True
            
            if should_delete:
                filepath = os.path.join(CACHE_DIR, filename)
                try:
                    os.remove(filepath)
                    deleted_count += 1
                except Exception as e:
                    print(f"删除缓存文件失败: {filename}, 错误: {e}")
    
    return deleted_count

def show_cache_management():
    """显示缓存管理页面"""
    st.header("🗂️ 缓存管理")
    
    # 获取缓存统计
    stats = get_cache_stats()
    
    # 显示缓存统计信息
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总缓存文件", stats["total_files"])
    with col2:
        st.metric("总缓存大小", f"{stats['total_size'] / 1024 / 1024:.2f} MB")
    with col3:
        st.metric("搜索缓存", stats["search_files"])
    with col4:
        st.metric("库存缓存", stats["inventory_files"])
    
    st.markdown("---")
    
    # 缓存清理选项
    st.subheader("清理缓存")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("清理所有缓存", use_container_width=True):
            deleted = clear_cache_by_type("all")
            st.success(f"已清理 {deleted} 个缓存文件")
            st.rerun()
    
    with col2:
        if st.button("清理搜索缓存", use_container_width=True):
            deleted = clear_cache_by_type("search")
            st.success(f"已清理 {deleted} 个搜索缓存文件")
            st.rerun()
    
    with col3:
        if st.button("清理库存缓存", use_container_width=True):
            deleted = clear_cache_by_type("inventory")
            st.success(f"已清理 {deleted} 个库存缓存文件")
            st.rerun()
    
    with col4:
        if st.button("清理产品缓存", use_container_width=True):
            deleted = clear_cache_by_type("product")
            st.success(f"已清理 {deleted} 个产品缓存文件")
            st.rerun()
    
    # 缓存优化建议
    st.markdown("---")
    st.subheader("缓存优化建议")
    
    if stats["total_size"] > 100:  # 超过100MB
        st.warning("⚠️ 缓存文件较大，建议清理过期缓存")
    
    if stats["inventory_files"] > 50:  # 库存缓存文件过多
        st.info("💡 库存缓存文件较多，建议定期清理以提高性能")
    
    if stats["total_files"] == 0:
        st.success("✅ 缓存目录为空，系统运行正常")
    
    # 智能缓存建议
    st.markdown("---")
    st.subheader("智能缓存策略")
    
    # 根据使用情况提供智能建议
    if stats["search_files"] > 10:
        st.info("🔍 搜索缓存较多，系统已优化搜索性能")
    
    if stats["inventory_files"] > 20:
        st.info("📦 库存缓存充足，批量查询将显著提速")
    
    # 缓存命中率估算
    total_cache_size_mb = stats["total_size"] / 1024 / 1024
    if total_cache_size_mb > 0:
        st.metric("缓存效率", f"{(total_cache_size_mb / max(1, stats['total_files'])):.2f} MB/文件")
    
    # 性能优化提示
    st.markdown("### 💡 性能优化提示")
    
    if stats["total_files"] > 100:
        st.warning("缓存文件较多，建议定期清理以提高系统响应速度")
    elif stats["total_files"] > 50:
        st.info("缓存文件适中，系统运行良好")
    else:
        st.success("缓存文件较少，系统运行高效")
    
    # 自动清理建议
    if stats["total_size"] > 200:  # 超过200MB
        st.error("⚠️ 缓存占用空间较大，建议立即清理")
    elif stats["total_size"] > 100:  # 超过100MB
        st.warning("⚠️ 缓存占用空间较大，建议考虑清理")
    else:
        st.success("✅ 缓存占用空间合理")


def get_current_step():
    """获取当前步骤"""
    if "step_history" not in st.session_state:
        st.session_state.step_history = ["start"]
    return st.session_state.step_history[-1]


def go_to_step(step_name):
    """跳转到指定步骤"""
    if "step_history" not in st.session_state:
        st.session_state.step_history = ["start"]
    st.session_state.step_history.append(step_name)
    st.rerun()


def go_back():
    """回退到上一步"""
    if len(st.session_state.step_history) > 1:
        st.session_state.step_history.pop()
        st.rerun()


# 页面配置
st.set_page_config(
    page_title="Lululemon查货系统",
    page_icon="🧘‍♀️",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def display_product_image(image_url, alt_text="产品图片"):
    """显示产品图片（限制尺寸，避免过大）"""
    # 占位图URL（使用Streamlit内置的占位图）
    placeholder_image = "https://via.placeholder.com/200x200/cccccc/969696?text=图片加载失败"

    if image_url and image_url.strip():
        try:
            # 验证图片URL格式
            if not image_url.startswith(('http://', 'https://')):
                st.image(placeholder_image, caption="图片URL格式错误", width=200)
                return
            
            # 限制图片宽度为200px，避免过大
            st.image(image_url, caption=alt_text, width=200)
        except Exception as e:
            st.image(placeholder_image, caption=f"图片加载失败: {str(e)[:50]}", width=200)
            print(f"图片加载失败 - URL: {image_url}, 错误: {e}")
    else:
        st.image(placeholder_image, caption="暂无图片", width=200)


def main():
    """主函数"""
    # 预加载soft jersey数据（仅在首次运行时）
    if "soft_jersey_preloaded" not in st.session_state:
        preload_soft_jersey_data()
        st.session_state.soft_jersey_preloaded = True
    
    # 获取汇率信息（使用缓存）
    exchange_rate_info = get_cached_exchange_rate()
    
    # 页面标题
    st.title("🧘‍♀️ Lululemon查货系统")
    
    # 汇率显示
    if exchange_rate_info:
        st.info(f"💱 汇率信息: {exchange_rate_info}")
    
    # 获取当前步骤
    current_step = get_current_step()
    
    # 侧边栏导航
    with st.sidebar:
        st.header("导航菜单")
        
        if st.button("🏠 首页", use_container_width=True):
            go_to_step("start")
        
        if st.button("🔍 产品搜索", use_container_width=True):
            go_to_step("search")
        
        if st.button("📦 库存查询", use_container_width=True):
            go_to_step("inventory")
        
        if st.button("❤️ 我的收藏", use_container_width=True):
            go_to_step("favorites")
        
        if st.button("🗂️ 缓存管理", use_container_width=True):
            go_to_step("cache_management")
        
    
    # 根据当前步骤显示不同内容
    if current_step == "start":
        show_home_page()
    elif current_step == "search":
        show_search_page()
    elif current_step == "product_detail":
        if "selected_product" in st.session_state:
            show_product_detail(st.session_state.selected_product)
        else:
            st.warning("未选择产品")
            go_to_step("search")
    elif current_step == "color_selection":
        if "selected_product" in st.session_state:
            show_color_selection()
        else:
            st.warning("未选择产品")
            go_to_step("search")
    elif current_step == "size_selection":
        if "selected_product" in st.session_state and "selected_color" in st.session_state:
            show_size_selection()
        else:
            st.warning("未选择产品或颜色")
            go_to_step("search")
    elif current_step == "product_details":
        if "selected_product" in st.session_state and "selected_color" in st.session_state and "selected_size" in st.session_state:
            show_product_details()
        else:
            st.warning("未完成产品选择")
            go_to_step("search")
    elif current_step == "inventory":
        show_inventory_page()
    elif current_step == "inventory_result":
        if "selected_sku" in st.session_state:
            show_inventory_result(st.session_state.selected_sku)
        else:
            st.warning("未选择SKU")
            go_to_step("inventory")
    elif current_step == "favorites":
        show_favorites_page()
    elif current_step == "cache_management":
        show_cache_management()


def show_home_page():
    """显示首页"""
    st.header("欢迎使用Lululemon查货系统")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🔍 产品搜索")
        st.markdown("搜索Lululemon产品，获取详细信息")
        if st.button("开始搜索", use_container_width=True):
            go_to_step("search")
    
    with col2:
        st.markdown("### 📦 库存查询")
        st.markdown("根据SKU查询各店铺库存情况")
        if st.button("查询库存", use_container_width=True):
            go_to_step("inventory")
    
    with col3:
        st.markdown("### ❤️ 我的收藏")
        st.markdown("管理收藏的产品，批量查询库存")
        if st.button("查看收藏", use_container_width=True):
            go_to_step("favorites")
    
    st.markdown("---")
    
    # 系统说明
    st.markdown("### 📋 系统功能说明")
    st.markdown("""
    - **产品搜索**: 输入产品型号搜索，获取颜色、尺码选项，确定SKU
    - **库存查询**: 根据SKU查询首尔、釜山地区各店铺库存情况
    - **收藏管理**: 收藏喜欢的产品，支持批量库存查询和分析
    - **数据分析**: 库存统计分析，价格计算，购买决策支持
    """)


def show_search_page():
    """显示搜索页面"""
    st.header("🔍 产品搜索")
    
    # 搜索输入
    search_query = st.text_input("请输入产品型号或关键词", placeholder="例如: soft jersey, align pants")
    
    if st.button("搜索产品", use_container_width=True):
        if search_query:
            # 创建进度条和状态容器
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 更新状态
            status_text.text("正在检查缓存...")
            progress_bar.progress(10)
            
            # 首先尝试从内存缓存加载
            products = get_cached_product_search(search_query)
            
            if products:
                # 使用内存缓存数据
                status_text.text("从内存缓存加载数据...")
                progress_bar.progress(50)
                
                status_text.text("缓存数据加载完成！")
                progress_bar.progress(100)
                
                # 清除进度条和状态
                time.sleep(0.5)
                progress_bar.empty()
                status_text.empty()
                
                st.success(f"从缓存找到 {len(products)} 个产品")
            else:
                # 缓存不存在，进行在线搜索
                status_text.text("正在连接服务器...")
                progress_bar.progress(20)
                
                # 搜索产品
                status_text.text("正在搜索产品...")
                progress_bar.progress(40)
                
                products = search_lululemon_products(search_query)
                
                # 更新进度
                status_text.text("正在处理搜索结果...")
                progress_bar.progress(70)
                
                if products:
                    # 保存到缓存
                    status_text.text("正在保存到缓存...")
                    progress_bar.progress(85)
                    
                    cache_data = {
                        'search_results': products,
                        'cached_at': datetime.now().isoformat(),
                        'query': search_query
                    }
                    save_to_cache(search_query, cache_data)
                    
                    # 完成搜索
                    status_text.text("搜索完成！")
                    progress_bar.progress(100)
                    
                    # 清除进度条和状态
                    time.sleep(0.5)
                    progress_bar.empty()
                    status_text.empty()
                    
                    st.success(f"找到 {len(products)} 个产品")
                else:
                    # 清除进度条和状态
                    progress_bar.empty()
                    status_text.empty()
                    st.warning("未找到相关产品")
                    return
            
            if products:
                # 保存搜索结果到session_state
                st.session_state.search_results = products
                st.session_state.search_query = search_query
                st.rerun()
            st.warning("请输入搜索关键词")
    
    # 显示搜索结果（如果存在）
    if "search_results" in st.session_state and st.session_state.search_results:
        st.markdown("### 搜索结果")
        
        for i, product in enumerate(st.session_state.search_results):
            # 构建产品标题，优先显示英文名称，如果没有则显示韩文名称
            if 'english_name' in product and product['english_name']:
                title = f"{i+1}. {product['english_name']}"
            else:
                title = f"{i+1}. {product['korean_name']}"
            
            with st.expander(title):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.markdown(f"**产品ID**: {product['product_id']}")
                    st.markdown(f"**价格**: {format_price_krw(product['product_price'])}")
                    st.markdown(f"**分类**: {product['category_unified']}")
                    if 'english_name' in product and product['english_name']:
                        st.markdown(f"**英文名称**: {product['english_name']}")
                
                with col2:
                    if st.button(f"选择此产品", key=f"select_product_from_search_{i}"):
                        st.session_state.selected_product = product
                        # 检查是否有缓存的产品详情
                        product_url = product['product_url']
                        cached_details = load_from_cache(f"product_details_{product_url}")
                        
                        if cached_details and 'product_details' in cached_details:
                            # 使用缓存的产品详情
                            st.session_state.product_details = cached_details['product_details']
                            st.success("产品详情已从缓存加载")
                        else:
                            # 获取产品详细信息并缓存
                            with st.spinner("正在获取产品详细信息..."):
                                details = get_product_details(product['product_url'])
                            if details:
                                st.session_state.product_details = details
                                # 保存到缓存
                                cache_data = {
                                    'product_details': details,
                                    'cached_at': datetime.now().isoformat(),
                                    'product_url': product_url
                                }
                                save_to_cache(f"product_details_{product_url}", cache_data)
                        go_to_step("color_selection")


def show_product_detail(product):
    """显示产品详情页面"""
    st.header(f"产品详情: {product['korean_name']}")
    
    # 返回按钮
    if st.button("← 返回搜索结果"):
        del st.session_state.selected_product
        go_to_step("search")
    
    # 获取产品详细信息
    product_url = product['product_url']
    cached_details = load_from_cache(f"product_details_{product_url}")
    
    if cached_details and 'product_details' in cached_details:
        # 使用缓存的产品详情
        details = cached_details['product_details']
        st.success("产品详情已从缓存加载")
    else:
        # 获取产品详细信息并缓存
        with st.spinner("正在获取产品详细信息..."):
            details = get_product_details(product['product_url'])
        if details:
            # 保存到缓存
            cache_data = {
                'product_details': details,
                'cached_at': datetime.now().isoformat(),
                'product_url': product_url
            }
            save_to_cache(f"product_details_{product_url}", cache_data)
    
    if details:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # 显示产品基本信息
            st.markdown("### 基本信息")
            st.markdown(f"**产品名称 (韩文)**: {product['korean_name']}")
            if 'english_name' in product and product['english_name']:
                st.markdown(f"**产品名称 (英文)**: {product['english_name']}")
            st.markdown(f"**产品ID**: {product['product_id']}")
            st.markdown(f"**价格**: {format_price_krw(product['product_price'])}")
            
            # 颜色选择
            if details['color_options']:
                st.markdown("### 颜色选择")
                selected_color = st.selectbox(
                    "选择颜色",
                    [f"{color} ({price})" for color, price in details['color_options']]
                )
                selected_color_name = selected_color.split(' (')[0]
            else:
                selected_color_name = None
                st.warning("未找到颜色选项")
            
            # 尺码选择
            if details['size_options']:
                st.markdown("### 尺码选择")
                selected_size = st.selectbox(
                    "选择尺码",
                    [size_code for size_code, size_text in details['size_options']]
                )
            else:
                selected_size = None
                st.warning("未找到尺码选项")
        
        with col2:
            # 显示SKU信息
            if selected_color_name and selected_size:
                mapping_key = f"{selected_color_name}_{selected_size}"
                
                if mapping_key in details['product_mapping']:
                    product_info = details['product_mapping'][mapping_key]
                    
                    st.markdown("### SKU信息")
                    st.markdown(f"**SKU**: {product_info['sku']}")
                    st.markdown(f"**库存状态**: {product_info['stock_status']}")
                    st.markdown(f"**价格**: {format_price_krw(product_info['price'])}")
                    
                    # 显示产品图片
                    if product_info['image_url']:
                        display_product_image(product_info['image_url'], "产品图片")
                    
                    # 添加到收藏按钮
                    if st.button("❤️ 添加到收藏", use_container_width=True):
                        # 计算人民币价格
                        exchange_rate_info = get_exchange_rate()
                        price_cny = calculate_cny_price(int(product_info['price']), exchange_rate_info)
                        
                        favorite_data = {
                            "product_name": product['korean_name'],
                            "product_name_en": product.get('english_name', ''),
                            "product_id": product['product_id'],
                            "color": selected_color_name,
                            "size": selected_size,
                            "price_krw": int(product_info['price']),
                            "price_cny": price_cny,
                            "sku": product_info['sku'],
                            "image_url": product_info['image_url'],
                            "product_url": product['product_url'],
                            "stock_status": product_info['stock_status']
                        }
                        
                        success, message = add_to_favorites(favorite_data)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                    
                    # 查询库存按钮
                    if st.button("📦 查询库存", use_container_width=True):
                        st.session_state.selected_sku = product_info['sku']
                        go_to_step("inventory_result")
                else:
                    st.warning("未找到对应的SKU信息")
    else:
        st.error("获取产品详情失败")


def show_inventory_page():
    """显示库存查询页面"""
    st.header("📦 库存查询")
    
    # SKU输入
    sku = st.text_input("请输入SKU", placeholder="例如: 144525802")
    
    # 地区选择
    region = st.selectbox("选择查询地区", ["1", "2"], format_func=lambda x: "首尔地区" if x == "1" else "釜山地区")
    
    if st.button("查询库存", use_container_width=True):
        if sku:
            # 首先尝试从缓存获取库存数据
            cached_stores = get_cached_inventory(sku, region)
            
            if cached_stores:
                st.success("从缓存加载库存数据")
                stores = cached_stores
            else:
                with st.spinner("正在查询库存..."):
                    stores = query_stock_by_sku(sku, region)
                    # 保存到缓存
                    if stores:
                        save_inventory_cache(sku, region, stores)
                
                if stores:
                    st.success(f"找到 {len(stores)} 个店铺")
                    
                    # 显示库存统计
                    stats = calculate_enhanced_inventory_stats(stores)
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("总店铺数", stats['total_stores'])
                    with col2:
                        st.metric("有库存店铺", stats['in_stock_stores'])
                    with col3:
                        st.metric("总库存量", stats['total_stock'])
                    with col4:
                        st.metric("库存率", f"{stats['availability_rate']}%")
                    
                    # 显示店铺列表
                    st.markdown("### 店铺库存详情")
                    for i, store in enumerate(stores):
                        with st.expander(f"{get_stock_status_color(store['status'])} {store['store_name']} - {store['status']}"):
                            col1, col2 = st.columns([1, 2])
                            
                            with col1:
                                st.markdown(f"**库存数量**: {store['stock']}件")
                                st.markdown(f"**区域**: {store['region']}")
                            
                            with col2:
                                st.markdown(f"**地址**: {store['address']}")
                else:
                    st.warning("未找到库存信息")
        else:
            st.warning("请输入SKU")
    
    # 如果选择了SKU，显示库存结果
    if "selected_sku" in st.session_state:
        show_inventory_result(st.session_state.selected_sku)


def show_inventory_result(sku):
    """显示库存查询结果"""
    st.header(f"库存查询结果: SKU {sku}")
    
    # 返回按钮区域
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # 返回库存查询页面按钮
        if st.button("← 返回库存查询", use_container_width=True):
            del st.session_state.selected_sku
            go_to_step("inventory")
    
    with col2:
        # 返回产品详情页按钮（如果是从产品详情页跳转过来的）
        if "selected_product" in st.session_state:
            if st.button("← 返回产品详情", use_container_width=True):
                del st.session_state.selected_sku
                go_to_step("product_detail")
    
    # 地区选择
    region = st.selectbox("选择查询地区", ["1", "2"], format_func=lambda x: "首尔地区" if x == "1" else "釜山地区")
    
    if st.button("重新查询", use_container_width=True):
        with st.spinner("正在查询库存..."):
            stores = query_stock_by_sku(sku, region)
            
            if stores:
                st.success(f"找到 {len(stores)} 个店铺")
                
                # 显示库存统计
                stats = calculate_enhanced_inventory_stats(stores)
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("总店铺数", stats['total_stores'])
                with col2:
                    st.metric("有库存店铺", stats['in_stock_stores'])
                with col3:
                    st.metric("总库存量", stats['total_stock'])
                with col4:
                    st.metric("库存率", f"{stats['availability_rate']}%")
                
                # 显示店铺列表
                st.markdown("### 店铺库存详情")
                for i, store in enumerate(stores):
                    with st.expander(f"{get_stock_status_color(store['status'])} {store['store_name']} - {store['status']}"):
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            st.markdown(f"**库存数量**: {store['stock']}件")
                            st.markdown(f"**区域**: {store['region']}")
                        
                        with col2:
                            st.markdown(f"**地址**: {store['address']}")
            else:
                st.warning("未找到库存信息")


def show_favorites_page():
    """显示收藏页面"""
    st.header("❤️ 我的收藏")
    
    # 初始化选中状态
    if "selected_favorites" not in st.session_state:
        st.session_state.selected_favorites = set()
    if "show_calculation_config" not in st.session_state:
        st.session_state.show_calculation_config = False
    if "selected_for_calculation" not in st.session_state:
        st.session_state.selected_for_calculation = []
    if "calculation_result" not in st.session_state:
        st.session_state.calculation_result = None
    
    # 加载收藏
    favorites = load_favorites()
    
    if favorites:
        st.success(f"共有 {len(favorites)} 个收藏产品")
        
        # 批量操作按钮
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
        
        with col1:
            if st.button("📦 批量查询库存", use_container_width=True):
                # 获取选中的产品
                selected_indices = st.session_state.selected_favorites
                selected_products = [favorites[i] for i in selected_indices if i < len(favorites)]
                
                if not selected_products:
                    st.warning("请先选择要查询库存的产品")
                else:
                    with st.spinner("正在批量查询库存..."):
                        # 查询库存并更新收藏列表
                        updated_products = batch_check_favorites_inventory(selected_products)
                        
                        # 将查询结果更新到原始收藏列表中
                        selected_indices_list = list(selected_indices)
                        for i, updated_product in enumerate(updated_products):
                            if i < len(selected_indices_list):
                                original_index = selected_indices_list[i]
                                if original_index < len(favorites):
                                    # 更新库存信息到原始收藏列表
                                    favorites[original_index]['inventory_stores'] = updated_product.get('inventory_stores', [])
                                    favorites[original_index]['total_stock'] = updated_product.get('total_stock', 0)
                                    favorites[original_index]['in_stock_stores'] = updated_product.get('in_stock_stores', 0)
                        
                        st.success("库存查询完成")
                        # 查询完成后自动弹出数据分析窗口
                        st.session_state.show_analysis_modal = True
                        st.session_state.analysis_products = updated_products
                        st.rerun()
        
        with col2:
            if st.button("📊 深度分析", use_container_width=True):
                # 获取选中的产品
                selected_indices = st.session_state.selected_favorites
                selected_products = [favorites[i] for i in selected_indices if i < len(favorites)]
                
                if not selected_products:
                    st.warning("请先选择要分析的产品")
                else:
                    st.session_state.show_analysis_modal = True
                    st.session_state.analysis_products = selected_products
                    st.rerun()
        
        with col3:
            if st.button("💰 试算", use_container_width=True):
                selected_indices = st.session_state.selected_favorites
                selected_products = [favorites[i] for i in selected_indices if i < len(favorites)]
                
                if not selected_products:
                    st.warning("请先选择要试算的产品")
                else:
                    st.session_state.show_calculation_config = True
                    st.session_state.selected_for_calculation = selected_products
                    st.session_state.calculation_result = None
                    st.rerun()
        
        with col4:
            if st.button("🗑️ 清空收藏", use_container_width=True):
                success, message = clear_favorites()
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        
        with col5:
            if st.button("🔄 全选/取消", use_container_width=True):
                if len(st.session_state.selected_favorites) == len(favorites):
                    st.session_state.selected_favorites = set()
                else:
                    st.session_state.selected_favorites = set(range(len(favorites)))
                st.rerun()
        
        # 显示试算配置窗口
        if st.session_state.show_calculation_config:
            show_calculation_config_window(st.session_state.selected_for_calculation)
            return
        
        # 显示试算结果
        if st.session_state.calculation_result:
            with st.expander("💰 试算结果", expanded=True):
                col_close, _ = st.columns([1, 3])
                with col_close:
                    if st.button("✕ 关闭试算", key="close_calculation_result"):
                        st.session_state.calculation_result = None
                        st.session_state.selected_for_calculation = []
                        st.rerun()
                
                display_calculation_results(
                    st.session_state.selected_for_calculation,
                    st.session_state.calculation_result
                )
        
        # 显示收藏列表
        for i, favorite in enumerate(favorites):
            # 使用5列布局，第一列为复选框
            col1, col2, col3, col4, col5 = st.columns([1, 3, 3, 1, 1])
            
            with col1:
                # 复选框 - 管理选中状态
                is_selected = i in st.session_state.selected_favorites
                new_selected = st.checkbox(
                    "选择",
                    value=is_selected,
                    key=f"fav_checkbox_{i}",
                    label_visibility="collapsed"
                )
                # 如果复选框状态发生变化，更新session_state
                if new_selected != is_selected:
                    if new_selected:
                        st.session_state.selected_favorites.add(i)
                    else:
                        st.session_state.selected_favorites.discard(i)
                    st.rerun()
            
            with col2:
                # 产品信息
                display_name = favorite.get('product_name_en') or favorite.get('product_name', 'Unknown')
                st.markdown(f"**{display_name}**")
                st.markdown(f"SKU: {favorite['sku']}")
                st.markdown(f"价格: {format_price_krw(favorite['price_krw'])}")
                if favorite.get('price_cny'):
                    st.markdown(f"人民币: {format_price_cny(favorite['price_cny'])}")
            
            with col3:
                # 库存信息
                if favorite.get('inventory_stores'):
                    st.markdown(f"**总库存**: {favorite['total_stock']}件")
                    st.markdown(f"**有库存店铺**: {favorite['in_stock_stores']}个")
                else:
                    st.markdown("**库存**: 未查询")
            
            with col4:
                # 产品图片
                if favorite.get('image_url'):
                    display_product_image(favorite['image_url'], "产品图片")
            
            with col5:
                # 删除按钮
                if st.button(f"删除", key=f"delete_{i}"):
                    success, message = remove_from_favorites(i)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
            
            # 显示库存详情（可折叠）
            if favorite.get('inventory_stores'):
                with st.expander(f"查看 {display_name} 库存详情", expanded=False):
                    for store in favorite['inventory_stores']:
                        st.markdown(f"- {get_stock_status_color(store['status'])} {store['store_name']}: {store['stock']}件")
    else:
        st.info("暂无收藏产品")
        st.markdown("### 如何添加收藏？")
        st.markdown("1. 在'产品搜索'页面搜索产品")
        st.markdown("2. 选择颜色和尺码")
        st.markdown("3. 点击'添加到收藏'按钮")
    
    # 显示数据分析弹窗
    if st.session_state.get('show_analysis_modal', False):
        st.markdown("---")
        show_analysis_modal(st.session_state.get('analysis_products', []))


def show_analysis_modal(selected_favorites):
    """显示数据分析弹窗 - 只对选中的产品进行分析"""
    st.header("📊 产品库存深度分析")
    
    # 关闭按钮
    if st.button("❌ 关闭分析", use_container_width=True):
        st.session_state.show_analysis_modal = False
        st.rerun()
    
    if not selected_favorites:
        st.info("📝 未选择产品，无法进行库存分析")
        return
    
    # 批量查询库存
    with st.spinner("🔄 正在查询库存数据..."):
        selected_favorites = batch_check_favorites_inventory(selected_favorites)
    
    # 构建库存矩阵用于深度分析
    inventory_matrix = {}
    for favorite in selected_favorites:
        if favorite.get('inventory_stores'):
            for store in favorite['inventory_stores']:
                store_name = store['store_name']
                if store_name not in inventory_matrix:
                    inventory_matrix[store_name] = {}
                
                # 构建产品键值，优先使用英文名称
                product_name = favorite.get('product_name_en') or favorite.get('product_name', '')
                product_key = f"{product_name} {favorite.get('color', '')} {favorite.get('size', '')}"
                inventory_matrix[store_name][product_key] = store['stock']
    
    # 计算增强版库存统计
    enhanced_stats = calculate_enhanced_inventory_stats_combined(inventory_matrix)
    
    # 库存深度分析概览
    st.markdown("### 📈 库存深度分析概览")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("分析产品数", len(selected_favorites))
    with col2:
        st.metric("分析店铺数", len(inventory_matrix))
    with col3:
        total_stock = sum(favorite.get('total_stock', 0) for favorite in selected_favorites)
        st.metric("总库存量", f"{total_stock}件")
    with col4:
        in_stock_products = len([f for f in selected_favorites if f.get('total_stock', 0) > 0])
        availability_rate = round(in_stock_products / len(selected_favorites) * 100, 1) if selected_favorites else 0
        st.metric("库存可用率", f"{availability_rate}%")
    
    # 库存状态分布
    st.markdown("### 📊 库存状态分布")
    if enhanced_stats.get('stock_status'):
        stock_status = enhanced_stats['stock_status']
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("✅ 高库存店铺", 
                     f"{stock_status['高库存店铺']['count']}家",
                     f"{stock_status['高库存店铺']['percentage']}%")
        with col2:
            st.metric("⚠️ 低库存店铺", 
                     f"{stock_status['低库存店铺']['count']}家",
                     f"{stock_status['低库存店铺']['percentage']}%")
        with col3:
            st.metric("❌ 无库存店铺", 
                     f"{stock_status['无库存店铺']['count']}家",
                     f"{stock_status['无库存店铺']['percentage']}%")
    
    # 区域库存热力图
    st.markdown("### 🗺️ 区域库存分布")
    if enhanced_stats.get('region_heatmap'):
        region_heatmap = enhanced_stats['region_heatmap']
        
        # 显示区域统计表格
        region_data = []
        for region, stats in region_heatmap.items():
            region_data.append({
                '区域': region,
                '店铺数量': stats['count'],
                '占比': f"{stats['percentage']}%",
                '总库存': stats['inventory'],
                '有库存店铺': stats['in_stock_stores']
            })
        
        df_region = pd.DataFrame(region_data)
        st.dataframe(df_region, use_container_width=True)
        
        # 区域库存可视化
        if len(region_data) > 1:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            # 库存量分布饼图
            regions = [item['区域'] for item in region_data]
            stocks = [item['总库存'] for item in region_data]
            ax1.pie(stocks, labels=regions, autopct='%1.1f%%', startangle=90)
            ax1.set_title('各区域库存分布')
            
            # 店铺数量柱状图
            ax2.bar(regions, [item['店铺数量'] for item in region_data])
            ax2.set_title('各区域店铺分布')
            ax2.set_ylabel('店铺数量')
            plt.xticks(rotation=45)
            
            plt.tight_layout()
            st.pyplot(fig)
    
    # 产品深度库存分析
    st.markdown("### 📦 产品库存深度分析")
    product_depth_stats = calculate_product_depth_stats_by_region(selected_favorites, inventory_matrix)
    
    for product_key, stats in product_depth_stats.items():
        with st.expander(f"📋 {product_key} 库存分析", expanded=False):
            # 基础统计
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📦 总库存", f"{stats['total_inventory']}件")
            with col2:
                st.metric("🏪 有库存店铺", f"{stats['stores_with_stock']}家")
            
            # 详细区域分布
            st.write("📍 区域分布:")
            for region, region_data in stats['region_distribution'].items():
                if region_data['total'] > 0:
                    # 显示区域汇总
                    st.write(f"**{region}**: {region_data['total']}件")
                    
                    # 显示具体店铺分布（缩进显示）
                    for store_info in region_data['stores']:
                        st.write(f"  - {store_info['store_name']}: {store_info['stock']}件")
    
    
    # 库存预警分析
    st.markdown("### ⚠️ 库存预警分析")
    
    # 低库存预警
    low_stock_items = [f for f in selected_favorites if f.get('total_stock', 0) < 5 and f.get('total_stock', 0) > 0]
    no_stock_items = [f for f in selected_favorites if f.get('total_stock', 0) == 0]
    
    if low_stock_items or no_stock_items:
        col1, col2 = st.columns(2)
        
        with col1:
            if low_stock_items:
                st.warning(f"⚠️ 发现 {len(low_stock_items)} 个产品库存不足（<5件）")
                for item in low_stock_items[:3]:  # 只显示前3个
                    # 构建产品显示名称，优先显示英文名称
                    product_name = item.get('product_name_en') or item.get('product_name', '')
                    st.write(f"- {product_name} {item.get('color', '')} {item.get('size', '')}: {item.get('total_stock', 0)}件")
        
        with col2:
            if no_stock_items:
                st.error(f"❌ 发现 {len(no_stock_items)} 个产品无库存")
                for item in no_stock_items[:3]:  # 只显示前3个
                    # 构建产品显示名称，优先显示英文名称
                    product_name = item.get('product_name_en') or item.get('product_name', '')
                    st.write(f"- {product_name} {item.get('color', '')} {item.get('size', '')}")
    else:
        st.success("✅ 所有产品库存充足")
    
    # 购买建议
    st.markdown("### 💡 购买建议")
    
    # 基于库存状态给出建议
    if no_stock_items:
        st.info("📝 无库存产品建议：考虑寻找替代产品或等待补货")
    
    if low_stock_items:
        st.info("📝 低库存产品建议：建议尽快购买，避免缺货")
    
    # 库存充足的产品
    sufficient_stock_items = [f for f in selected_favorites if f.get('total_stock', 0) >= 5]
    if sufficient_stock_items:
        st.info("📝 库存充足产品建议：可以按计划购买，库存充足")


def show_color_selection():
    """显示颜色选择页面 - 左侧布局风格"""
    product = st.session_state.selected_product
    
    # 页面标题
    st.markdown("## 颜色选择")
    
    # 调试模式开关
    debug_mode = st.checkbox("调试模式", value=st.session_state.get('debug_mode', False))
    st.session_state.debug_mode = debug_mode
    
    # 返回按钮
    if st.button("← 返回产品选择", use_container_width=True):
        go_back()
    
    # 使用已经获取的产品详细信息
    details = st.session_state.get('product_details')
    
    if details and details['color_options']:
        st.markdown("**请选择颜色:**")
        
        # 调试模式：显示颜色数据
        if debug_mode:
            st.markdown("### 调试信息")
            st.write(f"颜色选项数量: {len(details['color_options'])}")
            if 'color_price_image_data' in details:
                st.write(f"颜色图片数据数量: {len(details['color_price_image_data'])}")
                for i, color_data in enumerate(details['color_price_image_data']):
                    st.write(f"颜色 {i+1}: {color_data['color_name']} - 图片URL: {color_data.get('image_url', 'None')[:50]}...")
            else:
                st.write("未找到颜色图片数据")
        
        # 创建左右两列布局，确保对齐
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 颜色选项列表
            color_options = [f"{color} - {format_price_krw(price)}" for color, price in details['color_options']]
            selected_index = st.radio(
                "选择颜色:",
                options=color_options,
                key="color_selection"
            )
            
            if selected_index:
                # 找到选中的颜色
                for i, (color, price) in enumerate(details['color_options']):
                    if f"{color} - {format_price_krw(price)}" == selected_index:
                        st.session_state.selected_color = color
                        st.session_state.selected_color_price = price
                        st.session_state.product_details = details
                        break
        
        with col2:
            # 颜色预览区域 - 使用Streamlit原生组件
            st.markdown("**颜色预览**")
            
            # 使用Streamlit原生组件显示预览图片，确保正确渲染
            for i, (color, price) in enumerate(details['color_options']):
                # 获取颜色图片
                color_image_url = None
                if 'color_price_image_data' in details:
                    for color_data in details['color_price_image_data']:
                        if color_data['color_name'] == color:
                            color_image_url = color_data.get('image_url', '')
                            break
                
                # 使用精确的间距控制，确保与左侧radio button完美对齐
                if i > 0:
                    # 添加精确的间距，匹配左侧radio button的间距
                    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                
                # 显示颜色预览图片
                if color_image_url and color_image_url.strip() and color_image_url.startswith(('http://', 'https://')):
                    try:
                        st.image(color_image_url, width=60)
                    except Exception as e:
                        # 如果图片加载失败，显示错误信息和占位符
                        st.markdown("📷")
                        # 在开发模式下显示错误信息
                        if st.session_state.get('debug_mode', False):
                            st.error(f"图片加载失败: {str(e)[:50]}...")
                else:
                    st.markdown("📷")
                    # 在开发模式下显示调试信息
                    if st.session_state.get('debug_mode', False):
                        st.info(f"无图片URL: {color_image_url[:30] if color_image_url else 'None'}...")
        
        # 确认按钮
        if st.session_state.get('selected_color'):
            if st.button("确认颜色", use_container_width=True):
                go_to_step("size_selection")
    else:
        if not details:
            st.error("❌ 获取产品详情失败，请重试")
            st.markdown("**可能的原因：**")
            st.markdown("- 网络连接问题")
            st.markdown("- 产品页面暂时无法访问")
            st.markdown("- 请求超时")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 重新获取详情", use_container_width=True):
                    # 清除旧的产品详情，重新获取
                    if 'product_details' in st.session_state:
                        del st.session_state.product_details
                    
                    # 清除缓存并重新获取
                    product_url = product['product_url']
                    cache_file = get_cache_file_path(f"product_details_{product_url}")
                    if os.path.exists(cache_file):
                        os.remove(cache_file)
                    
                    with st.spinner("正在重新获取产品详细信息..."):
                        details = get_product_details(product['product_url'])
                    if details:
                        st.session_state.product_details = details
                        # 保存到缓存
                        cache_data = {
                            'product_details': details,
                            'cached_at': datetime.now().isoformat(),
                            'product_url': product_url
                        }
                        save_to_cache(f"product_details_{product_url}", cache_data)
                        st.rerun()
                    else:
                        st.error("重新获取失败，请稍后重试")
            
            with col2:
                if st.button("← 返回产品选择", use_container_width=True):
                    go_back()
        else:
            st.warning("⚠️ 此产品暂无颜色选项")
            if st.button("← 返回产品选择"):
                go_back()


def show_size_selection():
    """显示尺码选择页面 - 左侧布局风格"""
    product = st.session_state.selected_product
    selected_color = st.session_state.selected_color
    
    # 页面标题
    st.markdown("## 尺码选择")
    
    # 返回按钮
    if st.button("← 返回颜色选择", use_container_width=True):
        go_back()
    
    details = st.session_state.get('product_details')
    
    if details and details['size_options']:
        st.markdown("**请选择尺码:**")
        
        # 尺码选项列表 - 使用单选按钮组
        size_options = [f"{size_code}" for size_code, size_text in details['size_options']]
        selected_size_index = st.radio(
            "选择尺码:",
            options=size_options,
            key="size_selection"
        )
        
        if selected_size_index:
            # 找到选中的尺码
            for size_code, size_text in details['size_options']:
                if size_code == selected_size_index:
                    st.session_state.selected_size = size_code
                    break
        
        # 确认按钮
        if st.session_state.get('selected_size'):
            if st.button("确认尺码", use_container_width=True):
                go_to_step("product_details")
    else:
        if not details:
            st.error("❌ 产品详情数据丢失，请返回重新选择产品")
            if st.button("← 返回产品选择"):
                # 清除所有选择状态
                for key in ['selected_product', 'selected_color', 'selected_size', 'product_details']:
                    if key in st.session_state:
                        del st.session_state[key]
                go_to_step("search")
        else:
            st.warning("⚠️ 此产品暂无尺码选项")
            if st.button("← 返回颜色选择"):
                go_back()


def show_product_details():
    """显示产品详情页面 - 始祖鸟风格"""
    product = st.session_state.selected_product
    selected_color = st.session_state.selected_color
    selected_size = st.session_state.selected_size
    
    # 页面标题
    st.subheader("📋 产品详情")
    
    # 返回按钮
    if st.button("← 返回尺码选择"):
        go_back()
    
    # 显示当前选择的产品信息
    st.info(f"**产品**: {product['korean_name']}")
    st.info(f"**颜色**: {selected_color}")
    st.info(f"**尺码**: {selected_size}")
    
    details = st.session_state.get('product_details')
    
    # 获取SKU信息
    mapping_key = f"{selected_color}_{selected_size}"
    
    if mapping_key in details['product_mapping']:
        product_info = details['product_mapping'][mapping_key]
        
        # 始祖鸟风格的详情展示
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # 基本信息卡片
            st.markdown("### 📋 基本信息")
            st.markdown(f"""
            <div style="
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 20px;
                background-color: #fafafa;
                margin-bottom: 20px;
            ">
                <p><strong>产品名称(韩文):</strong> {product['korean_name']}</p>
                <p><strong>产品名称(英文):</strong> {product.get('english_name', 'N/A')}</p>
                <p><strong>产品ID:</strong> {product['product_id']}</p>
                <p><strong>价格:</strong> {format_price_krw(product['product_price'])}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # SKU信息卡片
            st.markdown("### 🏷️ SKU信息")
            st.markdown(f"""
            <div style="
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 20px;
                background-color: #fafafa;
                margin-bottom: 20px;
            ">
                <p><strong>SKU:</strong> {product_info['sku']}</p>
                <p><strong>库存状态:</strong> {product_info['stock_status']}</p>
                <p><strong>价格:</strong> {format_price_krw(product_info['price'])}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # 显示产品图片
            if product_info['image_url']:
                st.markdown("### 🖼️ 产品图片")
                display_product_image(product_info['image_url'], "产品图片")
        
        # 操作按钮区域
        st.markdown("### 🔧 操作")
        
        col3, col4, col5 = st.columns(3)
        
        with col3:
            # 添加到收藏按钮
            if st.button("❤️ 添加到收藏", use_container_width=True):
                # 计算人民币价格
                exchange_rate_info = get_exchange_rate()
                price_cny = calculate_cny_price(int(product_info['price']), exchange_rate_info)
                
                favorite_data = {
                    "product_name": product['korean_name'],
                    "product_name_en": product.get('english_name', ''),
                    "product_id": product['product_id'],
                    "color": selected_color,
                    "size": selected_size,
                    "price_krw": int(product_info['price']),
                    "price_cny": price_cny,
                    "sku": product_info['sku'],
                    "image_url": product_info['image_url'],
                    "product_url": product['product_url'],
                    "stock_status": product_info['stock_status']
                }
                
                success, message = add_to_favorites(favorite_data)
                if success:
                    st.success(message)
                else:
                    st.error(message)
        
        with col4:
            # 查询库存按钮
            if st.button("📦 查询库存", use_container_width=True):
                st.session_state.selected_sku = product_info['sku']
                go_to_step("inventory_result")
        
        with col5:
            # 复制SKU按钮
            if st.button("📋 复制SKU", use_container_width=True):
                st.write(f"SKU: {product_info['sku']}")
                st.success("SKU已复制到剪贴板")
        
        # 重新选择按钮
        st.markdown("---")
        if st.button("🔄 重新选择产品", use_container_width=True):
            # 清除所有选择状态
            for key in ['selected_product', 'selected_color', 'selected_size', 'product_details']:
                if key in st.session_state:
                    del st.session_state[key]
            go_to_step("search")
    
    else:
        if not details:
            st.error("❌ 产品详情数据丢失，请返回重新选择产品")
            if st.button("← 返回产品选择"):
                # 清除所有选择状态
                for key in ['selected_product', 'selected_color', 'selected_size', 'product_details']:
                    if key in st.session_state:
                        del st.session_state[key]
                go_to_step("search")
        else:
            st.error("❌ 未找到对应的SKU信息")
            st.markdown("**可能的原因：**")
            st.markdown("- 所选颜色和尺码组合不存在")
            st.markdown("- 产品数据不完整")
            st.markdown("- 请尝试选择其他颜色或尺码")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("← 返回尺码选择", use_container_width=True):
                    go_back()
            with col2:
                if st.button("🔄 重新选择产品", use_container_width=True):
                    # 清除所有选择状态
                    for key in ['selected_product', 'selected_color', 'selected_size', 'product_details']:
                        if key in st.session_state:
                            del st.session_state[key]
                    go_to_step("search")


def show_calculation_config_window(selected_products):
    """显示试算配置窗口"""
    st.subheader("💰 试算配置")
    
    # 显示选中的产品清单
    st.write("**选中的产品清单:**")
    for i, product in enumerate(selected_products, 1):
        display_name = product.get('product_name_en') or product.get('product_name', 'Unknown')
        st.write(f"{i}. {display_name} - {product['color']} - {product['size']} - {format_price_krw(product['price_krw'])}")
    
    # 计算原始总价
    total_krw = sum(product['price_krw'] for product in selected_products)
    st.write(f"**原始总价:** {format_price_krw(total_krw)}")
    
    st.divider()
    
    # 商家选择
    st.write("**选择商家优惠:**")
    store_options = ["明洞乐天", "新世界", "韩国电话注册", "乐天/新世界奥莱"]
    selected_store = st.radio("选择商家", store_options, key="store_selection")
    
    # 显示优惠选项
    store_config = DISCOUNT_CONFIG[selected_store]
    st.write(f"*{store_config['description']}*")
    
    selected_discounts = []
    for option in store_config['options']:
        col1, col2 = st.columns([1, 4])
        with col1:
            selected = st.checkbox(option['name'], key=f"discount_{option['name']}_{len(selected_discounts)}")
        with col2:
            with st.expander("ℹ️ 规则说明"):
                st.write(option['rule'])
        
        if selected:
            selected_discounts.append(option)
    
    # 按钮布局
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 开始试算", key="calculate_final"):
            if not selected_discounts:
                st.warning("请至少选择一个优惠项目")
            else:
                # 计算最终结果
                result = calculate_detailed_price(total_krw, selected_discounts)
                st.session_state.calculation_result = result
                st.session_state.show_calculation_config = False
                st.rerun()
    
    with col2:
        if st.button("← 返回收藏列表", key="back_to_favorites"):
            st.session_state.show_calculation_config = False
            st.session_state.selected_for_calculation = []
            st.rerun()


def calculate_detailed_price(total_krw, selected_discounts):
    """详细价格计算"""
    # 计算税前优惠
    pre_tax_discount = 0
    for discount in selected_discounts:
        if discount['type'] == 'pre_tax_percent':
            pre_tax_discount += total_krw * discount['rate']
        elif discount['type'] == 'pre_tax_fixed':
            if total_krw >= discount['threshold']:
                pre_tax_discount += discount['amount']
        elif discount['type'] == 'pre_tax_capped':
            if total_krw >= discount['threshold']:
                discount_amount = total_krw * discount['rate']
                pre_tax_discount += min(discount_amount, discount['cap'])
    
    # 计算税前优惠后价格
    after_pre_tax = total_krw - pre_tax_discount
    
    # 计算退税额
    tax_refund = calculate_tax_refund(after_pre_tax)
    
    # 计算税后价格
    after_tax = after_pre_tax - tax_refund
    
    # 计算税后商品券
    gift_coupon = 0
    for discount in selected_discounts:
        if discount['type'] == 'post_tax_tiered':
            for tier in reversed(discount['tiers']):  # 从高到低检查
                if after_tax >= tier['threshold']:
                    gift_coupon = tier['amount']
                    break
    
    # 计算最终实付
    final_payment = after_tax - gift_coupon
    
    return {
        'total_krw': total_krw,
        'pre_tax_discount': pre_tax_discount,
        'after_pre_tax': after_pre_tax,
        'tax_refund': tax_refund,
        'after_tax': after_tax,
        'gift_coupon': gift_coupon,
        'final_payment': final_payment,
        'selected_discounts': [d['name'] for d in selected_discounts]
    }


def calculate_tax_refund(total_amount):
    """根据韩国退税税率表计算退税额（基于总价）"""
    # 韩国退税税率表（基于总价）
    tax_brackets = [
        (15000, 29999, 1000),
        (30000, 49999, 2000),
        (50000, 74999, 3500),
        (75000, 99999, 5000),
        (100000, 124999, 6000),
        (125000, 149999, 7000),
        (150000, 199999, 10000),
        (200000, 249999, 13000),
        (250000, 299999, 15000),
        (300000, 399999, 20000),
        (400000, 499999, 25000),
        (500000, 599999, 30000),
        (600000, 699999, 35000),
        (700000, 799999, 40000),
        (800000, 899999, 45000),
        (900000, 999999, 50000),
        (1000000, 1249999, 55000),
        (1250000, 1499999, 60000),
        (1500000, 1999999, 70000),
        (2000000, 2499999, 80000),
        (2500000, 2999999, 90000),
        (3000000, 3999999, 100000),
        (4000000, 4999999, 120000),
        (5000000, 5999999, 140000),
        (6000000, 6999999, 170000),
        (7000000, 7999999, 200000),
        (8000000, 8999999, 230000),
        (9000000, 9999999, 260000),
        (10000000, 11499999, 300000),
        (11500000, 12999999, 340000),
        (13000000, 14999999, 380000),
        (15000000, 100000000, 480000)  # 最高退税额
    ]
    
    for min_amount, max_amount, refund in tax_brackets:
        if min_amount <= total_amount <= max_amount:
            return refund
    return 0


def display_calculation_results(selected_products, result):
    """显示试算结果"""
    if not result:
        st.error("试算失败，请重试")
        return
    
    st.subheader("📊 试算结果")
    
    # 显示选中的产品
    st.write("**选中的产品清单:**")
    for i, product in enumerate(selected_products, 1):
        display_name = product.get('product_name_en') or product.get('product_name', 'Unknown')
        st.write(f"{i}. {display_name} - {product['color']} - {product['size']}")
    
    st.divider()
    
    # 计算人民币价格
    exchange_rate_info = get_exchange_rate()
    cny_price = calculate_cny_price(result['final_payment'], exchange_rate_info)
    
    # 显示计算步骤
    st.write("**详细计算过程:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("原始总价", f"{result['total_krw']:,.0f}韩元")
        st.metric("税前优惠", f"-{result['pre_tax_discount']:,.0f}韩元")
        st.metric("优惠后总价", f"{result['after_pre_tax']:,.0f}韩元")
        st.metric("退税额", f"-{result['tax_refund']:,.0f}韩元")
    
    with col2:
        st.metric("税后总价", f"{result['after_tax']:,.0f}韩元")
        if result['gift_coupon'] > 0:
            st.metric("商品券优惠", f"-{result['gift_coupon']:,.0f}韩元")
            st.metric("最终实付",
                      f"{result['final_payment']:,.0f}韩元/{cny_price:,.0f}人民币",
                      f"含{result['gift_coupon']:,.0f}韩元商品券")
        else:
            st.metric("商品券优惠", "0韩元")
            st.metric("最终实付", f"{result['final_payment']:,.0f}韩元/{cny_price:,.0f}人民币")
    
    # 显示使用的优惠
    st.write("**使用的优惠:**")
    for discount in result['selected_discounts']:
        st.write(f"✅ {discount}")


if __name__ == "__main__":
    main()
