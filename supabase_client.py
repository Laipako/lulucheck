# supabase_client.py
import streamlit as st
import json
import os
from datetime import datetime
from config import SUPABASE_URL, SUPABASE_KEY

# 尝试导入supabase，如果失败则使用本地文件存储
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Supabase导入失败，使用本地文件存储: {e}")
    SUPABASE_AVAILABLE = False
    # 创建模拟的Client类
    class Client:
        pass


class LocalFileManager:
    """本地文件存储管理器"""
    def __init__(self):
        self.data_file = "favorites_data.json"
        self.ensure_data_file()
    
    def ensure_data_file(self):
        """确保数据文件存在"""
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    def load_data(self):
        """加载数据"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌❌ 加载本地数据失败: {e}")
            return []
    
    def save_data(self, data):
        """保存数据"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌❌ 保存本地数据失败: {e}")
            return False


class SupabaseManager:
    """Supabase 管理类"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseManager, cls).__new__(cls)
            cls._instance.init_client()
        return cls._instance

    def init_client(self):
        """初始化Supabase客户端"""
        self.use_local_storage = False
        
        if not SUPABASE_AVAILABLE:
            print("⚠️ Supabase不可用，使用本地文件存储")
            self.client = None
            self.use_local_storage = True
            self.local_manager = LocalFileManager()
            return
            
        try:
            # 从config.py获取配置
            self.url = SUPABASE_URL
            self.key = SUPABASE_KEY
            self.client: Client = create_client(self.url, self.key)
            print("✅ Supabase连接成功")
        except Exception as e:
            print(f"❌❌ Supabase 客户端初始化失败: {e}")
            print("⚠️ 切换到本地文件存储模式")
            self.client = None
            self.use_local_storage = True
            self.local_manager = LocalFileManager()

    def get_client(self):
        """获取Supabase客户端"""
        if self.use_local_storage:
            return self.local_manager
        elif self.client:
            return self.client
        else:
            raise Exception("Supabase连接不可用")


# 创建全局Supabase管理器实例
supabase_manager = SupabaseManager()
