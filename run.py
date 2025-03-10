#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import sys
import ctypes
import traceback
from pathlib import Path
import tkinter as tk

def is_admin():
    """检查是否具有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def request_admin():
    """请求管理员权限"""
    try:
        if not is_admin():
            # 使用绝对路径
            python_exe = sys.executable
            script = os.path.abspath(__file__)
            args = ' '.join(sys.argv[1:])
            
            logging.warning("需要管理员权限，正在请求...")
            
            # 使用runas命令提升权限
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas",
                python_exe,
                f'"{script}" {args}',
                None,
                1  # SW_SHOWNORMAL
            )
            
            # ShellExecuteW返回值大于32表示成功
            if ret <= 32:
                raise RuntimeError(f"请求管理员权限失败，错误码: {ret}")
                
            sys.exit(0)  # 退出当前进程
    except Exception as e:
        logging.error(f"请求管理员权限时出错: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

def setup_environment():
    """设置运行环境"""
    # 设置工作目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 配置日志
    log_file = 'accelerator.log'
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # 清理旧的日志文件
    try:
        if os.path.exists(log_file) and os.path.getsize(log_file) > 10 * 1024 * 1024:  # 10MB
            os.remove(log_file)
    except:
        pass

def main():
    """主程序入口"""
    try:
        # 检查管理员权限
        if not is_admin():
            request_admin()
            return
            
        # 设置环境
        setup_environment()
        
        # 导入GUI模块
        try:
            # 尝试从src.gui导入AcceleratorGUI
            from src.gui import AcceleratorGUI
            
            # 创建主窗口
            root = tk.Tk()
            app = AcceleratorGUI(root)
            
            # 设置窗口标题和图标
            root.title("游戏加速器")
            try:
                root.iconbitmap("assets/icon.ico")
            except:
                pass
                
            # 运行主循环
            root.mainloop()
            
        except ImportError as e:
            logging.error(f"导入GUI模块失败: {str(e)}")
            logging.info("尝试使用备用GUI模块...")
            
            # 尝试使用备用GUI类
            from gui import MainWindow
            
            # 创建主窗口
            root = tk.Tk()
            app = MainWindow(root)
            
            # 设置窗口标题和图标
            root.title("游戏加速器")
            try:
                root.iconbitmap("assets/icon.ico")
            except:
                pass
                
            # 运行主循环
            root.mainloop()
        
    except Exception as e:
        logging.error(f"程序运行出错: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()