import requests
import json
import streamlit as st

# Lululemon店铺信息翻译字典（基于666文件夹中的输入SKU查货.py）
STORE_TRANSLATIONS = {
    # 首尔地区店铺
    "이태원 스토어": {
        "name": "梨泰院店",
        "address": "首尔特别市龙山区梨泰院路200 Zenitas大厦1-2层"
    },
    "신세계백화점 본점 스토어": {
        "name": "新世界百货总店",
        "address": "首尔特别市中区小公路63新世界百货总店新馆4层"
    },
    "명동 타임워크 스토어": {
        "name": "明洞Timeworks店",
        "address": "首尔特别市中区南大门路78 Timeworks大厦1-2层"
    },
    "롯데백화점 명동 스토어": {
        "name": "乐天百货明洞店",
        "address": "首尔特别市中区南大门路81乐天百货总店3层"
    },
    "청담 스토어": {
        "name": "清潭店",
        "address": "首尔特别市江南区宣陵路835"
    },
    "신세계백화점 강남 스토어": {
        "name": "新世界百货江南店",
        "address": "首尔特别市瑞草区新盘浦路176新世界百货江南店5层"
    },
    "더현대 서울 스토어": {
        "name": "现代百货首尔店",
        "address": "首尔特别市永登浦区汝矣岛路108现代百货首尔店3层"
    },
    "현대백화점 무역센터 스토어": {
        "name": "现代百货贸易中心店",
        "address": "首尔特别市江南区德黑兰路517现代百货贸易中心店5层"
    },
    "파르나스몰 스토어": {
        "name": "Parnas Mall店",
        "address": "首尔特别市江南区德黑兰路521 Parnas Mall地下1层"
    },
    "롯데월드몰 스토어": {
        "name": "乐天世界购物中心店",
        "address": "首尔特别市松坡区奥林匹克路300乐天世界购物中心1层"
    },
    "현대백화점 목동 스토어": {
        "name": "现代百货木洞店",
        "address": "首尔特别市阳川区木洞洞路257现代百货木洞店别馆1层"
    },

    # 京畿道店铺（归类到首尔）
    "스타필드 고양 스토어": {
        "name": "Starfield高阳店",
        "address": "京畿道高阳市德阳区高阳路1955 Starfield高阳1层"
    },
    "스타필드 하남 스토어": {
        "name": "Starfield河南店",
        "address": "京畿道河南市弥沙大路750 Starfield河南L2层"
    },
    "현대백화점 판교 스토어": {
        "name": "现代百货板桥店",
        "address": "京畿道城南市盆唐区板桥站路146街20现代百货板桥店3层"
    },
    "신세계 사우스시티 스토어": {
        "name": "新世界South City店",
        "address": "京畿道龙仁市水枝区圃隐大路536新世界South City 2层"
    },
    "룰루레몬 타임빌라스 수원 스토어": {
        "name": "Lululemon Time Villa水原店",
        "address": "京畿道水原市劝善区细花路134 Time Villa水原2层"
    },
    "여주 프리미엄 아울렛 스토어": {
        "name": "骊州Premium Outlet店",
        "address": "京畿道骊州市名品路360新世界骊州Premium Outlet 310号"
    },

    # 釜山地区店铺
    "롯데백화점 부산본점 스토어": {
        "name": "乐天百货釜山总店",
        "address": "釜山广域市釜山镇区伽倻大路772乐天百货釜山总店3层"
    },
    "신세계 센텀시티 스토어": {
        "name": "新世界Centum City店",
        "address": "釜山广域市海云台区Centum4路15 Centum City Mall 1层"
    },
    
    # 大邱地区店铺
    "대구신세계 Art & Science 스토어": {
        "name": "大邱新世界 Art & Science 店",
        "address": "大邱广域市中区中央大路458新世界百货大邱店5层"
    },
    "신세계백화점 대구 스토어": {
        "name": "新世界百货大邱店",
        "address": "大邱广域市中区中央大路458新世界百货大邱店3层"
    },
    
    # 仁川地区店铺
    "인천신세계 스토어": {
        "name": "仁川新世界店",
        "address": "仁川广域市南洞区인하로55 新世界百货仁川店3层"
    },
    
    # 光州地区店铺
    "광주신세계 스토어": {
        "name": "光州新世界店",
        "address": "光州广域市东区금남로5 新世界百货光州店3层"
    },
    
    # 大田地区店铺
    "대전신세계 스토어": {
        "name": "大田新世界店",
        "address": "大田广域市中区큰길5 新世界百货大田店3层"
    }
}

# 地区坐标配置
REGION_COORDS = {
    "1": {"lat": "37.56521290000001", "long": "126.9773517"},  # 首尔
    "2": {"lat": "35.1731121", "long": "129.0714122"}  # 釜山
}

# 店铺区域映射
STORE_REGION_MAPPING = {
    # 首尔城区
    "梨泰院店": "首尔城区",
    "新世界百货总店": "首尔城区", 
    "明洞Timeworks店": "首尔城区",
    "乐天百货明洞店": "首尔城区",
    "清潭店": "首尔城区",
    "新世界百货江南店": "首尔城区",
    "现代百货首尔店": "首尔城区",
    "现代百货贸易中心店": "首尔城区",
    "Parnas Mall店": "首尔城区",
    "乐天世界购物中心店": "首尔城区",
    "现代百货木洞店": "首尔城区",
    
    # 京畿道地区（归类到首尔）
    "Starfield高阳店": "京畿道地区",
    "Starfield河南店": "京畿道地区",
    "现代百货板桥店": "京畿道地区",
    "新世界South City店": "京畿道地区",
    "Lululemon Time Villa水原店": "京畿道地区",
    "骊州Premium Outlet店": "京畿道地区",
    
    # 釜山
    "乐天百货釜山总店": "釜山",
    "新世界Centum City店": "釜山",
    
    # 大邱
    "大邱新世界 Art & Science 店": "大邱",
    "新世界百货大邱店": "大邱",
    
    # 仁川
    "仁川新世界店": "仁川",
    
    # 光州
    "光州新世界店": "光州",
    
    # 大田
    "大田新世界店": "大田"
}


def translate_store_name(store_name, original_address=""):
    """翻译店铺信息，没有翻译则返回原韩文"""
    if store_name in STORE_TRANSLATIONS:
        return (
            STORE_TRANSLATIONS[store_name]["name"],
            STORE_TRANSLATIONS[store_name]["address"]
        )
    return store_name, original_address


def get_store_region(store_name):
    """获取店铺所属区域"""
    return STORE_REGION_MAPPING.get(store_name, "未知区域")


def map_region_to_key(region_name):
    """将区域名称映射到坐标键"""
    if region_name in ["首尔城区", "京畿道地区"]:
        return "1"  # 首尔
    elif region_name == "釜山":
        return "2"  # 釜山
    else:
        return "1"  # 默认首尔


def get_stock_status(stock_value, message):
    """获取库存状态"""
    if message == "onlyfewleft":
        return "少量库存"
    elif stock_value > 0:
        return "有库存"
    else:
        return "无库存"


def query_stock_by_sku(sku, region="1"):
    """
    根据SKU查询库存
    基于666文件夹中的输入SKU查货.py
    """
    try:
        # 构建请求URL
        base_url = "https://www.lululemon.co.kr/on/demandware.store/Sites-KR-Site/ko_KR/InStores-FindStores"
        params = {
            "lat": REGION_COORDS[region]["lat"],
            "long": REGION_COORDS[region]["long"],
            "pid": sku
        }

        # 发送请求
        payload = {
            'api_key': '420b6b6ad161ba091d728cba109b8df5',
            'url': f"{base_url}?lat={params['lat']}&long={params['long']}&pid={params['pid']}"
        }
        
        r = requests.get('https://api.scraperapi.com/', params=payload, timeout=10)
        r.raise_for_status()
        data = json.loads(r.text)

        # 解析响应
        if not data.get("stores"):
            return []

        # 处理店铺信息
        stores = []
        for store in data["stores"]:
            name, address = translate_store_name(store["name"], store["address1"])
            stock = store["supply"]["value"]
            status = get_stock_status(stock, store["supply"]["message"])
            region = get_store_region(name)
            
            stores.append({
                "store_name": name,
                "address": address,
                "stock": stock,
                "status": status,
                "region": region,
                "original_name": store["name"]
            })

        return stores

    except Exception as e:
        print(f"查询库存失败: {e}")
        return []


def safe_batch_query(skus, region="1"):
    """批量安全查询库存"""
    results = {}
    for sku in skus:
        try:
            stores = query_stock_by_sku(sku, region)
            results[sku] = stores
        except Exception as e:
            print(f"查询SKU {sku} 失败: {e}")
            results[sku] = []
    return results


def calculate_enhanced_inventory_stats(stores_data):
    """计算增强的库存统计信息"""
    if not stores_data:
        return {}
    
    total_stores = len(stores_data)
    in_stock_stores = len([s for s in stores_data if s['stock'] > 0])
    low_stock_stores = len([s for s in stores_data if s['status'] == '少量库存'])
    total_stock = sum(s['stock'] for s in stores_data)
    
    # 按区域统计
    region_stats = {}
    for store in stores_data:
        region = store['region']
        if region not in region_stats:
            region_stats[region] = {'stores': 0, 'stock': 0, 'in_stock_stores': 0}
        
        region_stats[region]['stores'] += 1
        region_stats[region]['stock'] += store['stock']
        if store['stock'] > 0:
            region_stats[region]['in_stock_stores'] += 1
    
    return {
        'total_stores': total_stores,
        'in_stock_stores': in_stock_stores,
        'low_stock_stores': low_stock_stores,
        'total_stock': total_stock,
        'availability_rate': round(in_stock_stores / total_stores * 100, 1) if total_stores > 0 else 0,
        'region_stats': region_stats
    }


def calculate_product_depth_stats(stores_data):
    """计算产品深度统计"""
    if not stores_data:
        return {}
    
    # 按库存数量分组
    stock_distribution = {}
    for store in stores_data:
        stock = store['stock']
        if stock not in stock_distribution:
            stock_distribution[stock] = 0
        stock_distribution[stock] += 1
    
    # 计算平均库存
    total_stock = sum(s['stock'] for s in stores_data)
    avg_stock = total_stock / len(stores_data) if stores_data else 0
    
    return {
        'stock_distribution': stock_distribution,
        'avg_stock': round(avg_stock, 1),
        'max_stock': max(s['stock'] for s in stores_data) if stores_data else 0,
        'min_stock': min(s['stock'] for s in stores_data) if stores_data else 0
    }


def calculate_key_store_analysis(stores_data):
    """计算关键店铺分析"""
    if not stores_data:
        return {}
    
    # 按店铺类型分析
    store_types = {}
    for store in stores_data:
        store_name = store['store_name']
        if '百货' in store_name or '백화점' in store['original_name']:
            store_type = '百货店'
        elif 'Premium' in store_name or '프리미엄' in store['original_name']:
            store_type = '奥特莱斯'
        elif 'Mall' in store_name or '몰' in store['original_name']:
            store_type = '购物中心'
        else:
            store_type = '直营店'
        
        if store_type not in store_types:
            store_types[store_type] = {'stores': 0, 'total_stock': 0, 'in_stock_stores': 0}
        
        store_types[store_type]['stores'] += 1
        store_types[store_type]['total_stock'] += store['stock']
        if store['stock'] > 0:
            store_types[store_type]['in_stock_stores'] += 1
    
    return store_types


def calculate_stock_status_distribution(stores_data):
    """计算库存状态分布"""
    if not stores_data:
        return {
            "高库存店铺": {"count": 0, "percentage": 0},
            "低库存店铺": {"count": 0, "percentage": 0},
            "无库存店铺": {"count": 0, "percentage": 0}
        }
    
    total_stores = len(stores_data)
    high_stock_count = 0
    low_stock_count = 0
    no_stock_count = 0
    
    for store in stores_data:
        stock = store['stock']
        if stock > 2:
            high_stock_count += 1
        elif stock > 0:
            low_stock_count += 1
        else:
            no_stock_count += 1
    
    return {
        "高库存店铺": {
            "count": high_stock_count,
            "percentage": round(high_stock_count / total_stores * 100, 2) if total_stores > 0 else 0
        },
        "低库存店铺": {
            "count": low_stock_count,
            "percentage": round(low_stock_count / total_stores * 100, 2) if total_stores > 0 else 0
        },
        "无库存店铺": {
            "count": no_stock_count,
            "percentage": round(no_stock_count / total_stores * 100, 2) if total_stores > 0 else 0
        }
    }


def calculate_region_heatmap(stores_data):
    """计算区域库存热力图数据"""
    if not stores_data:
        return {}
    
    region_stats = {}
    total_stores = len(stores_data)
    
    for store in stores_data:
        region = store['region']
        if region not in region_stats:
            region_stats[region] = {
                'count': 0,
                'percentage': 0,
                'inventory': 0,
                'in_stock_stores': 0
            }
        
        region_stats[region]['count'] += 1
        region_stats[region]['inventory'] += store['stock']
        if store['stock'] > 0:
            region_stats[region]['in_stock_stores'] += 1
    
    # 计算百分比
    for region in region_stats:
        region_stats[region]['percentage'] = round(
            region_stats[region]['count'] / total_stores * 100, 2
        ) if total_stores > 0 else 0
    
    return region_stats


def calculate_product_depth_stats_by_region(favorites_list, inventory_matrix):
    """计算产品深度库存统计（按区域分布）"""
    if not favorites_list or not inventory_matrix:
        return {}
    
    product_stats = {}
    
    for favorite in favorites_list:
        # 构建产品键值，优先使用英文名称
        product_name = favorite.get('product_name_en') or favorite.get('product_name', '')
        product_key = f"{product_name} {favorite.get('color', '')} {favorite.get('size', '')}"
        
        product_stats[product_key] = {
            "total_inventory": 0,
            "stores_with_stock": 0,
            "region_distribution": {
                "首尔城区": {"total": 0, "stores": []},
                "京畿道地区": {"total": 0, "stores": []},
                "釜山": {"total": 0, "stores": []},
                "大邱": {"total": 0, "stores": []},
                "其他地区": {"total": 0, "stores": []}
            }
        }
        
        # 统计每个店铺的库存
        for store_name, products in inventory_matrix.items():
            if product_key in products:
                stock = products[product_key]
                if stock and str(stock).isdigit():
                    stock_count = int(stock)
                    if stock_count > 0:
                        # 更新总统计
                        product_stats[product_key]["total_inventory"] += stock_count
                        product_stats[product_key]["stores_with_stock"] += 1
                        
                        # 确定区域
                        region = get_store_region(store_name)
                        if region not in product_stats[product_key]["region_distribution"]:
                            region = "其他地区"
                        
                        # 添加店铺详情
                        product_stats[product_key]["region_distribution"][region]["total"] += stock_count
                        product_stats[product_key]["region_distribution"][region]["stores"].append({
                            "store_name": store_name,
                            "stock": stock_count
                        })
        
        # 对每个区域的店铺按库存量降序排序
        for region_key in product_stats[product_key]["region_distribution"]:
            product_stats[product_key]["region_distribution"][region_key]["stores"].sort(
                key=lambda x: x["stock"], reverse=True
            )
    
    return product_stats


def calculate_enhanced_inventory_stats_combined(inventory_matrix):
    """计算增强版库存统计（综合版本）"""
    if not inventory_matrix:
        return {}
    
    # 计算库存状态分布
    stock_status = calculate_stock_status_distribution_from_matrix(inventory_matrix)
    
    # 计算区域热力图
    region_heatmap = calculate_region_heatmap_from_matrix(inventory_matrix)
    
    return {
        "stock_status": stock_status,
        "region_heatmap": region_heatmap
    }


def calculate_stock_status_distribution_from_matrix(inventory_matrix):
    """从库存矩阵计算库存状态分布"""
    stock_stats = {
        "高库存店铺": {"count": 0, "percentage": 0},
        "低库存店铺": {"count": 0, "percentage": 0},
        "无库存店铺": {"count": 0, "percentage": 0}
    }
    
    total_stores = len(inventory_matrix)
    if total_stores == 0:
        return stock_stats
    
    for store_name, products in inventory_matrix.items():
        has_stock = False
        low_stock = False
        
        for stock in products.values():
            if stock and str(stock).isdigit():
                stock_count = int(stock)
                if stock_count > 0:
                    has_stock = True
                    if 1 <= stock_count <= 2:
                        low_stock = True
                    break
        
        if has_stock:
            if low_stock:
                stock_stats["低库存店铺"]["count"] += 1
            else:
                stock_stats["高库存店铺"]["count"] += 1
        else:
            stock_stats["无库存店铺"]["count"] += 1
    
    # 计算百分比
    for key in stock_stats:
        stock_stats[key]["percentage"] = round((stock_stats[key]["count"] / total_stores) * 100, 2)
    
    return stock_stats


def calculate_region_heatmap_from_matrix(inventory_matrix):
    """从库存矩阵计算区域热力图"""
    region_stats = {}
    total_stores = len(inventory_matrix)
    
    for store_name, products in inventory_matrix.items():
        region = get_store_region(store_name)
        
        if region not in region_stats:
            region_stats[region] = {
                'count': 0,
                'percentage': 0,
                'inventory': 0,
                'in_stock_stores': 0
            }
        
        region_stats[region]['count'] += 1
        
        # 统计库存总量
        total_inventory = 0
        has_stock = False
        for stock in products.values():
            if stock and str(stock).isdigit():
                stock_count = int(stock)
                total_inventory += stock_count
                if stock_count > 0:
                    has_stock = True
        
        region_stats[region]['inventory'] += total_inventory
        if has_stock:
            region_stats[region]['in_stock_stores'] += 1
    
    # 计算百分比
    for region in region_stats:
        region_stats[region]['percentage'] = round(
            region_stats[region]['count'] / total_stores * 100, 2
        ) if total_stores > 0 else 0
    
    return region_stats
