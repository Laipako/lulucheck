#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版Supabase客户端模块
用于管理收藏数据的数据库操作
包含详细诊断、自动恢复和连接监控功能
"""

import json
import os
import time
import traceback
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import streamlit as st

# 尝试导入supabase包
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
    print("✅ Supabase包导入成功")
except ImportError as e:
    print(f"⚠️ Supabase导入失败，使用本地文件存储: {e}")
    print("💡 解决方案: pip install supabase>=2.0.0")
    SUPABASE_AVAILABLE = False
    # 创建模拟的Client类
    class Client:
        pass
except Exception as e:
    print(f"❌ Supabase包导入时发生未知错误: {e}")
    SUPABASE_AVAILABLE = False
    class Client:
        pass


class ConnectionDiagnostics:
    """连接诊断工具"""
    
    @staticmethod
    def check_environment():
        """检查环境配置"""
        diagnostics = {
            "timestamp": datetime.now().isoformat(),
            "supabase_available": SUPABASE_AVAILABLE,
            "secrets_available": False,
            "connection_test": False,
            "error_details": []
        }
        
        # 检查Streamlit secrets
        try:
            if hasattr(st, 'secrets') and hasattr(st.secrets, 'supabase'):
                url = st.secrets.supabase.url
                key = st.secrets.supabase.key
                if url and key:
                    diagnostics["secrets_available"] = True
                    diagnostics["url"] = url
                    diagnostics["key_length"] = len(key)
                else:
                    diagnostics["error_details"].append("Supabase URL或Key为空")
            else:
                diagnostics["error_details"].append("Streamlit secrets中缺少supabase配置")
        except Exception as e:
            diagnostics["error_details"].append(f"Secrets检查失败: {str(e)}")
        
        return diagnostics
    
    @staticmethod
    def test_connection(url: str, key: str) -> Dict[str, Any]:
        """测试Supabase连接"""
        result = {
            "success": False,
            "error": None,
            "response_time": None,
            "table_exists": False,
            "record_count": 0
        }
        
        if not SUPABASE_AVAILABLE:
            result["error"] = "Supabase包不可用"
            return result
        
        try:
            start_time = time.time()
            client = create_client(url, key)
            
            # 测试数据库连接
            response = client.table('lululemon_favorites').select('*').limit(1).execute()
            
            result["success"] = True
            result["response_time"] = time.time() - start_time
            result["table_exists"] = True
            result["record_count"] = len(response.data) if response.data else 0
            
        except Exception as e:
            result["error"] = str(e)
            result["traceback"] = traceback.format_exc()
        
        return result


class LocalFileManager:
    """增强版本地文件存储管理器"""
    
    def __init__(self):
        self.data_file = "favorites_data.json"
        self.backup_file = "favorites_data_backup.json"
        self.ensure_data_file()
        self.last_sync_time = None
    
    def ensure_data_file(self):
        """确保数据文件存在"""
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    def create_backup(self):
        """创建数据备份"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as src:
                    data = src.read()
                with open(self.backup_file, 'w', encoding='utf-8') as dst:
                    dst.write(data)
                return True
        except Exception as e:
            print(f"⚠️ 创建备份失败: {e}")
        return False
    
    def load_data(self):
        """加载数据，支持自动恢复"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.last_sync_time = datetime.now()
            return data
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析错误，尝试从备份恢复: {e}")
            return self.restore_from_backup()
        except Exception as e:
            print(f"❌ 加载本地数据失败: {e}")
            return self.restore_from_backup()
    
    def restore_from_backup(self):
        """从备份恢复数据"""
        try:
            if os.path.exists(self.backup_file):
                with open(self.backup_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print("✅ 从备份恢复数据成功")
                return data
        except Exception as e:
            print(f"❌ 从备份恢复失败: {e}")
        return []
    
    def save_data(self, data):
        """保存数据，包含备份机制"""
        try:
            # 创建备份
            self.create_backup()
            
            # 保存新数据
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.last_sync_time = datetime.now()
            return True
        except Exception as e:
            print(f"❌ 保存本地数据失败: {e}")
            return False
    
    def get_status(self):
        """获取本地存储状态"""
        return {
            "file_exists": os.path.exists(self.data_file),
            "backup_exists": os.path.exists(self.backup_file),
            "last_sync": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "file_size": os.path.getsize(self.data_file) if os.path.exists(self.data_file) else 0
        }


class EnhancedSupabaseManager:
    """增强版Supabase管理器"""
    
    _instance = None
    _connection_retry_count = 0
    _max_retries = 3
    _retry_delay = 5  # 秒
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EnhancedSupabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.init_client()
            self._initialized = True
    
    def init_client(self):
        """初始化Supabase客户端，包含重试机制"""
        self.use_local_storage = False
        self.client = None
        self.local_manager = LocalFileManager()
        self.diagnostics = ConnectionDiagnostics()
        self.connection_status = "unknown"
        self.last_connection_test = None
        
        # 如果Supabase包不可用，直接使用本地存储
        if not SUPABASE_AVAILABLE:
            print("⚠️ Supabase包不可用，使用本地文件存储")
            self.use_local_storage = True
            self.connection_status = "package_unavailable"
            return
        
        # 尝试连接Supabase
        self._attempt_connection()
    
    def _attempt_connection(self):
        """尝试连接Supabase，包含重试逻辑"""
        for attempt in range(self._max_retries):
            try:
                print(f"🔄 尝试连接Supabase (第{attempt + 1}次)...")
                
                # 从config.py获取配置
                from config import SUPABASE_URL, SUPABASE_KEY
                self.url = SUPABASE_URL
                self.key = SUPABASE_KEY
                
                # 创建客户端
                self.client = create_client(self.url, self.key)
                
                # 测试连接
                test_result = self.diagnostics.test_connection(self.url, self.key)
                
                if test_result["success"]:
                    print("✅ Supabase连接成功")
                    print(f"   响应时间: {test_result['response_time']:.2f}秒")
                    print(f"   表记录数: {test_result['record_count']}")
                    self.connection_status = "connected"
                    self.last_connection_test = datetime.now()
                    return
                else:
                    print(f"❌ 连接测试失败: {test_result['error']}")
                    if attempt < self._max_retries - 1:
                        print(f"⏳ {self._retry_delay}秒后重试...")
                        time.sleep(self._retry_delay)
                        self._retry_delay *= 2  # 指数退避
                
            except Exception as e:
                print(f"❌ 连接尝试失败: {e}")
                if attempt < self._max_retries - 1:
                    print(f"⏳ {self._retry_delay}秒后重试...")
                    time.sleep(self._retry_delay)
                    self._retry_delay *= 2
        
        # 所有重试都失败，切换到本地存储
        print("⚠️ 所有连接尝试失败，切换到本地文件存储模式")
        self.use_local_storage = True
        self.connection_status = "connection_failed"
        self.client = None
    
    def reconnect(self):
        """重新连接Supabase"""
        print("🔄 尝试重新连接Supabase...")
        self._connection_retry_count = 0
        self._retry_delay = 5
        self._attempt_connection()
    
    def get_client(self):
        """获取客户端，支持自动重连"""
        if self.use_local_storage:
            return self.local_manager
        
        if self.client:
            # 测试连接是否仍然有效
            try:
                self.client.table('lululemon_favorites').select('*').limit(1).execute()
                return self.client
            except Exception as e:
                print(f"⚠️ 连接已断开，尝试重连: {e}")
                self.reconnect()
                if not self.use_local_storage:
                    return self.client
                else:
                    return self.local_manager
        else:
            raise Exception("Supabase连接不可用")
    
    def get_status(self):
        """获取连接状态"""
        return {
            "connection_status": self.connection_status,
            "use_local_storage": self.use_local_storage,
            "last_connection_test": self.last_connection_test.isoformat() if self.last_connection_test else None,
            "supabase_available": SUPABASE_AVAILABLE,
            "local_storage_status": self.local_manager.get_status() if self.use_local_storage else None
        }
    
    def get_diagnostics(self):
        """获取详细诊断信息"""
        env_check = self.diagnostics.check_environment()
        return {
            "environment": env_check,
            "status": self.get_status(),
            "timestamp": datetime.now().isoformat()
        }


class FavoritesDataManager:
    """收藏数据管理器 - 统一接口"""
    
    def __init__(self):
        self.supabase_manager = EnhancedSupabaseManager()
    
    def add_favorite(self, product_data: Dict[str, Any]) -> bool:
        """添加收藏"""
        try:
            client = self.supabase_manager.get_client()
            
            if self.supabase_manager.use_local_storage:
                # 本地存储
                data = client.load_data()
                data.append(product_data)
                return client.save_data(data)
            else:
                # Supabase存储
                response = client.table('lululemon_favorites').insert(product_data).execute()
                return len(response.data) > 0
                
        except Exception as e:
            print(f"❌ 添加收藏失败: {e}")
            return False
    
    def remove_favorite(self, product_id: str) -> bool:
        """移除收藏"""
        try:
            client = self.supabase_manager.get_client()
            
            if self.supabase_manager.use_local_storage:
                # 本地存储
                data = client.load_data()
                data = [item for item in data if item.get('id') != product_id]
                return client.save_data(data)
            else:
                # Supabase存储
                response = client.table('lululemon_favorites').delete().eq('id', product_id).execute()
                return True
                
        except Exception as e:
            print(f"❌ 移除收藏失败: {e}")
            return False
    
    def get_favorites(self) -> List[Dict[str, Any]]:
        """获取所有收藏"""
        try:
            client = self.supabase_manager.get_client()
            
            if self.supabase_manager.use_local_storage:
                # 本地存储
                return client.load_data()
            else:
                # Supabase存储
                response = client.table('lululemon_favorites').select('*').execute()
                return response.data if response.data else []
                
        except Exception as e:
            print(f"❌ 获取收藏失败: {e}")
            return []
    
    def is_favorite(self, product_id: str) -> bool:
        """检查是否为收藏"""
        try:
            client = self.supabase_manager.get_client()
            
            if self.supabase_manager.use_local_storage:
                # 本地存储
                data = client.load_data()
                return any(item.get('id') == product_id for item in data)
            else:
                # Supabase存储
                response = client.table('lululemon_favorites').select('id').eq('id', product_id).execute()
                return len(response.data) > 0 if response.data else False
                
        except Exception as e:
            print(f"❌ 检查收藏状态失败: {e}")
            return False
    
    def get_storage_info(self):
        """获取存储信息"""
        return self.supabase_manager.get_status()
    
    def get_diagnostics(self):
        """获取诊断信息"""
        return self.supabase_manager.get_diagnostics()


# 创建全局管理器实例
favorites_manager = FavoritesDataManager()
