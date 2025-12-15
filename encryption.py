#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加密工具类，用于保护用户隐私数据
"""

import os
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class EncryptionTool:
    """加密工具类，提供数据加密和解密功能"""
    
    def __init__(self, password="video_downloader_secret", salt_file="encryption_salt.json"):
        """初始化加密工具
        
        Args:
            password: 加密密码
            salt_file: 盐值存储文件
        """
        self.password = password
        self.salt_file = salt_file
        self.salt = self._get_or_create_salt()
        self.key = self._derive_key()
        self.cipher = Fernet(self.key)
    
    def _get_or_create_salt(self):
        """获取或创建盐值"""
        if os.path.exists(self.salt_file):
            try:
                with open(self.salt_file, "r") as f:
                    salt_data = json.load(f)
                    return base64.b64decode(salt_data["salt"])
            except Exception as e:
                print(f"读取盐值失败: {e}")
        
        # 创建新盐值
        salt = os.urandom(16)
        salt_data = {"salt": base64.b64encode(salt).decode()}
        with open(self.salt_file, "w") as f:
            json.dump(salt_data, f)
        return salt
    
    def _derive_key(self):
        """从密码和盐值派生密钥"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.password.encode()))
        return key
    
    def encrypt(self, data):
        """加密数据
        
        Args:
            data: 要加密的数据（字符串）
            
        Returns:
            加密后的数据（字符串）
        """
        if not isinstance(data, str):
            data = str(data)
        encrypted_data = self.cipher.encrypt(data.encode())
        return encrypted_data.decode()
    
    def decrypt(self, encrypted_data):
        """解密数据
        
        Args:
            encrypted_data: 要解密的数据（字符串）
            
        Returns:
            解密后的数据（字符串）
        """
        if not encrypted_data:
            return ""
        decrypted_data = self.cipher.decrypt(encrypted_data.encode())
        return decrypted_data.decode()
    
    def encrypt_dict(self, data_dict):
        """加密字典
        
        Args:
            data_dict: 要加密的字典
            
        Returns:
            加密后的字典（所有值都已加密）
        """
        encrypted_dict = {}
        for key, value in data_dict.items():
            if isinstance(value, dict):
                encrypted_dict[key] = self.encrypt_dict(value)
            elif isinstance(value, list):
                encrypted_dict[key] = [self.encrypt(item) if isinstance(item, str) else item for item in value]
            elif isinstance(value, str):
                encrypted_dict[key] = self.encrypt(value)
            else:
                encrypted_dict[key] = value
        return encrypted_dict
    
    def decrypt_dict(self, encrypted_dict):
        """解密字典
        
        Args:
            encrypted_dict: 要解密的字典
            
        Returns:
            解密后的字典
        """
        decrypted_dict = {}
        for key, value in encrypted_dict.items():
            if isinstance(value, dict):
                decrypted_dict[key] = self.decrypt_dict(value)
            elif isinstance(value, list):
                decrypted_dict[key] = [self.decrypt(item) if isinstance(item, str) else item for item in value]
            elif isinstance(value, str):
                decrypted_dict[key] = self.decrypt(value)
            else:
                decrypted_dict[key] = value
        return decrypted_dict
