import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import logging
from typing import Dict, Optional
from .core import AcceleratorCore

class AcceleratorGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.core = AcceleratorCore()
        self.status_update_id = None
        
        # 设置窗口
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 游戏选择区域
        self.game_frame = ttk.LabelFrame(self.main_frame, text="游戏", padding="5")
        self.game_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        self.game_var = tk.StringVar(value="DotA2")
        games = ["DotA2", "CS2"]
        for i, game in enumerate(games):
            ttk.Radiobutton(self.game_frame, text=game, value=game, 
                          variable=self.game_var).grid(row=0, column=i, padx=10)
        
        # 区服选择区域
        self.region_frame = ttk.LabelFrame(self.main_frame, text="区服", padding="5")
        self.region_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        self.region_var = tk.StringVar(value="国服")
        regions = ["国服", "日服", "美服", "欧服"]
        for i, region in enumerate(regions):
            ttk.Radiobutton(self.region_frame, text=region, value=region,
                          variable=self.region_var).grid(row=0, column=i, padx=10)
        
        # 状态显示区域
        self.status_frame = ttk.LabelFrame(self.main_frame, text="状态", padding="5")
        self.status_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S),
                             padx=5, pady=5)
        
        self.status_text = scrolledtext.ScrolledText(self.status_frame, height=10,
                                                   wrap=tk.WORD)
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 控制按钮区域
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        self.start_button = ttk.Button(self.button_frame, text="启动加速",
                                     command=self.start_acceleration)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(self.button_frame, text="停止加速",
                                    command=self.stop_acceleration, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5)
        
        # 配置grid权重
        self.main_frame.columnconfigure(0, weight=1)
        self.status_frame.columnconfigure(0, weight=1)
        self.status_frame.rowconfigure(0, weight=1)
        
        # 初始化状态
        self.acceleration_active = False
        self.log("欢迎使用游戏加速器！")
        self.log("请选择游戏和区服，然后点击'启动加速'")
        
    def log(self, message: str):
        """添加日志到状态框"""
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        
    def update_status(self):
        """更新状态显示"""
        if not self.acceleration_active:
            return
            
        try:
            status = self.core.get_status()
            if status["active"]:
                text = ""
                for server, route in status["routes"].items():
                    current = route["current_latency"]
                    original = route["original_latency"]
                    improvement = ((original - current) / original * 100 
                                 if original > 0 else 0)
                    
                    text += f"服务器: {server}\n"
                    text += f"当前延迟: {current:.0f}ms "
                    text += f"(优化: {improvement:+.1f}%)\n"
                    
                self.status_text.delete(1.0, tk.END)
                self.status_text.insert(tk.END, text)
            
        except Exception as e:
            logging.error(f"更新状态失败: {str(e)}")
            
        finally:
            # 每秒更新一次
            if self.acceleration_active:
                self.status_update_id = self.root.after(1000, self.update_status)
        
    def start_acceleration(self):
        """启动加速"""
        if self.acceleration_active:
            return
            
        game = self.game_var.get()
        region = self.region_var.get()
        
        # 禁用按钮，防止重复点击
        self.start_button.config(state=tk.DISABLED)
        self.game_frame.config(state=tk.DISABLED)
        self.region_frame.config(state=tk.DISABLED)
        
        self.log(f"正在启动加速 ({game} - {region})...")
        
        def _start():
            try:
                if self.core.start_acceleration(game, region):
                    self.acceleration_active = True
                    self.root.after(0, self._update_ui_after_start)
                else:
                    self.log("启动加速失败，请查看日志获取详细信息")
                    self.root.after(0, self._update_ui_after_stop)
            except Exception as e:
                logging.error(f"启动加速失败: {str(e)}")
                self.log(f"启动加速时出错: {str(e)}")
                self.root.after(0, self._update_ui_after_stop)
        
        # 在新线程中启动加速
        threading.Thread(target=_start, daemon=True).start()
        
    def stop_acceleration(self):
        """停止加速"""
        if not self.acceleration_active:
            return
            
        # 禁用按钮，防止重复点击
        self.stop_button.config(state=tk.DISABLED)
        self.log("正在停止加速...")
        
        def _stop():
            try:
                self.core.stop_acceleration()
            except Exception as e:
                logging.error(f"停止加速失败: {str(e)}")
                self.log(f"停止加速时出错: {str(e)}")
            finally:
                self.acceleration_active = False
                self.root.after(0, self._update_ui_after_stop)
        
        # 在新线程中停止加速
        threading.Thread(target=_stop, daemon=True).start()
        
    def _update_ui_after_start(self):
        """加速启动后更新UI"""
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.game_frame.config(state=tk.DISABLED)
        self.region_frame.config(state=tk.DISABLED)
        self.update_status()
        
    def _update_ui_after_stop(self):
        """加速停止后更新UI"""
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.game_frame.config(state=tk.NORMAL)
        self.region_frame.config(state=tk.NORMAL)
        
        if self.status_update_id:
            self.root.after_cancel(self.status_update_id)
            self.status_update_id = None
