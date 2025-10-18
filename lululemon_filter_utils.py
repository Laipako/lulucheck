import pandas as pd
from io import BytesIO
from lululemon_inventory_check import get_store_region


def any_has_stock(products):
    """检查店铺中是否有任何产品有库存"""
    for stock in products.values():
        if stock and str(stock).isdigit() and int(stock) > 0:
            return True
    return False


def store_in_region(store_name, target_region):
    """检查店铺是否在目标区域"""
    if target_region == "全部":
        return True
    return get_store_region(store_name) == target_region


def apply_filters_and_sort(inventory_matrix, stock_filter, region_filter, sort_option):
    """应用筛选和排序"""
    filtered_data = {}
    
    for store_name, products in inventory_matrix.items():
        # 库存状态筛选
        if stock_filter != "全部":
            has_stock = any_has_stock(products)
            if (stock_filter == "有库存" and not has_stock) or \
                    (stock_filter == "无库存" and has_stock):
                continue
        
        # 区域筛选
        if region_filter != "全部" and not store_in_region(store_name, region_filter):
            continue
        
        filtered_data[store_name] = products
    
    # 排序
    if sort_option != "默认":
        sorted_items = sorted(
            filtered_data.items(),
            key=lambda x: sum(int(stock) for stock in x[1].values() if stock and str(stock).isdigit()),
            reverse=(sort_option == "库存总量降序")
        )
        filtered_data = dict(sorted_items)
    
    return filtered_data


def convert_to_excel(df):
    """将DataFrame转换为Excel字节流"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='库存数据', index=True)
    excel_data = output.getvalue()
    return excel_data


def create_inventory_visualization(inventory_matrix):
    """创建库存可视化图表"""
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 准备数据
    store_names = []
    total_inventory = []
    regions = []
    
    for store_name, products in inventory_matrix.items():
        store_names.append(store_name)
        total_inventory.append(sum(int(stock) for stock in products.values() if stock and str(stock).isdigit()))
        regions.append(get_store_region(store_name))
    
    # 创建图表
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # 库存分布柱状图
    ax1.bar(range(len(store_names)), total_inventory)
    ax1.set_title('各店铺库存总量分布')
    ax1.set_xlabel('店铺')
    ax1.set_ylabel('库存总量')
    ax1.tick_params(axis='x', rotation=45)
    
    # 区域库存热力图
    region_data = {}
    for i, region in enumerate(regions):
        if region not in region_data:
            region_data[region] = 0
        region_data[region] += total_inventory[i]
    
    regions_list = list(region_data.keys())
    inventory_list = list(region_data.values())
    
    ax2.bar(regions_list, inventory_list, color='skyblue')
    ax2.set_title('区域库存分布')
    ax2.set_xlabel('区域')
    ax2.set_ylabel('库存总量')
    ax2.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    return fig


def generate_inventory_report(inventory_matrix, favorites_list):
    """生成库存分析报告"""
    from lululemon_inventory_check import (
        calculate_enhanced_inventory_stats_combined,
        calculate_product_depth_stats_by_region
    )
    
    # 计算统计数据
    stats = calculate_enhanced_inventory_stats_combined(inventory_matrix)
    product_stats = calculate_product_depth_stats_by_region(favorites_list, inventory_matrix)
    
    report = {
        "summary": {
            "total_stores": len(inventory_matrix),
            "total_products": len(favorites_list),
            "stock_status": stats.get("stock_status", {}),
            "region_distribution": stats.get("region_heatmap", {})
        },
        "product_analysis": product_stats,
        "recommendations": []
    }
    
    # 生成建议
    if stats.get("stock_status", {}).get("无库存店铺", {}).get("percentage", 0) > 50:
        report["recommendations"].append("⚠️ 超过50%的店铺无库存，建议考虑补货")
    
    if stats.get("region_heatmap", {}).get("首尔城区", {}).get("inventory", 0) > 0:
        report["recommendations"].append("✅ 首尔城区库存充足，适合优先采购")
    
    return report
