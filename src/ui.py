import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
import ctypes
from typing import Optional, Dict
from src.core import AcceleratorCore

def is_admin():
    """检查是否具有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

class MainWindow:
    def __init__(self):
        # 检查管理员权限
        if not is_admin():
            messagebox.showerror("错误", "请以管理员权限运行程序！")
            raise PermissionError("需要管理员权限")
            
        self.root = tk.Tk()
        self.root.title("游戏加速器")
        self.root.geometry("400x600")
        self.root.resizable(False, False)
        
        # 初始化加速器核心
        self.core = AcceleratorCore()
        
        # 状态变量
        self.status_timer: Optional[str] = None
        self.last_status: Dict = {}
        self.is_testing = False
        
        self._init_ui()
        
    def _init_ui(self):
        # 设置样式
        style = ttk.Style()
        style.configure("Title.TLabel", font=("微软雅黑", 16, "bold"))
        style.configure("Status.TLabel", font=("微软雅黑", 10))
        style.configure("Game.TRadiobutton", font=("微软雅黑", 10))
        
        # 标题
        title = ttk.Label(self.root, text="游戏加速器", style="Title.TLabel")
        title.pack(pady=20)
        
        # 游戏选择区域
        game_frame = ttk.LabelFrame(self.root, text="选择游戏", padding=10)
        game_frame.pack(fill=tk.X, padx=20, pady=5)
        
        self.game_var = tk.StringVar(value="DotA2")
        games = [("DotA2", "DotA2"), ("CS2", "CS2")]
        for game, value in games:
            ttk.Radiobutton(game_frame, text=game, value=value, 
                          variable=self.game_var, style="Game.TRadiobutton",
                          command=self._on_selection_change).pack(side=tk.LEFT, padx=20)
        
        # 区服选择区域
        region_frame = ttk.LabelFrame(self.root, text="选择区服", padding=10)
        region_frame.pack(fill=tk.X, padx=20, pady=5)
        
        self.region_var = tk.StringVar(value="国服")
        regions = [("国服", "国服"), ("香港", "香港"), ("东南亚", "东南亚")]
        for region, value in regions:
            ttk.Radiobutton(region_frame, text=region, value=value,
                          variable=self.region_var, style="Game.TRadiobutton",
                          command=self._on_selection_change).pack(side=tk.LEFT, padx=10)
        
        # 状态显示区域
        status_frame = ttk.LabelFrame(self.root, text="加速状态", padding=10)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        # 使用Text组件显示状态
        self.status_text = tk.Text(status_frame, height=20, width=40, 
                                 font=("微软雅黑", 9), wrap=tk.WORD)
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
        self.status_bar = ttk.Label(self.root, text="就绪", style="Status.TLabel")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
    def _on_selection_change(self):
        """处理游戏或区服选择变更"""
        if self.core.active:
            if messagebox.askyesno("确认", "切换游戏或区服将停止当前加速，是否继续？"):
                self._stop_acceleration()
            else:
                # 恢复之前的选择
                self.game_var.set(self.last_status.get("game", "DotA2"))
                self.region_var.set(self.last_status.get("region", "国服"))
                
    def _toggle_acceleration(self):
        """切换加速状态"""
        if self.is_testing:  # 防止重复点击
            return
            
        if not self.core.active:
            self._start_acceleration()
        else:
            self._stop_acceleration()
            
    def _start_acceleration(self):
        """启动加速"""
        # 保存当前选择
        self.last_status = {
            "game": self.game_var.get(),
            "region": self.region_var.get()
        }
        
        # 更新UI状态
        self.is_testing = True
        self.control_btn.configure(state=tk.DISABLED)
        self.status_bar.configure(text="正在测试线路...")
        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(tk.END, "正在测试加速节点...\n")
        
        def start():
            try:
                if self.core.start_acceleration(self.game_var.get(), self.region_var.get()):
                    self.root.after(0, self._acceleration_started)
                else:
                    self.root.after(0, self._acceleration_failed)
            finally:
                self.root.after(0, self._reset_testing_state)
                
        threading.Thread(target=start, daemon=True).start()
        
    def _acceleration_started(self):
        """加速启动成功"""
        self.control_btn.configure(text="停止加速", state=tk.NORMAL)
        self.status_bar.configure(text="加速运行中")
        self._update_status()
        
    def _acceleration_failed(self):
        """加速启动失败"""
        self.control_btn.configure(text="开始加速", state=tk.NORMAL)
        self.status_bar.configure(text="加速启动失败")
        messagebox.showerror("错误", "加速启动失败，请查看日志获取详细信息")
        
    def _reset_testing_state(self):
        """重置测试状态"""
        self.is_testing = False
        self.control_btn.configure(state=tk.NORMAL)
        
    def _stop_acceleration(self):
        """停止加速"""
        if self.is_testing:
            return
            
        self.core.stop_acceleration()
        
        # 更新UI
        self.control_btn.configure(text="开始加速")
        self.status_bar.configure(text="就绪")
        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(tk.END, "加速已停止\n")
        
        # 取消状态更新定时器
        if self.status_timer:
            self.root.after_cancel(self.status_timer)
            self.status_timer = None
            
    def _update_status(self):
        """更新状态显示"""
        if not self.core.active:
            return
            
        try:
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
            
    def run(self):
        """运行主窗口"""
        self.root.mainloop()
        
        # 确保程序退出时停止加速
        if self.core.active:
            self.core.stop_acceleration()
