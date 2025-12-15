#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音平台下载模块
"""

from .base_platform import BasePlatform

class DouyinPlatform(BasePlatform):
    """抖音平台处理类"""
    
    def __init__(self):
        """初始化抖音平台"""
        super().__init__("douyin", "抖音")
    
    def process_url(self, url):
        """
        处理抖音URL，转换为标准格式
        
        Args:
            url (str): 原始抖音URL
            
        Returns:
            str: 处理后的标准抖音URL
        """
        # 先调用父类的标准处理
        url = super().process_url(url)
        
        # 处理抖音的各种链接格式
        if 'modal_id=' in url:
            modal_id = url.split('modal_id=')[1].split('&')[0]
            url = f"https://www.douyin.com/video/{modal_id}"
        elif 'share/video/' in url:
            # 处理分享链接
            video_id = url.split('share/video/')[1].split('/')[0]
            url = f"https://www.douyin.com/video/{video_id}"
        
        return url
    
    def get_ydl_opts_for_info(self, url):
        """
        为获取抖音视频信息设置yt-dlp选项
        
        Args:
            url (str): 抖音视频URL
            
        Returns:
            dict: yt-dlp选项配置
        """
        ydl_opts = super().get_ydl_opts_for_info(url)
        
        # 抖音特定配置
        ydl_opts.update({
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Referer': 'https://www.douyin.com/',
            },
            'no_check_certificate': True,
            'ignoreerrors': True,
            # 针对抖音的特殊参数
            'extractor_args': {
                'douyin': {'no_watermark': True}
            }
        })
        
        return ydl_opts
    
    def get_ydl_opts_for_formats(self, url):
        """
        为获取抖音视频格式设置yt-dlp选项
        
        Args:
            url (str): 抖音视频URL
            
        Returns:
            dict: yt-dlp选项配置
        """
        ydl_opts = super().get_ydl_opts_for_formats(url)
        
        # 抖音特定配置
        ydl_opts.update({
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Referer': 'https://www.douyin.com/',
            },
            # 针对抖音的特殊参数
            'extractor_args': {
                'douyin': {'no_watermark': True, 'include_comments': False}
            },
        })
        
        return ydl_opts
    
    def is_supported(self, url):
        """
        检查URL是否为抖音链接
        
        Args:
            url (str): 视频URL
            
        Returns:
            bool: 是否为抖音链接
        """
        return any(pattern in url for pattern in ['douyin.com', 'tiktok.com', 'v.douyin.com', 'www.tiktok.com'])
