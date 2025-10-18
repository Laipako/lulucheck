# config.py
# 系统配置文件

# ScraperAPI配置
SCRAPER_API_KEY = "420b6b6ad161ba091d728cba109b8df5"
SCRAPER_API_URL = "https://api.scraperapi.com/"

# Lululemon相关URL
LULULEMON_BASE_URL = "https://www.lululemon.co.kr"
LULULEMON_SEARCH_URL = f"{LULULEMON_BASE_URL}/ko-kr/search"
LULULEMON_INVENTORY_URL = f"{LULULEMON_BASE_URL}/on/demandware.store/Sites-KR-Site/ko_KR/InStores-FindStores"

# 汇率API配置
EXCHANGE_RATE_URL = "https://www.unionpayintl.com/upload/jfimg/"

# 地区坐标配置
REGION_COORDS = {
    "1": {"lat": "37.56521290000001", "long": "126.9773517"},  # 首尔
    "2": {"lat": "35.1731121", "long": "129.0714122"}  # 釜山
}

# 请求超时配置
REQUEST_TIMEOUT = 10

# 缓存配置
CACHE_TTL = 3600  # 1小时

# 分页配置
DEFAULT_PAGE_SIZE = 16
MAX_PAGE_SIZE = 100
