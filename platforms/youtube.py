#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube平台下载模块
"""

from .base_platform import BasePlatform

class YouTubePlatform(BasePlatform):
    """YouTube平台处理类"""
    
    def __init__(self):
        """初始化YouTube平台"""
        super().__init__("youtube", "YouTube")
    
    def process_url(self, url):
        """
        处理YouTube URL，转换为标准格式
        
        Args:
            url (str): 原始YouTube URL
            
        Returns:
            str: 处理后的标准YouTube URL
        """
        # 先调用父类的标准处理
        url = super().process_url(url)
        
        # 处理YouTube短链接
        if 'youtu.be' in url:
            video_id = url.split('youtu.be/')[1].split('?')[0]
            url = f"https://www.youtube.com/watch?v={video_id}"
        
        return url
    
    def get_ydl_opts_for_info(self, url):
        """
        为获取YouTube视频信息设置yt-dlp选项
        
        Args:
            url (str): YouTube视频URL
            
        Returns:
            dict: yt-dlp选项配置
        """
        ydl_opts = super().get_ydl_opts_for_info(url)
        
        # YouTube特定配置
        ydl_opts.update({
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
            },
            # YouTube特有参数
            'extract_flat': False,
            'playliststart': 1,
            'playlistend': 200,
            'ignoreerrors': True,
        })
        
        return ydl_opts
    
    def get_ydl_opts_for_formats(self, url):
        """
        为获取YouTube视频格式设置yt-dlp选项
        
        Args:
            url (str): YouTube视频URL
            
        Returns:
            dict: yt-dlp选项配置
        """
        ydl_opts = super().get_ydl_opts_for_formats(url)
        
        # YouTube特定配置
        ydl_opts.update({
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
            },
            'ignoreerrors': True,
            'extract_flat': False,
            'socket_timeout': 45,  # YouTube可能需要更长的超时时间
            'retries': 5,
            'fragment_retries': 5,
            'extractor_retries': 5,
        })
        
        return ydl_opts
    
    def is_supported(self, url):
        """
        检查URL是否为YouTube链接
        
        Args:
            url (str): 视频URL
            
        Returns:
            bool: 是否为YouTube链接
        """
        return any(pattern in url for pattern in ['youtube.com', 'youtu.be'])
