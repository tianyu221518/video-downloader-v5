#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
哔哩哔哩平台下载模块
"""

import requests
from .base_platform import BasePlatform

class BilibiliPlatform(BasePlatform):
    """哔哩哔哩平台处理类"""
    
    def __init__(self):
        """初始化哔哩哔哩平台"""
        super().__init__("bilibili", "哔哩哔哩")
    
    def process_url(self, url):
        """
        处理B站URL，转换为标准格式
        
        Args:
            url (str): 原始B站URL
            
        Returns:
            str: 处理后的标准B站URL
        """
        # 先调用父类的标准处理
        url = super().process_url(url)
        
        # 处理B站短链接
        if 'b23.tv' in url:
            try:
                response = requests.head(url, allow_redirects=True, timeout=5)
                if response.status_code == 200:
                    url = response.url
            except Exception:
                pass
        
        return url
    
    def get_ydl_opts_for_info(self, url):
        """
        为获取B站视频信息设置yt-dlp选项
        
        Args:
            url (str): B站视频URL
            
        Returns:
            dict: yt-dlp选项配置
        """
        ydl_opts = super().get_ydl_opts_for_info(url)
        
        # B站特定配置
        ydl_opts.update({
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Referer': 'https://www.bilibili.com/',
            },
            # B站特有参数
            'extract_flat': False,
            'playliststart': 1,
            'playlistend': 200,
        })
        
        return ydl_opts
    
    def get_ydl_opts_for_formats(self, url):
        """
        为获取B站视频格式设置yt-dlp选项
        
        Args:
            url (str): B站视频URL
            
        Returns:
            dict: yt-dlp选项配置
        """
        ydl_opts = super().get_ydl_opts_for_formats(url)
        
        # B站特定配置
        ydl_opts.update({
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Referer': 'https://www.bilibili.com/',
            },
            # B站特有参数
            'extractor_args': {
                'bilibili': {'no_live_chat': True}
            },
        })
        
        return ydl_opts
    
    def is_supported(self, url):
        """
        检查URL是否为B站链接
        
        Args:
            url (str): 视频URL
            
        Returns:
            bool: 是否为B站链接
        """
        return any(pattern in url for pattern in ['bilibili.com', 'b23.tv'])
