#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频下载工具 - 支持多平台视频下载
基于yt-dlp，支持抖音、B站、YouTube、腾讯视频、爱奇艺、优酷、微博、快手等
"""

import os
import json
import threading
import subprocess
import platform
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText

# 导入加密工具
from encryption import EncryptionTool

# 导入平台模块
from platforms.douyin import DouyinPlatform
from platforms.bilibili import BilibiliPlatform
from platforms.youtube import YouTubePlatform

class VideoDownloader:
    """视频下载工具主类"""
    
    def __init__(self, root):
        """初始化应用程序"""
        self.root = root
        self.root.title("视频下载工具")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # 窗口关闭时的处理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 下载路径设置 - 使用持久化存储
        self.prefs_file = "download_prefs.json"
        self.download_path = os.path.join(os.path.expanduser("~"), "Downloads", "视频下载")
        
        # 读取下载路径偏好
        if os.path.exists(self.prefs_file):
            try:
                with open(self.prefs_file, "r", encoding="utf-8") as f:
                    prefs = json.load(f)
                    if "download_path" in prefs:
                        self.download_path = prefs["download_path"]
            except Exception as e:
                self.log(f"读取下载路径偏好失败: {str(e)}")
        
        # 确保下载目录存在
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
        
        # 上次下载的文件路径
        self.last_downloaded_file = None
        
        # 下载状态
        self.downloading = False
        self.download_thread = None
        
        # 格式转换相关变量
        self.convert_after_download = False
        self.target_format = "mp4"
        
        # 断点续传相关变量
        self.resume_downloads = True
        self.progress_file = "download_progress.json"
        self.download_progress = {}
        
        # 加密工具初始化
        self.encryption_tool = EncryptionTool()
        
        # 下载历史记录（加密存储）
        self.history_file = "download_history.json"
        self.download_history = self._load_encrypted_history()
        
        # 初始化平台模块
        self.platform_modules = {
            "douyin": DouyinPlatform(),
            "bilibili": BilibiliPlatform(),
            "youtube": YouTubePlatform()
        }
        
        # 支持的平台
        self.platforms = {
            "自动检测": "",
            "哔哩哔哩": "bilibili",
            "抖音": "douyin",
            "YouTube": "youtube",
            "腾讯视频": "v.qq.com",
            "爱奇艺": "iqiyi",
            "优酷": "youku",
            "微博": "weibo",
            "快手": "kuaishou"
        }
        
        # 主题相关配置
        self.current_theme = "light"
        self.themes = {
            "light": {
                "name": "浅色主题",
                "bg": "#f0f0f0",
                "fg": "#000000",
                "frame_bg": "#ffffff",
                "label_fg": "#000000",
                "entry_bg": "#ffffff",
                "button_bg": "#d0d0d0",
                "button_fg": "#000000",
                "button_hover": "#b0b0b0",
                "scrollbar_bg": "#d0d0d0",
                "status_label": {"downloading": "#ff8c00", "completed": "#008000", "error": "#ff0000"},
                "log_bg": "#ffffff",
                "log_fg": "#000000"
            },
            "dark": {
                "name": "深色主题",
                "bg": "#2d2d2d",
                "fg": "#ffffff",
                "frame_bg": "#3d3d3d",
                "label_fg": "#ffffff",
                "entry_bg": "#4d4d4d",
                "button_bg": "#5d5d5d",
                "button_fg": "#ffffff",
                "button_hover": "#7d7d7d",
                "scrollbar_bg": "#5d5d5d",
                "status_label": {"downloading": "#ff8c00", "completed": "#00ff00", "error": "#ff0000"},
                "log_bg": "#1d1d1d",
                "log_fg": "#ffffff"
            }
        }
        
        # 主题偏好文件
        self.theme_prefs_file = "theme_prefs.json"
        # 读取主题偏好
        if os.path.exists(self.theme_prefs_file):
            try:
                with open(self.theme_prefs_file, "r", encoding="utf-8") as f:
                    theme_prefs = json.load(f)
                    if "theme" in theme_prefs and theme_prefs["theme"] in self.themes:
                        self.current_theme = theme_prefs["theme"]
            except Exception as e:
                self.log(f"读取主题偏好失败: {str(e)}")
        
        # 初始化UI
        self.setup_ui()
        
        # 初始化日志
        self.setup_log()
        
        # 检查必要的依赖
        self.check_dependencies()
        
    def setup_ui(self):
        """设置用户界面"""
        # 创建Canvas和滚动条实现可滚动主框架
        canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        
        # 创建主框架
        main_frame = ttk.Frame(canvas, padding="10")
        
        # 配置滚动区域
        main_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=main_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 绑定鼠标滚轮事件
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # 布局Canvas和滚动条
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # URL输入区
        url_frame = ttk.LabelFrame(main_frame, text="URL输入", padding="10")
        url_frame.pack(fill=tk.X, pady=5)
        
        # 批量/单条切换
        batch_frame = ttk.Frame(url_frame)
        batch_frame.pack(fill=tk.X, pady=5)
        
        self.batch_mode = tk.BooleanVar(value=False)
        ttk.Checkbutton(batch_frame, text="批量下载模式", variable=self.batch_mode, 
                       command=self.toggle_batch_mode).pack(side=tk.LEFT, padx=5)
        
        # 单条URL输入框
        self.single_url_frame = ttk.Frame(url_frame)
        self.single_url_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.single_url_frame, text="视频URL:").pack(anchor=tk.W)
        self.url_entry = ttk.Entry(self.single_url_frame, width=80)
        self.url_entry.pack(fill=tk.X, pady=5)
        self.url_entry.bind("<Return>", lambda e: self.start_download())
        
        # 批量URL输入框
        self.batch_url_frame = ttk.Frame(url_frame)
        # 默认隐藏，通过toggle_batch_mode显示
        
        ttk.Label(self.batch_url_frame, text="批量URL（每行一个）:").pack(anchor=tk.W)
        self.batch_url_text = ScrolledText(self.batch_url_frame, height=10, width=80)
        self.batch_url_text.pack(fill=tk.X, pady=5)
        
        # 平台选择
        platform_frame = ttk.Frame(url_frame)
        platform_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(platform_frame, text="平台:").pack(side=tk.LEFT, padx=5)
        self.platform_var = tk.StringVar(value="自动检测")
        platform_combo = ttk.Combobox(platform_frame, textvariable=self.platform_var,
                                     values=list(self.platforms.keys()), state="readonly")
        platform_combo.pack(side=tk.LEFT, padx=5)
        
        # 下载路径选择
        path_frame = ttk.Frame(url_frame)
        path_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(path_frame, text="下载路径:").pack(side=tk.LEFT, padx=5)
        self.path_entry = ttk.Entry(path_frame, width=60)
        self.path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.path_entry.insert(0, self.download_path)
        
        browse_btn = ttk.Button(path_frame, text="浏览", command=self.browse_path)
        browse_btn.pack(side=tk.RIGHT, padx=5)
        
        # 格式选择区
        format_frame = ttk.LabelFrame(main_frame, text="格式选择", padding="10")
        format_frame.pack(fill=tk.X, pady=5)
        
        # 质量选择
        ttk.Label(format_frame, text="视频质量:").pack(anchor=tk.W)
        self.quality_var = tk.StringVar(value="自动推荐最佳质量")
        self.quality_combo = ttk.Combobox(format_frame, textvariable=self.quality_var, state="readonly")
        self.quality_combo.pack(fill=tk.X, pady=5)
        
        # 保存可用质量选项
        self.available_qualities = ["自动推荐最佳质量"]
        self.quality_to_format = {"自动推荐最佳质量": "bestvideo+bestaudio/best"}
        
        self.format_var = tk.StringVar(value="默认最佳组合")
        self.format_options = [
            ("默认最佳组合", "bestvideo+bestaudio/best"),
            ("直接选择最佳格式", "best")
        ]
        
        for text, value in self.format_options:
            ttk.Radiobutton(format_frame, text=text, variable=self.format_var, value=value).pack(anchor=tk.W, pady=2)
        
        # 额外选项
        options_frame = ttk.LabelFrame(main_frame, text="额外选项", padding="10")
        options_frame.pack(fill=tk.X, pady=5)
        
        # 断点续传选项
        self.resume_var = tk.BooleanVar(value=self.resume_downloads)
        ttk.Checkbutton(options_frame, text="启用断点续传", variable=self.resume_var).pack(anchor=tk.W, pady=2)
        
        # 格式转换选项
        self.convert_var = tk.BooleanVar(value=self.convert_after_download)
        ttk.Checkbutton(options_frame, text="下载后转换格式", variable=self.convert_var, 
                       command=self.toggle_convert_options).pack(anchor=tk.W, pady=2)
        
        # 目标格式选择
        convert_subframe = ttk.Frame(options_frame)
        convert_subframe.pack(fill=tk.X, padx=20)
        
        ttk.Label(convert_subframe, text="目标格式:").pack(side=tk.LEFT, padx=5)
        self.target_format_var = tk.StringVar(value=self.target_format)
        format_combo = ttk.Combobox(convert_subframe, textvariable=self.target_format_var,
                                   values=["mp4", "avi", "mkv", "webm"], state="readonly")
        format_combo.pack(side=tk.LEFT, padx=5)
        
        # 视频信息预览区
        info_frame = ttk.LabelFrame(main_frame, text="视频信息预览", padding="10")
        info_frame.pack(fill=tk.X, pady=5)
        
        self.info_text = ScrolledText(info_frame, wrap=tk.WORD, height=8)
        self.info_text.pack(fill=tk.BOTH, expand=True)
        self.info_text.configure(state=tk.DISABLED)
        
        # 按钮区
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        self.start_btn = ttk.Button(button_frame, text="开始下载", command=self.start_download, style="Primary.TButton")
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.get_info_btn = ttk.Button(button_frame, text="获取信息", command=self.get_video_info, style="Secondary.TButton")
        self.get_info_btn.pack(side=tk.LEFT, padx=5)
        
        self.copy_info_btn = ttk.Button(button_frame, text="复制信息", command=self.copy_video_info, style="Secondary.TButton")
        self.copy_info_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="停止下载", command=self.stop_download, style="Secondary.TButton")
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # 新增：打开输出文件按钮
        self.open_output_btn = ttk.Button(button_frame, text="打开输出", command=self.open_output_file, style="Secondary.TButton")
        self.open_output_btn.pack(side=tk.LEFT, padx=5)
        
        # 主题切换按钮
        self.theme_btn = ttk.Button(button_frame, text="切换主题", command=self.toggle_theme, style="Secondary.TButton")
        self.theme_btn.pack(side=tk.RIGHT, padx=5)
        
        # 安装依赖按钮
        self.install_btn = ttk.Button(button_frame, text="安装依赖", command=self.install_dependencies, style="Secondary.TButton")
        self.install_btn.pack(side=tk.RIGHT, padx=5)
        
        # 安装FFmpeg按钮
        self.install_ffmpeg_btn = ttk.Button(button_frame, text="安装FFmpeg", command=self.install_ffmpeg, style="Secondary.TButton")
        self.install_ffmpeg_btn.pack(side=tk.RIGHT, padx=5)
        
        # 状态区
        status_frame = ttk.LabelFrame(main_frame, text="下载状态", padding="10")
        status_frame.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="就绪", font=(", 10"))
        self.status_label.pack(anchor=tk.W)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # 日志区
        log_frame = ttk.LabelFrame(main_frame, text="日志信息", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = ScrolledText(log_frame, wrap=tk.WORD, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.configure(state=tk.DISABLED)
        
        # 应用主题
        self.apply_theme()
        
    def apply_theme(self):
        """应用主题"""
        theme = self.themes[self.current_theme]
        
        # 设置窗口背景
        self.root.configure(bg=theme["bg"])
        
        # 配置ttk样式
        style = ttk.Style()
        style.theme_use("clam")
        
        # 基本样式
        style.configure(".", background=theme["bg"], foreground=theme["fg"])
        style.configure("TFrame", background=theme["frame_bg"])
        style.configure("TLabel", background=theme["frame_bg"], foreground=theme["label_fg"])
        style.configure("TEntry", fieldbackground=theme["entry_bg"], foreground=theme["fg"])
        style.configure("TButton", background=theme["button_bg"], foreground=theme["button_fg"])
        style.configure("TRadiobutton", background=theme["frame_bg"], foreground=theme["label_fg"])
        style.configure("TCheckbutton", background=theme["frame_bg"], foreground=theme["label_fg"])
        style.configure("TCombobox", fieldbackground=theme["entry_bg"], foreground=theme["fg"])
        style.configure("Horizontal.TProgressbar", background="#FF5722")
        
        # 按钮样式
        style.configure("Primary.TButton", background="#4CAF50", foreground="white")
        style.configure("Secondary.TButton", background=theme["button_bg"], foreground=theme["button_fg"])
        
        # 配置日志文本框
        self.log_text.configure(bg=theme["log_bg"], fg=theme["log_fg"])
        
        # 保存主题偏好
        try:
            with open(self.theme_prefs_file, "w", encoding="utf-8") as f:
                json.dump({"theme": self.current_theme}, f)
        except Exception as e:
            pass
        
    def toggle_theme(self):
        """切换主题"""
        if self.current_theme == "light":
            self.current_theme = "dark"
        else:
            self.current_theme = "light"
        self.apply_theme()
    
    def toggle_batch_mode(self):
        """切换批量下载模式"""
        if self.batch_mode.get():
            # 切换到批量模式
            self.single_url_frame.pack_forget()
            self.batch_url_frame.pack(fill=tk.X, pady=5)
        else:
            # 切换到单条模式
            self.batch_url_frame.pack_forget()
            self.single_url_frame.pack(fill=tk.X, pady=5)
    
    def setup_log(self):
        """初始化日志"""
        self.log("视频下载工具启动成功")
        self.log("支持平台: 抖音、B站、YouTube、腾讯视频、爱奇艺、优酷、微博、快手")
        self.log(f"当前下载路径: {self.download_path}")
    
    def log(self, message):
        """记录日志"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
        
        # 打印到控制台
        print(log_message.strip())
    
    def check_dependencies(self):
        """检查必要的依赖"""
        # 检查yt-dlp
        try:
            import yt_dlp
            self.log("✓ yt-dlp 已安装")
        except ImportError:
            self.log("✗ yt-dlp 未安装，请点击'安装依赖'按钮自动安装")
        
        # 检查FFmpeg
        self.check_ffmpeg()
        
        # 检查平台模块
        self.log("✓ 平台模块初始化成功")
        for module_id, module in self.platform_modules.items():
            self.log(f"  - {module.platform_name}平台模块已加载")
    
    def _load_encrypted_history(self):
        """加载加密的下载历史"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    encrypted_history = json.load(f)
                return self.encryption_tool.decrypt_dict(encrypted_history)
            except Exception as e:
                self.log(f"读取加密历史失败: {str(e)}")
        return []
    
    def _save_encrypted_history(self):
        """保存加密的下载历史"""
        try:
            encrypted_history = self.encryption_tool.encrypt_dict(self.download_history)
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(encrypted_history, f)
        except Exception as e:
            self.log(f"保存加密历史失败: {str(e)}")
    
    def add_to_history(self, url, title, status, download_path):
        """添加下载记录到历史"""
        history_item = {
            "url": url,
            "title": title,
            "status": status,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "download_path": download_path
        }
        self.download_history.append(history_item)
        # 只保留最近100条记录
        if len(self.download_history) > 100:
            self.download_history = self.download_history[-100:]
        self._save_encrypted_history()
    
    def browse_path(self):
        """浏览下载路径"""
        path = filedialog.askdirectory(initialdir=self.download_path, title="选择下载路径")
        if path:
            self.download_path = path
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)
            
            # 保存下载路径偏好
            try:
                with open(self.prefs_file, "w", encoding="utf-8") as f:
                    json.dump({"download_path": path}, f)
                self.log(f"下载路径已更新并保存: {path}")
            except Exception as e:
                self.log(f"保存下载路径失败: {str(e)}")
    
    
    
    def start_download(self):
        """开始下载视频"""
        urls = []
        
        if self.batch_mode.get():
            # 批量模式，读取所有URL
            batch_text = self.batch_url_text.get(1.0, tk.END).strip()
            if not batch_text:
                messagebox.showerror("错误", "请输入视频URL")
                return
            # 按行分割，过滤空行
            urls = [line.strip() for line in batch_text.split('\n') if line.strip()]
            if not urls:
                messagebox.showerror("错误", "请输入有效的视频URL")
                return
            self.log(f"已获取 {len(urls)} 个视频URL，准备开始批量下载")
        else:
            # 单条模式
            url = self.url_entry.get().strip()
            if not url:
                messagebox.showerror("错误", "请输入视频URL")
                return
            urls = [url]
        
        if self.downloading:
            messagebox.showwarning("警告", "正在下载中，请先停止当前下载")
            return
        
        # 更新配置
        self.download_path = self.path_entry.get().strip()
        self.resume_downloads = self.resume_var.get()
        self.convert_after_download = self.convert_var.get()
        self.target_format = self.target_format_var.get()
        
        # 确保下载目录存在
        if not os.path.exists(self.download_path):
            try:
                os.makedirs(self.download_path)
            except Exception as e:
                messagebox.showerror("错误", f"无法创建下载目录: {str(e)}")
                return
        
        # 开始下载线程
        self.downloading = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="准备下载...")
        
        self.download_thread = threading.Thread(target=self.batch_download, args=(urls,))
        self.download_thread.daemon = True
        self.download_thread.start()
    
    def stop_download(self):
        """停止下载"""
        if not self.downloading:
            return
        
        self.downloading = False
        self.log("正在停止下载...")
    
    def open_output_file(self):
        """打开输出文件或目录"""
        try:
            if hasattr(self, 'last_downloaded_file') and self.last_downloaded_file and os.path.exists(self.last_downloaded_file):
                # 打开最近下载的文件
                self.log(f"打开最近下载的文件: {self.last_downloaded_file}")
                
                if platform.system() == "Windows":
                    # 在Windows上选中文件打开
                    subprocess.Popen(["explorer", "/select,", self.last_downloaded_file])
                elif platform.system() == "Darwin":  # macOS
                    subprocess.Popen(["open", self.last_downloaded_file])
                else:  # Linux
                    subprocess.Popen(["xdg-open", self.last_downloaded_file])
            else:
                # 打开下载目录
                self.log(f"打开下载目录: {self.download_path}")
                
                if platform.system() == "Windows":
                    os.startfile(self.download_path)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.Popen(["open", self.download_path])
                else:  # Linux
                    subprocess.Popen(["xdg-open", self.download_path])
        except Exception as e:
            self.log(f"打开文件/目录失败: {str(e)}")
            messagebox.showerror("错误", f"无法打开文件/目录: {str(e)}")
    
    def _process_url(self, url):
        """处理URL，优化对各平台链接的支持"""
        try:
            # 标准化URL（添加协议）
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                self.log(f"已添加HTTPS协议: {url}")
            
            # 平台检测和特殊处理
            platform_name = "自动检测"
            platform_id = ""
            processed_url = url
            
            # 1. 优先使用平台模块处理
            module_processed = False
            for module_platform_id, module in self.platform_modules.items():
                try:
                    if module.is_supported(url):
                        platform_id = module_platform_id
                        platform_name = module.platform_name
                        processed_url = module.process_url(url)
                        self.log(f"使用{platform_name}平台模块处理链接: {url} -> {processed_url}")
                        module_processed = True
                        break
                except Exception as e:
                    self.log(f"平台模块处理URL时出错: {str(e)}")
            
            # 2. 如果平台模块未处理，使用传统检测和处理
            if not module_processed:
                # 抖音/TikTok处理
                if any(pattern in url for pattern in ['douyin.com', 'tiktok.com', 'v.douyin.com', 'www.tiktok.com']):
                    platform_name = "抖音"
                    platform_id = "douyin"
                    self.log(f"检测到抖音链接: {url}")
                    
                    # 处理抖音的各种链接格式
                    try:
                        if 'modal_id=' in url:
                            modal_id = url.split('modal_id=')[1].split('&')[0]
                            processed_url = f"https://www.douyin.com/video/{modal_id}"
                            self.log(f"已转换为标准格式: {processed_url}")
                        elif 'share/video/' in url:
                            # 处理分享链接
                            video_id = url.split('share/video/')[1].split('/')[0]
                            processed_url = f"https://www.douyin.com/video/{video_id}"
                            self.log(f"已转换为标准格式: {processed_url}")
                        elif 'video/' in url:
                            # 直接提取视频ID
                            parts = url.split('video/')
                            if len(parts) > 1:
                                video_id = parts[1].split('?')[0].split('/')[0]
                                processed_url = f"https://www.douyin.com/video/{video_id}"
                                self.log(f"已转换为标准格式: {processed_url}")
                        else:
                            processed_url = url
                    except Exception as e:
                        self.log(f"抖音URL处理失败: {str(e)}")
                        processed_url = url
                
                # B站处理
                elif any(pattern in url for pattern in ['bilibili.com', 'b23.tv']):
                    platform_name = "哔哩哔哩"
                    platform_id = "bilibili"
                    self.log(f"检测到B站链接: {url}")
                    
                    # 处理B站短链接
                    if 'b23.tv' in url:
                        try:
                            import requests
                            response = requests.head(url, allow_redirects=True, timeout=5)
                            if response.status_code == 200:
                                processed_url = response.url
                                self.log(f"已解析B站短链接: {processed_url}")
                            else:
                                processed_url = url
                                self.log(f"B站短链接解析失败，状态码: {response.status_code}")
                        except requests.exceptions.Timeout:
                            self.log(f"B站短链接解析超时，请检查网络连接")
                            processed_url = url
                        except requests.exceptions.ConnectionError:
                            self.log(f"B站短链接解析连接失败，请检查网络连接")
                            processed_url = url
                        except Exception as e:
                            self.log(f"解析B站短链接失败: {str(e)}")
                            processed_url = url
                    else:
                        processed_url = url
                
                # YouTube处理
                elif any(pattern in url for pattern in ['youtube.com', 'youtu.be']):
                    platform_name = "YouTube"
                    platform_id = "youtube"
                    self.log(f"检测到YouTube链接: {url}")
                    
                    # 处理YouTube短链接
                    try:
                        if 'youtu.be' in url:
                            video_id = url.split('youtu.be/')[1].split('?')[0]
                            processed_url = f"https://www.youtube.com/watch?v={video_id}"
                            self.log(f"已转换为标准格式: {processed_url}")
                        elif 'v=' in url:
                            # 处理普通YouTube链接
                            video_id = url.split('v=')[1].split('&')[0]
                            processed_url = f"https://www.youtube.com/watch?v={video_id}"
                            self.log(f"已转换为标准格式: {processed_url}")
                        else:
                            processed_url = url
                    except Exception as e:
                        self.log(f"YouTube URL处理失败: {str(e)}")
                        processed_url = url
                
                # 其他平台处理
                elif any(pattern in url for pattern in ['v.qq.com', 'qq.com/x/page']):
                    platform_name = "腾讯视频"
                    platform_id = "v.qq.com"
                    self.log(f"检测到腾讯视频链接: {url}")
                    processed_url = url
                elif 'iqiyi.com' in url:
                    platform_name = "爱奇艺"
                    platform_id = "iqiyi"
                    self.log(f"检测到爱奇艺链接: {url}")
                    processed_url = url
                elif 'youku.com' in url:
                    platform_name = "优酷"
                    platform_id = "youku"
                    self.log(f"检测到优酷链接: {url}")
                    processed_url = url
                elif 'weibo.com' in url and ('video' in url or 'status' in url):
                    platform_name = "微博"
                    platform_id = "weibo"
                    self.log(f"检测到微博视频链接: {url}")
                    processed_url = url
                elif any(pattern in url for pattern in ['kuaishou.com', 'kwai.com']):
                    platform_name = "快手"
                    platform_id = "kuaishou"
                    self.log(f"检测到快手链接: {url}")
                    processed_url = url
                else:
                    # 未知平台，保持原URL
                    processed_url = url
                    self.log(f"未知平台链接: {url}")
        
        except Exception as e:
            self.log(f"URL处理失败: {str(e)}")
            processed_url = url
        
        # 保存识别结果到实例变量
        self.current_platform = platform_name
        self.current_platform_id = platform_id
        
        return processed_url, platform_id
    
    def _get_ydl_opts_for_info(self, url, platform_id):
        """为获取视频信息设置yt-dlp选项，根据平台优化配置"""
        import os
        
        # 先尝试使用平台模块获取配置
        if platform_id in self.platform_modules:
            self.log(f"使用{self.platform_modules[platform_id].platform_name}平台模块的信息获取配置")
            return self.platform_modules[platform_id].get_ydl_opts_for_info(url)
        
        # 无对应模块时使用默认配置
        ydl_opts = {
            'quiet': True,
            'no_warnings': False,
            'extract_flat': False,
            # 设置合理的超时
            'socket_timeout': 30,
            # 重试次数
            'retries': 3,
            # 等待时间
            'sleep_interval': 5,
            # 重定向输出到空设备，避免'list' object has no attribute 'write'错误
            'outtmpl': os.devnull,
        }
        
        # 平台特定配置（传统方式）
        if platform_id == 'douyin':
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
        elif platform_id == 'bilibili':
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
        elif platform_id == 'youtube':
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
        elif platform_id in ['v.qq.com', 'iqiyi', 'youku', 'weibo', 'kuaishou']:
            ydl_opts.update({
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9',
                },
                'ignoreerrors': True,
                'no_check_certificate': True,
            })
        
        return ydl_opts
    
    def batch_download(self, urls):
        """批量下载视频"""
        total_urls = len(urls)
        success_count = 0
        failed_count = 0
        
        self.log(f"开始批量下载，共 {total_urls} 个视频")
        
        for index, url in enumerate(urls):
            if not self.downloading:
                self.log("批量下载已停止")
                break
            
            self.log(f"\n=== 开始下载第 {index + 1}/{total_urls} 个视频 ===")
            self.log(f"视频URL: {url}")
            
            try:
                import yt_dlp
                import requests
                
                # 处理URL
                processed_url, platform_id = self._process_url(url)
                
                # 获取视频信息
                self.log(f"正在获取视频信息: {processed_url}")
                self.status_label.config(text=f"正在获取第 {index + 1}/{total_urls} 个视频信息...")
                
                info_dict = None
                download_success = False
                
                try:
                    with yt_dlp.YoutubeDL(self._get_ydl_opts_for_info(processed_url, platform_id)) as ydl:
                        info_dict = ydl.extract_info(processed_url, download=False)
                except yt_dlp.utils.ExtractorError as e:
                    self.log(f"视频提取器错误: {str(e)}")
                    self.log("可能是链接无效或平台限制，请检查链接是否正确")
                    failed_count += 1
                    self.status_label.config(text=f"第 {index + 1}/{total_urls} 个视频提取失败")
                    # 添加到加密历史记录
                    self.add_to_history(
                        url=processed_url,
                        title="未知标题",
                        status="失败",
                        download_path=""
                    )
                    continue
                except yt_dlp.utils.DownloadError as e:
                    self.log(f"视频下载器错误: {str(e)}")
                    failed_count += 1
                    self.status_label.config(text=f"第 {index + 1}/{total_urls} 个视频下载器错误")
                    # 添加到加密历史记录
                    self.add_to_history(
                        url=processed_url,
                        title="未知标题",
                        status="失败",
                        download_path=""
                    )
                    continue
                except requests.exceptions.Timeout:
                    self.log("获取视频信息超时，请检查网络连接")
                    failed_count += 1
                    self.status_label.config(text=f"第 {index + 1}/{total_urls} 个视频信息获取超时")
                    # 添加到加密历史记录
                    self.add_to_history(
                        url=processed_url,
                        title="未知标题",
                        status="失败",
                        download_path=""
                    )
                    continue
                except requests.exceptions.ConnectionError:
                    self.log("获取视频信息连接失败，请检查网络连接")
                    failed_count += 1
                    self.status_label.config(text=f"第 {index + 1}/{total_urls} 个视频信息获取连接失败")
                    # 添加到加密历史记录
                    self.add_to_history(
                        url=processed_url,
                        title="未知标题",
                        status="失败",
                        download_path=""
                    )
                    continue
                except Exception as e:
                    self.log(f"获取视频信息失败: {str(e)}")
                    failed_count += 1
                    self.status_label.config(text=f"第 {index + 1}/{total_urls} 个视频信息获取失败")
                    # 添加到加密历史记录
                    self.add_to_history(
                        url=processed_url,
                        title="未知标题",
                        status="失败",
                        download_path=""
                    )
                    continue
                
                # 获取格式选择器
                try:
                    # 优先使用用户选择的视频质量
                    selected_quality = self.quality_var.get()
                    format_selector = self.quality_to_format.get(selected_quality, "bestvideo+bestaudio/best")
                    self.log(f"使用选择的质量: {selected_quality} (格式ID: {format_selector})")
                except Exception as e:
                    self.log(f"获取质量选择器失败: {str(e)}")
                    self.log("使用默认格式")
                    format_selector = "bestvideo+bestaudio/best"
                
                # 获取下载配置
                try:
                    if platform_id in self.platform_modules:
                        self.log(f"使用{self.platform_modules[platform_id].platform_name}平台模块的下载配置")
                        ydl_opts = self.platform_modules[platform_id].get_ydl_opts_for_download(format_selector, self.download_path)
                    else:
                        # 使用默认下载配置
                        ydl_opts = {
                            'format': format_selector,
                            'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
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
                except Exception as e:
                    self.log(f"获取下载配置失败: {str(e)}")
                    self.log("使用默认下载配置")
                    ydl_opts = {
                        'format': "bestvideo+bestaudio/best",
                        'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
                        'ignoreerrors': True,
                        'no_check_certificate': True,
                    }
                
                # 添加进度钩子
                def progress_hook(d):
                    if d['status'] == 'downloading':
                        percent = d.get('_percent_str', '0.0%').strip()
                        speed = d.get('_speed_str', '0 B/s').strip()
                        eta = d.get('_eta_str', 'N/A').strip()
                        self.status_label.config(text=f"正在下载第 {index + 1}/{total_urls} 个视频: {percent} | 速度: {speed} | 预计剩余: {eta}")
                        
                        # 更新进度条
                        if '_percent_str' in d:
                            try:
                                percent_float = float(d['_percent_str'].strip('%'))
                                self.progress_var.set(percent_float)
                            except:
                                pass
                    elif d['status'] == 'finished':
                        self.status_label.config(text=f"第 {index + 1}/{total_urls} 个视频下载完成，正在处理文件...")
                        self.progress_var.set(100)
                        
                        # 保存最后下载的文件路径
                        self.last_downloaded_file = d['filename']
                
                ydl_opts['progress_hooks'] = [progress_hook]
                
                # 执行下载
                self.log(f"开始下载视频: {info_dict.get('title', '未知标题')}")
                self.status_label.config(text=f"开始下载第 {index + 1}/{total_urls} 个视频...")
                
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([processed_url])
                except yt_dlp.utils.ExtractorError as e:
                    self.log(f"视频提取失败: {str(e)}")
                    self.log("可能是链接已失效或平台限制下载")
                    failed_count += 1
                    self.status_label.config(text=f"第 {index + 1}/{total_urls} 个视频提取失败")
                    # 添加到加密历史记录
                    self.add_to_history(
                        url=processed_url,
                        title=info_dict.get('title', '未知标题') if 'info_dict' in locals() else '未知标题',
                        status="失败",
                        download_path=""
                    )
                    continue
                except yt_dlp.utils.DownloadError as e:
                    self.log(f"视频下载失败: {str(e)}")
                    failed_count += 1
                    self.status_label.config(text=f"第 {index + 1}/{total_urls} 个视频下载失败")
                    # 添加到加密历史记录
                    self.add_to_history(
                        url=processed_url,
                        title=info_dict.get('title', '未知标题') if 'info_dict' in locals() else '未知标题',
                        status="失败",
                        download_path=""
                    )
                    continue
                except yt_dlp.utils.PostProcessingError as e:
                    self.log(f"视频后处理失败: {str(e)}")
                    self.log("可能是FFmpeg配置问题，请检查FFmpeg是否正确安装")
                    failed_count += 1
                    self.status_label.config(text=f"第 {index + 1}/{total_urls} 个视频后处理失败")
                    # 添加到加密历史记录
                    self.add_to_history(
                        url=processed_url,
                        title=info_dict.get('title', '未知标题') if 'info_dict' in locals() else '未知标题',
                        status="失败",
                        download_path=""
                    )
                    continue
                except requests.exceptions.Timeout:
                    self.log("视频下载超时，请检查网络连接或尝试使用断点续传")
                    failed_count += 1
                    self.status_label.config(text=f"第 {index + 1}/{total_urls} 个视频下载超时")
                    # 添加到加密历史记录
                    self.add_to_history(
                        url=processed_url,
                        title=info_dict.get('title', '未知标题') if 'info_dict' in locals() else '未知标题',
                        status="失败",
                        download_path=""
                    )
                    continue
                except requests.exceptions.ConnectionError:
                    self.log("视频下载连接失败，请检查网络连接")
                    failed_count += 1
                    self.status_label.config(text=f"第 {index + 1}/{total_urls} 个视频下载连接失败")
                    # 添加到加密历史记录
                    self.add_to_history(
                        url=processed_url,
                        title=info_dict.get('title', '未知标题') if 'info_dict' in locals() else '未知标题',
                        status="失败",
                        download_path=""
                    )
                    continue
                except OSError as e:
                    self.log(f"文件系统错误: {str(e)}")
                    self.log("可能是磁盘空间不足或权限问题")
                    failed_count += 1
                    self.status_label.config(text=f"第 {index + 1}/{total_urls} 个视频文件系统错误")
                    # 添加到加密历史记录
                    self.add_to_history(
                        url=processed_url,
                        title=info_dict.get('title', '未知标题') if 'info_dict' in locals() else '未知标题',
                        status="失败",
                        download_path=""
                    )
                    continue
                
                self.log(f"视频下载完成: {info_dict.get('title', '未知标题')}")
                success_count += 1
                self.status_label.config(text=f"第 {index + 1}/{total_urls} 个视频下载成功")
                
                # 添加到加密历史记录
                self.add_to_history(
                    url=processed_url,
                    title=info_dict.get('title', '未知标题'),
                    status="成功",
                    download_path=self.last_downloaded_file if hasattr(self, 'last_downloaded_file') else ""
                )
                
            except ImportError as e:
                self.log(f"依赖库缺失: {str(e)}")
                self.log("请点击'安装依赖'按钮安装所有必要的依赖库")
                failed_count += 1
                self.status_label.config(text=f"第 {index + 1}/{total_urls} 个视频依赖缺失")
            except Exception as e:
                self.log(f"下载失败: {str(e)}")
                self.log("这是一个未预期的错误，请检查日志获取更多信息")
                failed_count += 1
                self.status_label.config(text=f"第 {index + 1}/{total_urls} 个视频下载失败")
            finally:
                # 重置进度条
                self.progress_var.set(0)
        
        # 批量下载完成
        self.log(f"\n=== 批量下载完成 ===")
        self.log(f"总共: {total_urls} 个视频")
        self.log(f"成功: {success_count} 个视频")
        self.log(f"失败: {failed_count} 个视频")
        
        # 更新UI状态
        self.downloading = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="批量下载完成")
        
        # 显示批量下载结果
        result_msg = f"批量下载完成！\n\n总共: {total_urls} 个视频\n成功: {success_count} 个视频\n失败: {failed_count} 个视频"
        messagebox.showinfo("批量下载完成", result_msg)
    
    def copy_video_info(self):
        """复制视频信息到剪贴板"""
        try:
            # 获取文本内容
            info_text = self.info_text.get(1.0, tk.END).strip()
            if not info_text:
                messagebox.showinfo("提示", "没有可复制的视频信息")
                return
            
            # 复制到剪贴板
            self.root.clipboard_clear()
            self.root.clipboard_append(info_text)
            self.root.update()  # 确保数据被真正复制
            
            self.log("视频信息已复制到剪贴板")
            messagebox.showinfo("成功", "视频信息已复制到剪贴板")
        except Exception as e:
            error_msg = f"复制视频信息失败: {str(e)}"
            self.log(error_msg)
            messagebox.showerror("复制失败", error_msg)
    
    def get_video_info(self):
        """获取视频信息并显示在预览区域"""
        # 获取URL
        if self.batch_mode.get():
            # 批量模式下获取第一个非空URL
            batch_text = self.batch_url_text.get(1.0, tk.END).strip()
            if not batch_text:
                messagebox.showerror("错误", "请输入视频URL")
                return
            urls = [line.strip() for line in batch_text.split('\n') if line.strip()]
            if not urls:
                messagebox.showerror("错误", "请输入有效的视频URL")
                return
            url = urls[0]
        else:
            # 单条模式
            url = self.url_entry.get().strip()
            if not url:
                messagebox.showerror("错误", "请输入视频URL")
                return
        
        # 清空之前的信息
        self.info_text.configure(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.configure(state=tk.DISABLED)
        
        try:
            import yt_dlp
            import requests
            
            # 处理URL
            processed_url, platform_id = self._process_url(url)
            
            # 获取视频信息
            self.log(f"正在获取视频信息: {processed_url}")
            self.status_label.config(text="正在获取视频信息...")
            
            try:
                with yt_dlp.YoutubeDL(self._get_ydl_opts_for_info(processed_url, platform_id)) as ydl:
                    info_dict = ydl.extract_info(processed_url, download=False)
            except yt_dlp.utils.ExtractorError as e:
                error_msg = f"视频提取器错误: {str(e)}"
                self.log(error_msg)
                self.log("可能是链接无效或平台限制，请检查链接是否正确")
                self.status_label.config(text="视频提取失败")
                # 提供更详细的错误信息和解决方案
                if "unable to extract" in str(e).lower():
                    error_msg += "\n\n可能原因: URL格式不正确或平台更新了页面结构。\n解决方案: 请检查URL是否正确，或尝试更新yt-dlp版本。"
                elif "no video formats found" in str(e).lower():
                    error_msg += "\n\n可能原因: 视频可能是付费内容或已被删除。\n解决方案: 请确认视频可正常访问。"
                messagebox.showerror("视频提取失败", error_msg)
                return
            except yt_dlp.utils.DownloadError as e:
                error_msg = f"视频下载器错误: {str(e)}"
                self.log(error_msg)
                self.status_label.config(text="视频下载器错误")
                # 提供更详细的错误信息和解决方案
                if "403 forbidden" in str(e).lower():
                    error_msg += "\n\n可能原因: 访问被拒绝，可能需要登录或Cookie验证。\n解决方案: 请检查是否需要登录，或尝试更新yt-dlp配置。"
                elif "404 not found" in str(e).lower():
                    error_msg += "\n\n可能原因: 视频或页面不存在。\n解决方案: 请检查URL是否正确。"
                messagebox.showerror("视频下载器错误", error_msg)
                return
            except yt_dlp.utils.PostProcessingError as e:
                error_msg = f"视频后处理失败: {str(e)}"
                self.log(error_msg)
                self.status_label.config(text="视频后处理失败")
                error_msg += "\n\n可能原因: FFmpeg配置问题。\n解决方案: 请检查FFmpeg是否正确安装并添加到系统路径。"
                messagebox.showerror("视频后处理失败", error_msg)
                return
            except requests.exceptions.Timeout as e:
                error_msg = "获取视频信息超时"
                self.log(f"{error_msg}: {str(e)}")
                self.status_label.config(text=error_msg)
                error_msg += "\n\n可能原因: 网络连接不稳定或服务器响应缓慢。\n解决方案: 请检查网络连接，或稍后重试。"
                messagebox.showerror(error_msg, error_msg + "，请检查网络连接")
                return
            except requests.exceptions.ConnectionError as e:
                error_msg = "获取视频信息连接失败"
                self.log(f"{error_msg}: {str(e)}")
                self.status_label.config(text=error_msg)
                error_msg += "\n\n可能原因: 网络连接中断或服务器不可达。\n解决方案: 请检查网络连接，或确认视频平台是否可正常访问。"
                messagebox.showerror(error_msg, error_msg + "，请检查网络连接")
                return
            except requests.exceptions.RequestException as e:
                error_msg = f"网络请求错误: {str(e)}"
                self.log(error_msg)
                self.status_label.config(text="网络请求错误")
                error_msg += "\n\n可能原因: 网络配置问题或服务器错误。\n解决方案: 请检查网络连接，或稍后重试。"
                messagebox.showerror("网络请求错误", error_msg)
                return
            except Exception as e:
                error_msg = f"获取视频信息失败: {str(e)}"
                self.log(error_msg)
                self.status_label.config(text="获取视频信息失败")
                # 捕获其他所有异常，提供通用解决方案
                error_msg += "\n\n可能原因: 未知错误。\n解决方案: 请检查URL是否正确，网络连接是否正常，或尝试更新应用程序。"
                messagebox.showerror("获取视频信息失败", error_msg)
                return
            
            # 格式化显示视频信息
            self.log("视频信息获取成功")
            self.status_label.config(text="视频信息获取成功")
            
            # 解析视频信息
            title = info_dict.get('title', '未知标题')
            uploader = info_dict.get('uploader', '未知上传者')
            upload_date = info_dict.get('upload_date', '未知日期')
            if upload_date and len(upload_date) == 8:
                upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
            duration = info_dict.get('duration', 0)
            minutes, seconds = divmod(duration, 60)
            hours, minutes = divmod(minutes, 60)
            duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours > 0 else f"{minutes:02d}:{seconds:02d}"
            
            # 获取最佳质量
            formats = info_dict.get('formats', [])
            best_format = max(formats, key=lambda f: f.get('height', 0) if f.get('height') is not None else 0, default={})
            quality = f"{best_format.get('height', 0)}p" if best_format.get('height') else "未知质量"
            
            # 提取并填充可用质量选项
            self.available_qualities = ["自动推荐最佳质量"]
            self.quality_to_format = {"自动推荐最佳质量": "bestvideo+bestaudio/best"}
            
            # 过滤出有视频流的格式
            video_formats = [fmt for fmt in formats if fmt.get('vcodec') and fmt.get('vcodec') != 'none']
            
            # 按高度和比特率排序，去重并获取不同质量
            unique_heights = {}
            for fmt in video_formats:
                height = fmt.get('height')
                # 确保height是有效数值且大于0
                if height is not None and isinstance(height, (int, float)) and height > 0:
                    current_tbr = fmt.get('tbr', 0)
                    current_tbr = current_tbr if current_tbr is not None else 0
                    existing_tbr = unique_heights[height].get('tbr', 0) if height in unique_heights else 0
                    existing_tbr = existing_tbr if existing_tbr is not None else 0
                    if height not in unique_heights or current_tbr > existing_tbr:
                        unique_heights[height] = fmt
            
            # 将质量选项添加到下拉菜单
            sorted_heights = sorted(unique_heights.keys(), reverse=True)
            for height in sorted_heights:
                fmt = unique_heights[height]
                quality_name = f"{height}p"
                format_id = str(fmt.get('format_id', ''))
                self.available_qualities.append(quality_name)
                self.quality_to_format[quality_name] = format_id
            
            # 更新下拉菜单
            self.quality_combo['values'] = self.available_qualities
            # 默认选择最佳质量
            if sorted_heights:
                best_quality = f"{max(sorted_heights)}p"
                self.quality_var.set(best_quality)
            
            # 播放列表信息
            playlist_count = info_dict.get('playlist_count', None)
            
            # 组装信息文本
            # 组装信息文本，优化格式和布局
            info_text = "=" * 60 + "\n"
            info_text += f"🎬 视频标题: {title}\n"
            info_text += "=" * 60 + "\n"
            info_text += f"📺 平台: {self.current_platform}\n"
            info_text += f"👤 上传者: {uploader}\n"
            info_text += f"📅 上传日期: {upload_date}\n"
            info_text += f"⏱️ 时长: {duration_str}\n"
            info_text += f"📊 最佳质量: {quality}\n"
            info_text += f"🔗 视频URL: {processed_url}\n"
            
            if playlist_count:
                info_text += f"📋 播放列表包含: {playlist_count} 个视频\n"
            
            # 显示更多详细信息，添加分隔线和更好的布局
            info_text += "\n" + "=" * 60 + "\n"
            info_text += "📋 视频详情\n"
            info_text += "=" * 60 + "\n"
            
            if 'description' in info_dict and info_dict['description']:
                desc = info_dict['description']
                # 换行处理，每80个字符换行
                wrapped_desc = []
                for i in range(0, len(desc), 80):
                    wrapped_desc.append(desc[i:i+80])
                desc = "\n      ".join(wrapped_desc)
                if len(info_dict['description']) > 400:
                    desc += "..."
                info_text += f"描述: {desc}\n"
            
            stats = []
            if 'view_count' in info_dict:
                stats.append(f"播放量: {info_dict['view_count']:,}")
            if 'like_count' in info_dict:
                stats.append(f"点赞数: {info_dict['like_count']:,}")
            if 'comment_count' in info_dict:
                stats.append(f"评论数: {info_dict['comment_count']:,}")
            if 'favorite_count' in info_dict:
                stats.append(f"收藏数: {info_dict['favorite_count']:,}")
            if 'repost_count' in info_dict:
                stats.append(f"转发数: {info_dict['repost_count']:,}")
            
            if stats:
                info_text += "\n互动数据:\n"
                for stat in stats:
                    info_text += f"  {stat}\n"
            
            # 视频技术信息
            info_text += "\n" + "=" * 60 + "\n"
            info_text += "⚙️ 技术参数\n"
            info_text += "=" * 60 + "\n"
            
            # 分辨率信息
            if best_format.get('width') and best_format.get('height'):
                resolution = f"{best_format['width']}x{best_format['height']}"
                info_text += f"分辨率: {resolution}\n"
            
            # 视频编码格式
            if best_format.get('vcodec') and best_format['vcodec'] != 'none':
                video_codec = best_format['vcodec'].split('.')[0] if '.' in best_format['vcodec'] else best_format['vcodec']
                info_text += f"视频编码: {video_codec}\n"
            
            # 音频编码格式
            # 查找最佳音频格式
            best_audio_format = max(formats, key=lambda f: f.get('abr', 0) if f.get('abr') is not None else 0, default={})
            if best_audio_format.get('acodec') and best_audio_format['acodec'] != 'none':
                audio_codec = best_audio_format['acodec'].split('.')[0] if '.' in best_audio_format['acodec'] else best_audio_format['acodec']
                info_text += f"音频编码: {audio_codec}\n"
            
            # 音频比特率
            if best_audio_format.get('abr'):
                audio_bitrate = f"{best_audio_format['abr']} Kbps"
                info_text += f"音频比特率: {audio_bitrate}\n"
            
            # 文件大小信息
            if 'filesize_approx' in info_dict:
                filesize = info_dict['filesize_approx']
                if filesize < 1024 * 1024:
                    filesize_str = f"{filesize / 1024:.1f} KB"
                elif filesize < 1024 * 1024 * 1024:
                    filesize_str = f"{filesize / (1024 * 1024):.1f} MB"
                else:
                    filesize_str = f"{filesize / (1024 * 1024 * 1024):.1f} GB"
                info_text += f"预计文件大小: {filesize_str}\n"
            
            # 文件扩展名
            if best_format.get('ext'):
                info_text += f"文件格式: {best_format['ext']}\n"
            
            # 显示可用格式
            if formats:
                info_text += "\n📱 可用视频格式 (前5种):\n"
                # 过滤重复的高度和格式
                unique_formats = {}
                for fmt in formats:
                    height = fmt.get('height')
                    ext = fmt.get('ext')
                    # 确保height是数值类型且ext存在
                    if isinstance(height, (int, float)) and ext:
                        key = (height, ext)
                        if key not in unique_formats:
                            unique_formats[key] = fmt
                
                # 按高度排序
                sorted_formats = sorted(unique_formats.values(), key=lambda f: f.get('height', 0) if f.get('height') is not None else 0, reverse=True)
                
                for i, fmt in enumerate(sorted_formats[:5]):
                    height = fmt.get('height', 0)
                    ext = fmt.get('ext', '未知格式')
                    bitrate = fmt.get('tbr', 0) / 1000 if fmt.get('tbr') else 0
                    info_text += f"  • {height}p .{ext} ({bitrate:.1f} Mbps)\n"
            
            # 显示字幕信息
            if 'subtitles' in info_dict:
                info_text += "\n📝 可用字幕:\n"
                subtitle_list = [f"  • {lang}" for lang, sub_list in info_dict['subtitles'].items()]
                info_text += "\n".join(subtitle_list) + "\n"
            
            # 显示自动生成字幕信息
            if 'automatic_captions' in info_dict:
                info_text += "\n🤖 可用自动生成字幕:\n"
                caption_list = [f"  • {lang}" for lang, sub_list in info_dict['automatic_captions'].items()]
                info_text += "\n".join(caption_list) + "\n"
            
            info_text += "\n" + "=" * 60 + "\n"
            
            # 显示信息
            self.info_text.configure(state=tk.NORMAL)
            self.info_text.insert(tk.END, info_text)
            self.info_text.configure(state=tk.DISABLED)
            
            messagebox.showinfo("成功", "视频信息获取完成！")
            
        except ImportError as e:
            self.log(f"依赖库缺失: {str(e)}")
            self.log("请点击'安装依赖'按钮安装所有必要的依赖库")
            self.status_label.config(text="依赖缺失")
            messagebox.showerror("错误", f"依赖库缺失: {str(e)}")
        except Exception as e:
            self.log(f"获取视频信息失败: {str(e)}")
            self.log("这是一个未预期的错误，请检查日志获取更多信息")
            self.status_label.config(text="获取视频信息失败")
            messagebox.showerror("错误", f"获取视频信息失败: {str(e)}")
        finally:
            self.status_label.config(text="就绪")
    
    def download(self, url):
        """下载单个视频的主函数"""
        try:
            import yt_dlp
            import requests
            
            # 处理URL
            processed_url, platform_id = self._process_url(url)
            
            # 获取视频信息
            self.log(f"正在获取视频信息: {processed_url}")
            self.status_label.config(text="正在获取视频信息...")
            
            try:
                with yt_dlp.YoutubeDL(self._get_ydl_opts_for_info(processed_url, platform_id)) as ydl:
                    info_dict = ydl.extract_info(processed_url, download=False)
            except yt_dlp.utils.ExtractorError as e:
                self.log(f"视频提取器错误: {str(e)}")
                self.log("可能是链接无效或平台限制，请检查链接是否正确")
                self.status_label.config(text="视频提取失败")
                messagebox.showerror("错误", "视频提取器错误: 可能是链接无效或平台限制，请检查链接是否正确")
                return
            except yt_dlp.utils.DownloadError as e:
                self.log(f"视频下载器错误: {str(e)}")
                self.status_label.config(text="视频下载器错误")
                messagebox.showerror("错误", f"视频下载器错误: {str(e)}")
                return
            except requests.exceptions.Timeout:
                self.log("获取视频信息超时，请检查网络连接")
                self.status_label.config(text="获取视频信息超时")
                messagebox.showerror("错误", "获取视频信息超时，请检查网络连接")
                return
            except requests.exceptions.ConnectionError:
                self.log("获取视频信息连接失败，请检查网络连接")
                self.status_label.config(text="获取视频信息连接失败")
                messagebox.showerror("错误", "获取视频信息连接失败，请检查网络连接")
                return
            except Exception as e:
                self.log(f"获取视频信息失败: {str(e)}")
                self.status_label.config(text="获取视频信息失败")
                messagebox.showerror("错误", f"获取视频信息失败: {str(e)}")
                return
            
            # 获取格式选择器
            try:
                format_selector = next(opt[1] for opt in self.format_options if opt[0] == self.format_var.get())
            except StopIteration:
                self.log("无效的格式选择器，使用默认格式")
                format_selector = "bestvideo+bestaudio/best"
            
            # 获取下载配置
            try:
                if platform_id in self.platform_modules:
                    self.log(f"使用{self.platform_modules[platform_id].platform_name}平台模块的下载配置")
                    ydl_opts = self.platform_modules[platform_id].get_ydl_opts_for_download(format_selector, self.download_path)
                else:
                    # 使用默认下载配置
                    ydl_opts = {
                        'format': format_selector,
                        'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
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
            except Exception as e:
                self.log(f"获取下载配置失败: {str(e)}")
                self.log("使用默认下载配置")
                ydl_opts = {
                    'format': "bestvideo+bestaudio/best",
                    'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
                    'ignoreerrors': True,
                    'no_check_certificate': True,
                }
            
            # 添加进度钩子
            def progress_hook(d):
                if d['status'] == 'downloading':
                    percent = d.get('_percent_str', '0.0%').strip()
                    speed = d.get('_speed_str', '0 B/s').strip()
                    eta = d.get('_eta_str', 'N/A').strip()
                    self.status_label.config(text=f"正在下载: {percent} | 速度: {speed} | 预计剩余: {eta}")
                    
                    # 更新进度条
                    if '_percent_str' in d:
                        try:
                            percent_float = float(d['_percent_str'].strip('%'))
                            self.progress_var.set(percent_float)
                        except:
                            pass
                elif d['status'] == 'finished':
                    self.status_label.config(text="下载完成，正在处理文件...")
                    self.progress_var.set(100)
                    
                    # 保存最后下载的文件路径
                    self.last_downloaded_file = d['filename']
            
            ydl_opts['progress_hooks'] = [progress_hook]
            
            # 执行下载
            self.log(f"开始下载视频: {info_dict.get('title', '未知标题')}")
            self.status_label.config(text="开始下载视频...")
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([processed_url])
            except yt_dlp.utils.ExtractorError as e:
                self.log(f"视频提取失败: {str(e)}")
                self.log("可能是链接已失效或平台限制下载")
                self.status_label.config(text="视频提取失败")
                messagebox.showerror("错误", "视频提取失败: 可能是链接已失效或平台限制下载")
                return
            except yt_dlp.utils.DownloadError as e:
                self.log(f"视频下载失败: {str(e)}")
                self.status_label.config(text="视频下载失败")
                messagebox.showerror("错误", f"视频下载失败: {str(e)}")
                return
            except yt_dlp.utils.PostProcessingError as e:
                self.log(f"视频后处理失败: {str(e)}")
                self.log("可能是FFmpeg配置问题，请检查FFmpeg是否正确安装")
                self.status_label.config(text="视频后处理失败")
                messagebox.showerror("错误", "视频后处理失败: 可能是FFmpeg配置问题，请检查FFmpeg是否正确安装")
                return
            except requests.exceptions.Timeout:
                self.log("视频下载超时，请检查网络连接或尝试使用断点续传")
                self.status_label.config(text="视频下载超时")
                messagebox.showerror("错误", "视频下载超时，请检查网络连接或尝试使用断点续传")
                return
            except requests.exceptions.ConnectionError:
                self.log("视频下载连接失败，请检查网络连接")
                self.status_label.config(text="视频下载连接失败")
                messagebox.showerror("错误", "视频下载连接失败，请检查网络连接")
                return
            except OSError as e:
                self.log(f"文件系统错误: {str(e)}")
                self.log("可能是磁盘空间不足或权限问题")
                self.status_label.config(text="文件系统错误")
                messagebox.showerror("错误", f"文件系统错误: {str(e)}")
                return
            
            self.log(f"视频下载完成: {info_dict.get('title', '未知标题')}")
            self.status_label.config(text="下载完成")
            messagebox.showinfo("成功", "视频下载完成！")
            
            # 添加到加密历史记录
            self.add_to_history(
                url=processed_url,
                title=info_dict.get('title', '未知标题'),
                status="成功",
                download_path=self.last_downloaded_file if hasattr(self, 'last_downloaded_file') else ""
            )
            
        except ImportError as e:
            self.log(f"依赖库缺失: {str(e)}")
            self.log("请点击'安装依赖'按钮安装所有必要的依赖库")
            self.status_label.config(text="依赖缺失")
            messagebox.showerror("错误", f"依赖库缺失: {str(e)}")
        except Exception as e:
            self.log(f"下载失败: {str(e)}")
            self.log("这是一个未预期的错误，请检查日志获取更多信息")
            self.status_label.config(text="下载失败")
            messagebox.showerror("错误", f"下载失败: {str(e)}")
            
            # 添加到加密历史记录
            if 'processed_url' in locals() and 'info_dict' in locals():
                self.add_to_history(
                    url=processed_url,
                    title=info_dict.get('title', '未知标题'),
                    status="失败",
                    download_path=""
                )
        finally:
            self.downloading = False
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.progress_var.set(0)
    
    def on_closing(self):
        """窗口关闭时的处理"""
        if self.downloading:
            if messagebox.askyesno("确认", "正在下载中，确定要关闭吗？"):
                self.stop_download()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def install_dependencies(self):
        """安装必要的依赖"""
        try:
            # 安装yt-dlp
            subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
            self.log("✓ yt-dlp 安装成功")
            
            # 安装系统托盘和通知相关依赖
            self.log("开始安装系统托盘和通知相关依赖...")
            
            # 安装pystray（跨平台系统托盘支持）
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "pystray", "pillow"])
                self.log("✓ pystray 和 pillow 安装成功")
            except subprocess.CalledProcessError:
                self.log("✗ pystray 安装失败，系统托盘功能可能受限")
            
            # 在Windows平台安装win10toast
            if platform.system() == 'Windows':
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "win10toast"])
                    self.log("✓ win10toast 安装成功")
                except subprocess.CalledProcessError:
                    self.log("✗ win10toast 安装失败，Windows通知功能可能受限")
                    
            self.log("所有依赖安装完成，请重启程序以应用更改")
            
        except subprocess.CalledProcessError:
            self.log("✗ yt-dlp 安装失败，请手动运行: pip install yt-dlp")
            messagebox.showerror("错误", "无法自动安装yt-dlp，请手动运行以下命令：\npip install yt-dlp")
    
    def check_ffmpeg(self):
        """检查FFmpeg是否可用"""
        try:
            # 尝试执行ffmpeg命令
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            self.ffmpeg_available = True
            self.log("✓ FFmpeg 已安装，支持视频格式转换功能")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.ffmpeg_available = False
            self.log("✗ FFmpeg 未找到，请安装FFmpeg以使用视频格式转换功能")
            self.log("提示: 您可以点击'安装FFmpeg'按钮自动安装，或从 https://ffmpeg.org/download.html 手动下载")
            return False
    
    def install_ffmpeg(self):
        """自动下载和安装FFmpeg"""
        self.log("开始自动安装FFmpeg...")
        
        # 创建一个线程来执行安装，避免阻塞UI
        def _install_ffmpeg_thread():
            try:
                import requests
                import zipfile
                import tempfile
                import shutil
                
                # 更新状态
                def update_status(msg):
                    self.log(msg)
                
                update_status("正在下载FFmpeg...")
                
                # 根据平台下载不同版本
                if platform.system() == "Windows":
                    # Windows版本下载地址
                    url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
                    extract_folder = "ffmpeg-master-latest-win64-gpl"
                elif platform.system() == "Darwin":
                    # macOS版本下载地址
                    url = "https://evermeet.cx/ffmpeg/ffmpeg-7.0.2.zip"
                    extract_folder = ""
                else:
                    # Linux版本，提示用户手动安装
                    self.log("✗ Linux系统暂不支持自动安装FFmpeg，请使用包管理器手动安装")
                    messagebox.showwarning("提示", "Linux系统暂不支持自动安装FFmpeg，请使用包管理器手动安装")
                    return
                
                # 下载文件
                response = requests.get(url, stream=True)
                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
                    temp_path = temp_file.name
                    
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            temp_file.write(chunk)
                            downloaded_size += len(chunk)
                            progress = (downloaded_size / total_size) * 100
                            update_status(f"下载进度: {progress:.1f}%")
                
                update_status("FFmpeg下载完成，正在解压...")
                
                # 解压文件
                with tempfile.TemporaryDirectory() as extract_dir:
                    with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                    
                    # 找到FFmpeg可执行文件
                    if platform.system() == "Windows":
                        ffmpeg_path = os.path.join(extract_dir, extract_folder, "bin")
                        # 将bin目录添加到系统PATH
                        os.environ["PATH"] += os.pathsep + ffmpeg_path
                        # 复制到程序目录
                        program_dir = os.path.dirname(os.path.abspath(__file__))
                        for exe in ["ffmpeg.exe", "ffprobe.exe", "ffplay.exe"]:
                            src = os.path.join(ffmpeg_path, exe)
                            dst = os.path.join(program_dir, exe)
                            if os.path.exists(src):
                                shutil.copy2(src, dst)
                                update_status(f"已复制 {exe} 到程序目录")
                    elif platform.system() == "Darwin":
                        ffmpeg_path = os.path.join(extract_dir, "ffmpeg")
                        # 复制到/usr/local/bin
                        shutil.copy2(ffmpeg_path, "/usr/local/bin/ffmpeg")
                        update_status("已复制 ffmpeg 到 /usr/local/bin")
                
                # 清理临时文件
                os.unlink(temp_path)
                
                update_status("FFmpeg安装完成")
                self.log("✓ FFmpeg 安装成功")
                
                # 重新检查FFmpeg
                if self.check_ffmpeg():
                    messagebox.showinfo("成功", "FFmpeg安装完成！")
                else:
                    messagebox.showerror("错误", "FFmpeg安装失败，请手动安装")
                    
            except Exception as e:
                self.log(f"✗ FFmpeg安装失败: {str(e)}")
                messagebox.showerror("错误", f"FFmpeg安装失败: {str(e)}")
        
        # 启动安装线程
        threading.Thread(target=_install_ffmpeg_thread, daemon=True).start()
    
    def toggle_convert_options(self):
        """切换格式转换选项"""
        # 这个方法可以根据需要扩展
        pass

def main():
    """主函数"""
    root = tk.Tk()
    app = VideoDownloader(root)
    root.mainloop()

if __name__ == "__main__":
    main()
