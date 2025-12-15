#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平台基类 - 定义所有平台模块的统一接口
"""

import os

class BasePlatform:
    """平台基类，定义统一的接口"""
    
    def __init__(self, platform_id, platform_name):
        """
        初始化平台模块
        
        Args:
            platform_id (str): 平台唯一标识符
            platform_name (str): 平台名称
        """
        self.platform_id = platform_id
        self.platform_name = platform_name
    
    def process_url(self, url):
        """
        处理URL，优化对平台链接的支持
        
        Args:
            url (str): 原始URL
            
        Returns:
            str: 处理后的URL
        """
        # 标准化URL（添加协议）
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            self.logger.info(f"已添加HTTPS协议: {url}")
        return url
    
    def get_ydl_opts_for_info(self, url):
        """
        为获取视频信息设置yt-dlp选项
        
        Args:
            url (str): 视频URL
            
        Returns:
            dict: yt-dlp选项配置
        """
        return {
            'quiet': True,
            'no_warnings': False,
            'extract_flat': False,
            'socket_timeout': 30,
            'retries': 3,
            'sleep_interval': 5,
            'outtmpl': os.devnull,
        }
    
    def get_ydl_opts_for_formats(self, url):
        """
        为获取视频格式设置yt-dlp选项
        
        Args:
            url (str): 视频URL
            
        Returns:
            dict: yt-dlp选项配置
        """
        return {
            'quiet': True,
            'no_warnings': True,
            'simulate': True,
            'skip_download': True,
            'ignoreerrors': True,
            'no_check_certificate': True,
            'allow_unplayable_formats': True,
            'extractor_retries': 3,
            'socket_timeout': 30,
            'retries': 3,
            'sleep_interval': 5,
            'logtostderr': False,
            'no_color': True,
            'outtmpl': os.devnull,
        }
    
    def get_ydl_opts_for_download(self, format_selector, download_path):
        """
        为下载视频设置yt-dlp选项
        
        Args:
            format_selector (str): 格式选择器
            download_path (str): 下载路径
            
        Returns:
            dict: yt-dlp选项配置
        """
        return {
            'format': format_selector,
            'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
            'noplaylist': False,
            'extractaudio': False,
            'audioformat': 'mp3',
            'embed_subs': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['zh', 'zh-CN', 'en'],
            'ignoreerrors': True,
            'merge_output_format': 'mp4',
            'allow_unplayable_formats': True,
            'no_check_certificate': True,
            'socket_timeout': 30,
            'retries': 10,
            'fragment_retries': 10,
        }
    
    def is_supported(self, url):
        """
        检查URL是否属于当前平台
        
        Args:
            url (str): 视频URL
            
        Returns:
            bool: 是否支持该URL
        """
        return False
