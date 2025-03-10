import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
import json
import os
from pathlib import Path
from src.core import AcceleratorCore

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("游戏加速器")
        self.root.geometry("400x600")
        self.root.resizable(False, False)
        
        # 初始化加速器核心
        try:
            self.core = AcceleratorCore()
            logging.info("加速器核心初始化成功")
        except Exception as e:
            logging.error(f"加速器核心初始化失败: {str(e)}")
            messagebox.showerror("错误", "加速器初始化失败，请检查配置文件")
            self.root.destroy()
            return
        
        # 状态变量
        self.is_accelerating = False
        self.status_timer = None
        self.acceleration_thread = None
        
        self._init_ui()
        logging.info("GUI初始化完成")
        
    def _init_ui(self):
        """初始化界面"""
        # 游戏选择区域
        game_frame = ttk.LabelFrame(self.root, text="选择游戏", padding=10)
        game_frame.pack(fill=tk.X, padx=20, pady=5)
        
        self.game_var = tk.StringVar(value="DotA2")
        games = [("DotA2", "DotA2"), ("CS2", "CS2")]
        for game, value in games:
            ttk.Radiobutton(game_frame, text=game, value=value, 
                          variable=self.game_var).pack(side=tk.LEFT, padx=20)
        
        # 区服选择区域
        region_frame = ttk.LabelFrame(self.root, text="选择区服", padding=10)
        region_frame.pack(fill=tk.X, padx=20, pady=5)
        
        self.region_var = tk.StringVar(value="国服")
        regions = [("国服", "国服"), ("香港", "香港"), ("东南亚", "东南亚")]
        for region, value in regions:
            ttk.Radiobutton(region_frame, text=region, value=value,
                          variable=self.region_var).pack(side=tk.LEFT, padx=10)
        
        # 状态显示区域
        status_frame = ttk.LabelFrame(self.root, text="加速状态", padding=10)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        self.status_text = tk.Text(status_frame, height=15, width=40, font=("微软雅黑", 9))
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, 
                                command=self.status_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        # 控制按钮
        self.control_btn = ttk.Button(self.root, text="开始加速", 
                                    command=self._toggle_acceleration)
        self.control_btn.pack(pady=20)
        
        # 底部状态栏
        self.status_bar = ttk.Label(self.root, text="就绪")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
    def _toggle_acceleration(self):
        """切换加速状态"""
        logging.info(f"切换加速状态: 当前状态={self.is_accelerating}")
        if not self.is_accelerating:
            self._start_acceleration()
        else:
            self._stop_acceleration()
            
    def _start_acceleration(self):
        """启动加速"""
        try:
            # 防止重复点击
            if self.acceleration_thread and self.acceleration_thread.is_alive():
                logging.warning("加速线程已在运行中")
                return
                
            # 禁用按钮，更新状态
            self.control_btn.configure(state=tk.DISABLED)
            self.status_bar.configure(text="正在启动加速...")
            self.status_text.delete(1.0, tk.END)
            self.status_text.insert(tk.END, "正在测试线路...\n")
            
            game = self.game_var.get()
            region = self.region_var.get()
            logging.info(f"开始加速: 游戏={game}, 区服={region}")
            
            # 立即更新界面，提供视觉反馈
            self.root.update_idletasks()
            
            def start():
                try:
                    if self.core.start_acceleration(game, region):
                        logging.info("加速启动成功")
                        self.root.after(0, self._acceleration_started)
                    else:
                        logging.error("加速启动失败")
                        self.root.after(0, self._acceleration_failed)
                except Exception as e:
                    logging.error(f"加速线程出错: {str(e)}")
                    self.root.after(0, self._acceleration_failed)
                finally:
                    self.root.after(0, lambda: self.control_btn.configure(state=tk.NORMAL))
                    
            self.acceleration_thread = threading.Thread(target=start, daemon=True)
            self.acceleration_thread.start()
            logging.info("加速线程已启动")
            
            # 添加额外的状态更新
            self.status_text.insert(tk.END, "加速线程已启动，正在测试网络...\n")
            self.root.update_idletasks()
            
        except Exception as e:
            logging.error(f"启动加速失败: {str(e)}")
            messagebox.showerror("错误", f"启动加速失败: {str(e)}")
            self.control_btn.configure(state=tk.NORMAL)
            
    def _acceleration_started(self):
        """加速启动成功"""
        self.is_accelerating = True
        self.control_btn.configure(text="停止加速", state=tk.NORMAL)
        self.status_bar.configure(text="加速运行中")
        self._update_status()
        logging.info("加速状态更新已启动")
        
    def _acceleration_failed(self):
        """加速启动失败"""
        self.is_accelerating = False
        self.control_btn.configure(text="开始加速", state=tk.NORMAL)
        self.status_bar.configure(text="加速启动失败")
        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(tk.END, "加速启动失败，请检查以下问题：\n\n")
        self.status_text.insert(tk.END, "1. 是否以管理员权限运行\n")
        self.status_text.insert(tk.END, "2. 网络连接是否正常\n")
        self.status_text.insert(tk.END, "3. 防火墙是否允许程序联网\n\n")
        self.status_text.insert(tk.END, "请查看日志获取详细信息\n\n")
        self.status_text.insert(tk.END, "注意：如果点击按钮后界面没有反应，可能是因为加速进程正在后台运行，\n")
        self.status_text.insert(tk.END, "请等待几秒钟，如果状态没有更新，请再次点击按钮。")
        messagebox.showerror("错误", "加速启动失败，请查看日志获取详细信息")
        # 确保界面更新
        self.root.update_idletasks()
        
    def _stop_acceleration(self):
        """停止加速"""
        try:
            logging.info("正在停止加速...")
            self.is_accelerating = False
            self.core.stop_acceleration()
            
            # 更新UI
            self.control_btn.configure(text="开始加速")
            self.status_bar.configure(text="就绪")
            self.status_text.delete(1.0, tk.END)
            self.status_text.insert(tk.END, "加速已停止\n")
            
            # 取消状态更新
            if self.status_timer:
                self.root.after_cancel(self.status_timer)
                self.status_timer = None
                
            logging.info("加速已停止")
                
        except Exception as e:
            logging.error(f"停止加速失败: {str(e)}")
            messagebox.showerror("错误", f"停止加速失败: {str(e)}")
            
    def _update_status(self):
        """更新状态显示"""
        try:
            if not self.is_accelerating:
                return
                
            status = self.core.get_status()
            self.status_text.delete(1.0, tk.END)
            
            if status["routes"]:
                total_improvement = 0
                route_count = 0
                
                for server, route in status["routes"].items():
                    if "original_latency" in route and "current_latency" in route:
                        original = route["original_latency"]
                        current = route["current_latency"]
                        improvement = ((original - current) / original * 100 
                                    if original > 0 else 0)
                        
                        self.status_text.insert(tk.END, 
                            f"服务器: {server}\n"
                            f"加速线路: {route.get('node', '无')}\n"
                            f"原始延迟: {original:.0f}ms\n"
                            f"当前延迟: {current:.0f}ms\n"
                            f"优化效果: {improvement:+.1f}%\n\n"
                        )
                        
                        total_improvement += improvement
                        route_count += 1
                        
                if route_count > 0:
                    avg_improvement = total_improvement / route_count
                    self.status_text.insert(tk.END, 
                        f"平均优化效果: {avg_improvement:+.1f}%\n")
                    
                    # 更新状态栏
                    self.status_bar.configure(
                        text=f"加速中 - 平均优化: {avg_improvement:+.1f}%")
            
            # 设置下一次更新
            self.status_timer = self.root.after(1000, self._update_status)
            
        except Exception as e:
            logging.error(f"更新状态失败: {str(e)}")
            self.status_timer = self.root.after(5000, self._update_status)
            
    def _on_closing(self):
        """处理窗口关闭事件"""
        try:
            if self.is_accelerating:
                if messagebox.askokcancel("确认", "加速正在运行中，确定要退出吗？"):
                    self._stop_acceleration()
                    self.root.destroy()
            else:
                self.root.destroy()
        except:
            self.root.destroy()
            
    def run(self):
        """运行主窗口"""
        self.root.mainloop()
        
        # 确保程序退出时停止加速
        if self.is_accelerating:
            self.core.stop_acceleration()

def main():
    root = tk.Tk()
    app = MainWindow(root)
    app.run()

if __name__ == "__main__":
    main()
