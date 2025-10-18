# lululemon_favorites_manager.py
import json
import os
from datetime import datetime
from utils import is_duplicate
from supabase_client import supabase_manager


def get_storage_status():
    """获取当前存储状态信息"""
    try:
        client = supabase_manager.get_client()
        
        # 检查是否使用本地存储
        if hasattr(client, 'load_data'):
            # 本地文件存储
            return {
                "type": "local",
                "name": "本地文件存储",
                "icon": "💾",
                "description": "数据存储在本地文件中",
                "path": "favorites.json"
            }
        else:
            # Supabase存储
            return {
                "type": "supabase", 
                "name": "Supabase云端存储",
                "icon": "☁️",
                "description": "数据存储在Supabase云端数据库中",
                "url": "https://kmsebovqoemcenedwfbi.supabase.co"
            }
    except Exception as e:
        return {
            "type": "unknown",
            "name": "存储状态未知",
            "icon": "❓",
            "description": f"无法确定存储状态: {str(e)}",
            "error": str(e)
        }


def load_favorites():
    """从 Supabase 或本地文件加载所有收藏产品"""
    try:
        client = supabase_manager.get_client()
        
        # 检查是否使用本地存储
        if hasattr(client, 'load_data'):
            # 本地文件存储
            favorites = client.load_data()
            # 按添加时间排序（最新的在前）
            favorites.sort(key=lambda x: x.get('added_time', ''), reverse=True)
            return favorites
        else:
            # Supabase存储
            try:
                # 尝试按 added_time 排序
                response = client.table('lululemon_favorites').select('*').order('added_time', desc=True).execute()
                favorites = response.data if response.data else []
                return favorites
            except Exception as e:
                # 如果 added_time 字段不存在，按 id 排序
                try:
                    response = client.table('lululemon_favorites').select('*').order('id', desc=True).execute()
                    favorites = response.data if response.data else []
                    return favorites
                except Exception as e2:
                    # 如果连 id 排序都不行，直接查询
                    response = client.table('lululemon_favorites').select('*').execute()
                    favorites = response.data if response.data else []
                    return favorites

    except Exception as e:
        print(f"❌❌ 加载收藏失败: {e}")
        return []


def add_to_favorites(product_info):
    """添加产品到收藏（Supabase 或本地文件）"""
    try:
        # 检查是否重复
        existing_favorites = load_favorites()
        if is_duplicate(existing_favorites, product_info):
            return False, "该产品已存在于收藏中"

        # 准备插入数据 - 使用完整的字段结构
        product_data = {
            "product_name": product_info.get("product_name", ""),
            "product_id": product_info.get("product_id", ""),
            "color": product_info.get("color"),
            "size": product_info.get("size"),
            "price_krw": product_info.get("price_krw"),
            "price_cny": product_info.get("price_cny"),
            "sku": product_info.get("sku"),
            "image_url": product_info.get("image_url"),
            "product_url": product_info.get("product_url"),
            "stock_status": product_info.get("stock_status"),
            "product_name_en": product_info.get("product_name_en")
        }
        
        # 移除空值字段
        product_data = {k: v for k, v in product_data.items() if v is not None and v != ""}

        client = supabase_manager.get_client()
        
        # 检查是否使用本地存储
        if hasattr(client, 'load_data'):
            # 本地文件存储
            favorites = client.load_data()
            # 添加ID和时间戳（本地存储需要手动生成）
            product_data['id'] = len(favorites) + 1
            product_data['added_time'] = datetime.now().isoformat()
            favorites.append(product_data)
            
            if client.save_data(favorites):
                return True, "成功添加到收藏"
            else:
                return False, "保存到本地文件失败"
        else:
            # Supabase存储
            response = client.table('lululemon_favorites').insert(product_data).execute()
            if response.data:
                return True, "成功添加到收藏"
            else:
                return False, "添加到数据库失败"

    except Exception as e:
        print(f"❌❌ 添加到收藏失败: {e}")
        return False, f"添加到收藏失败: {str(e)}"


def remove_from_favorites(index):
    """根据索引从收藏中移除产品"""
    try:
        favorites = load_favorites()
        if 0 <= index < len(favorites):
            client = supabase_manager.get_client()
            
            # 检查是否使用本地存储
            if hasattr(client, 'load_data'):
                # 本地文件存储
                favorites.pop(index)
                if client.save_data(favorites):
                    return True, f"已从收藏中移除"
                else:
                    return False, "保存到本地文件失败"
            else:
                # Supabase存储
                id_to_remove = favorites[index]['id']
                response = client.table('lululemon_favorites').delete().eq('id', id_to_remove).execute()
                if response.data:
                    return True, f"已从收藏中移除"
                else:
                    return False, "删除失败，未找到对应记录"
        else:
            return False, "索引超出范围"

    except Exception as e:
        print(f"❌❌ 从收藏移除失败: {e}")
        return False, f"数据库错误: {str(e)}"


def clear_favorites():
    """清空收藏表"""
    try:
        client = supabase_manager.get_client()
        
        # 检查是否使用本地存储
        if hasattr(client, 'load_data'):
            # 本地文件存储
            if client.save_data([]):
                return True, "已清空收藏列表"
            else:
                return False, "清空失败"
        else:
            # Supabase存储 - 删除所有记录
            response = client.table('lululemon_favorites').delete().gte('id', 0).execute()
            deleted_count = len(response.data) if response.data else 0
            return True, f"已清空收藏列表，删除了 {deleted_count} 条记录"
    except Exception as e:
        print(f"❌❌ 清空收藏失败: {e}")
        return False, f"清空失败: {str(e)}"


def batch_check_favorites_inventory(favorites, region="1"):
    """批量查询收藏产品的库存（带缓存优化）"""
    try:
        from lululemon_inventory_check import safe_batch_query
        import streamlit as st
        from datetime import datetime, timedelta
        import json
        import os
        
        # 缓存配置
        CACHE_DIR = "cache"
        INVENTORY_CACHE_HOURS = 2
        
        def get_cache_file_path(sku, region):
            """获取库存缓存文件路径"""
            import hashlib
            cache_key = f"inventory_{sku}_{region}"
            query_hash = hashlib.md5(cache_key.encode()).hexdigest()
            return os.path.join(CACHE_DIR, f"inventory_{query_hash}.json")
        
        def is_inventory_cache_valid(cache_file):
            """检查库存缓存是否有效"""
            if not os.path.exists(cache_file):
                return False
            file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            expiry_time = file_time + timedelta(hours=INVENTORY_CACHE_HOURS)
            return datetime.now() < expiry_time
        
        def get_cached_inventory(sku, region):
            """获取缓存的库存数据"""
            cache_file = get_cache_file_path(sku, region)
            if is_inventory_cache_valid(cache_file):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        return data.get('stores', [])
                except Exception as e:
                    print(f"库存缓存加载失败: {e}")
            return None
        
        def save_inventory_cache(sku, region, stores):
            """保存库存数据到缓存"""
            cache_file = get_cache_file_path(sku, region)
            try:
                cache_data = {
                    'stores': stores,
                    'cached_at': datetime.now().isoformat(),
                    'sku': sku,
                    'region': region
                }
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"库存缓存保存失败: {e}")
        
        # 提取所有SKU
        skus = [fav['sku'] for fav in favorites if fav.get('sku')]
        
        if not skus:
            return favorites
        
        # 先检查缓存，只查询未缓存或已过期的SKU
        cached_results = {}
        skus_to_query = []
        
        for sku in skus:
            cached_stores = get_cached_inventory(sku, region)
            if cached_stores:
                cached_results[sku] = cached_stores
            else:
                skus_to_query.append(sku)
        
        # 查询未缓存的SKU
        if skus_to_query:
            print(f"查询 {len(skus_to_query)} 个未缓存的SKU...")
            inventory_results = safe_batch_query(skus_to_query, region)
            
            # 保存新查询的结果到缓存
            for sku, stores in inventory_results.items():
                save_inventory_cache(sku, region, stores)
                cached_results[sku] = stores
        else:
            print("所有SKU都使用缓存数据")
        
        # 为每个收藏产品添加库存信息
        for favorite in favorites:
            sku = favorite.get('sku')
            if sku and sku in cached_results:
                stores = cached_results[sku]
                favorite['inventory_stores'] = stores
                favorite['total_stock'] = sum(s['stock'] for s in stores)
                favorite['in_stock_stores'] = len([s for s in stores if s['stock'] > 0])
            else:
                favorite['inventory_stores'] = []
                favorite['total_stock'] = 0
                favorite['in_stock_stores'] = 0
        
        return favorites
        
    except Exception as e:
        print(f"❌❌ 批量查询库存失败: {e}")
        return favorites


def calculate_favorites_summary(favorites):
    """计算收藏产品汇总信息"""
    if not favorites:
        return {}
    
    total_products = len(favorites)
    total_value_krw = sum(fav.get('price_krw', 0) for fav in favorites)
    total_value_cny = sum(fav.get('price_cny', 0) for fav in favorites)
    
    # 库存统计
    in_stock_products = len([fav for fav in favorites if fav.get('total_stock', 0) > 0])
    low_stock_products = len([fav for fav in favorites if fav.get('total_stock', 0) > 0 and fav.get('total_stock', 0) < 5])
    
    # 按区域统计库存
    region_stats = {}
    for favorite in favorites:
        stores = favorite.get('inventory_stores', [])
        for store in stores:
            region = store.get('region', '未知区域')
            if region not in region_stats:
                region_stats[region] = {'products': set(), 'total_stock': 0}
            region_stats[region]['products'].add(favorite['id'])
            region_stats[region]['total_stock'] += store.get('stock', 0)
    
    # 转换set为count
    for region in region_stats:
        region_stats[region]['product_count'] = len(region_stats[region]['products'])
        del region_stats[region]['products']
    
    return {
        'total_products': total_products,
        'total_value_krw': total_value_krw,
        'total_value_cny': total_value_cny,
        'in_stock_products': in_stock_products,
        'low_stock_products': low_stock_products,
        'availability_rate': round(in_stock_products / total_products * 100, 1) if total_products > 0 else 0,
        'region_stats': region_stats
    }
