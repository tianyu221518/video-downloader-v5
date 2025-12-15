#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频下载工具 - 打包脚本
将Python程序打包成独立的可执行文件
"""

import os
import sys
import subprocess
import shutil

def install_pyinstaller():
    """安装PyInstaller"""
    print("正在安装PyInstaller...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller安装成功")
        return True
    except subprocess.CalledProcessError:
        print("✗ PyInstaller安装失败")
        return False

def create_spec_file():
    """创建PyInstaller规格文件"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['tkinter', 'tkinter.ttk', 'tkinter.messagebox', 
                  'tkinter.filedialog', 'tkinter.scrolledtext',
                  'yt_dlp', 'yt_dlp.extractor', 'yt_dlp.downloader',
                  'yt_dlp.postprocessor', 'requests'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='视频下载工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
    onefile=True,  # 生成单一可执行文件
)
'''
    
    with open('视频下载工具.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print("✓ 规格文件创建成功")

def build_executable():
    """构建可执行文件"""
    print("开始打包程序...")
    print("这可能需要几分钟时间，请耐心等待...")
    
    try:
        # 清理之前的构建
        if os.path.exists('build'):
            shutil.rmtree('build')
        if os.path.exists('dist'):
            shutil.rmtree('dist')
        
        # 直接使用命令行参数进行打包，确保onefile模式
        subprocess.check_call([sys.executable, '-m', 'PyInstaller', 
                              '--clean', '--onefile', 
                              '--windowed',  # 无控制台窗口
                              '--name', '视频下载工具',
                              '--hidden-import', 'tkinter',
                              '--hidden-import', 'tkinter.ttk',
                              '--hidden-import', 'tkinter.messagebox',
                              '--hidden-import', 'tkinter.filedialog',
                              '--hidden-import', 'tkinter.scrolledtext',
                              '--hidden-import', 'yt_dlp',
                              '--hidden-import', 'yt_dlp.extractor',
                              '--hidden-import', 'yt_dlp.downloader',
                              '--hidden-import', 'yt_dlp.postprocessor',
                              '--hidden-import', 'requests',
                              'main.py'])
        
        print("✓ 程序打包成功！")
        print(f"可执行文件位置: {os.path.abspath('dist/视频下载工具.exe')}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ 打包失败: {e}")
        return False

def create_portable_package():
    """创建便携版包"""
    print("正在创建便携版包...")
    
    # 创建便携版目录
    portable_dir = "视频下载工具_便携版"
    if os.path.exists(portable_dir):
        shutil.rmtree(portable_dir)
    
    os.makedirs(portable_dir)
    
    # 复制单一可执行文件
    if os.path.exists('dist/视频下载工具.exe'):
        shutil.copy('dist/视频下载工具.exe', portable_dir)
    
    # 复制使用说明
    if os.path.exists('使用说明.txt'):
        shutil.copy('使用说明.txt', portable_dir)
    
    # 创建说明文件
    readme_content = """视频下载工具 - 单一可执行文件便携版

【使用方法】
直接双击"视频下载工具.exe"运行程序

【注意事项】
- 这是单一可执行文件版本，无需安装Python环境
- 首次运行可能需要一些时间解压临时文件
- 下载的视频将保存在程序所在目录
- 程序完全独立，可直接分享给他人使用

【更新说明】
- 采用onefile模式打包，仅需一个EXE文件
- 包含所有必要的依赖和库
- 优化了抖音链接的支持

版本：v1.0.1
"""
    
    with open(f'{portable_dir}/使用说明.txt', 'w', encoding='utf-8') as f:
        # 如果原有使用说明存在，保留它，否则使用新内容
        if not os.path.exists('使用说明.txt'):
            f.write(readme_content)
        else:
            # 读取并添加版本信息
            with open('使用说明.txt', 'r', encoding='utf-8') as original:
                original_content = original.read()
                # 检查是否已有版本信息，如果没有则添加
                if "版本：" not in original_content:
                    f.write(original_content + "\n\n版本：v1.0.1\n")
                else:
                    f.write(original_content)
    
    print(f"✓ 便携版创建完成: {os.path.abspath(portable_dir)}")
    print("✓ 现在您可以直接分享视频下载工具.exe文件给他人使用")

def main():
    """主函数"""
    print("=" * 50)
    print("    视频下载工具 - 打包程序")
    print("=" * 50)
    print("模式：单一可执行文件")
    print()
    
    # 检查当前目录
    if not os.path.exists('main.py'):
        print("✗ 错误: 未找到main.py文件")
        print("请在项目根目录运行此脚本")
        input("按回车键退出...")
        return
    
    # 安装PyInstaller
    if not install_pyinstaller():
        input("按回车键退出...")
        return
    
    # 不再创建规格文件，直接使用命令行参数
    # create_spec_file()
    
    # 构建可执行文件
    if not build_executable():
        input("按回车键退出...")
        return
    
    # 创建便携版包
    create_portable_package()
    
    print()
    print("=" * 50)
    print("打包完成！")
    print("=" * 50)
    print(f"单一可执行文件: {os.path.abspath('dist/视频下载工具.exe')}")
    print(f"便携版目录: {os.path.abspath('视频下载工具_便携版')}")
    print()
    print("🎉 现在您可以:")
    print("1. 直接分享dist目录下的视频下载工具.exe文件")
    print("2. 无需额外文件，双击即可使用")
    print("3. 其他用户无需安装Python环境")
    print("4. 程序已包含所有必要的依赖库")
    print()
    print("💡 提示：")
    print("- 首次运行可能需要稍长时间加载")
    print("- 建议将exe文件放在非系统盘运行")
    print()
    
    input("按回车键退出...")

if __name__ == "__main__":
    main()
