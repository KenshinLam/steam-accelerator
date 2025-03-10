#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""游戏加速器主程序"""

import logging
import os
import sys
import ctypes
from pathlib import Path

def is_admin():
    """检查是否具有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def request_admin():
    """请求管理员权限"""
    if not is_admin():
        # 使用Python执行器重启脚本
        python_exe = sys.executable
        script_path = os.path.abspath(__file__)
        
        ctypes.windll.shell32.ShellExecuteW(
            None, 
            "runas", 
            python_exe,
            f'"{script_path}"',
            None, 
            1
        )
        return True
    return False

def setup_environment():
    """设置运行环境"""
    # 将项目根目录添加到Python路径
    root_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(root_dir))
    
    # 设置工作目录
    os.chdir(root_dir)
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('accelerator.log', encoding='utf-8', mode='w'),
            logging.StreamHandler()
        ]
    )

def main():
    """程序入口"""
    try:
        # 检查管理员权限
        if not is_admin():
            logging.info("正在请求管理员权限...")
            if request_admin():
                return
            
        setup_environment()
        logging.info("启动游戏加速器...")
        
        # 导入UI模块并启动
        from src.ui import MainWindow
        app = MainWindow()
        app.run()
        
    except Exception as e:
        logging.error(f"程序启动失败: {str(e)}")
        input("按回车键退出...")

if __name__ == "__main__":
    main()