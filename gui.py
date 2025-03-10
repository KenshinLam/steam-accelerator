import tkinter as tk
from tkinter import ttk, scrolledtext
import json
import threading
import time
import logging
from src.route_optimizer import RouteOptimizer

class AcceleratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("游戏加速器")
        self.root.geometry("800x600")
        
        # 设置样式
        style = ttk.Style()
        style.configure("Accent.TButton", font=('微软雅黑', 10, 'bold'))
        style.configure("Status.TLabel", font=('微软雅黑', 9))
        
        self.optimizer = RouteOptimizer()
        self.monitoring = False
        self.current_server = None
        self.original_latency = None
        
        self._init_ui()
        self._load_config()
        
    def _init_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # 配置网格
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        
        # 左侧控制面板
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding="5")
        control_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # 游戏选择
        ttk.Label(control_frame, text="游戏:").grid(row=0, column=0, sticky="w", pady=2)
        self.game_var = tk.StringVar()
        self.game_combo = ttk.Combobox(control_frame, textvariable=self.game_var, state="readonly")
        self.game_combo.grid(row=0, column=1, sticky="ew", pady=2)
        
        # 区域选择
        ttk.Label(control_frame, text="区域:").grid(row=1, column=0, sticky="w", pady=2)
        self.region_var = tk.StringVar()
        self.region_combo = ttk.Combobox(control_frame, textvariable=self.region_var, state="readonly")
        self.region_combo.grid(row=1, column=1, sticky="ew", pady=2)
        
        # 操作按钮
        btn_frame = ttk.Frame(control_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.test_btn = ttk.Button(btn_frame, text="测试延迟", command=self.test_latency, style="Accent.TButton")
        self.test_btn.grid(row=0, column=0, padx=5)
        
        self.accelerate_btn = ttk.Button(btn_frame, text="开始加速", command=self.start_acceleration, style="Accent.TButton")
        self.accelerate_btn.grid(row=0, column=1, padx=5)
        
        # 右侧状态面板
        status_frame = ttk.LabelFrame(main_frame, text="状态监控", padding="5")
        status_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # 延迟显示
        latency_frame = ttk.Frame(status_frame)
        latency_frame.grid(row=0, column=0, sticky="ew", pady=5)
        latency_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(latency_frame, text="当前状态:", style="Status.TLabel").grid(row=0, column=0, sticky="w")
        self.status_label = ttk.Label(latency_frame, text="未加速", style="Status.TLabel")
        self.status_label.grid(row=0, column=1, sticky="w", padx=5)
        
        ttk.Label(latency_frame, text="原始延迟:", style="Status.TLabel").grid(row=1, column=0, sticky="w")
        self.original_latency_label = ttk.Label(latency_frame, text="--", style="Status.TLabel")
        self.original_latency_label.grid(row=1, column=1, sticky="w", padx=5)
        
        ttk.Label(latency_frame, text="优化延迟:", style="Status.TLabel").grid(row=2, column=0, sticky="w")
        self.optimized_latency_label = ttk.Label(latency_frame, text="--", style="Status.TLabel")
        self.optimized_latency_label.grid(row=2, column=1, sticky="w", padx=5)
        
        ttk.Label(latency_frame, text="延迟改善:", style="Status.TLabel").grid(row=3, column=0, sticky="w")
        self.latency_improvement_label = ttk.Label(latency_frame, text="--", style="Status.TLabel")
        self.latency_improvement_label.grid(row=3, column=1, sticky="w", padx=5)
        
        # 服务器信息
        server_frame = ttk.LabelFrame(status_frame, text="服务器信息", padding="5")
        server_frame.grid(row=1, column=0, sticky="ew", pady=5)
        server_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(server_frame, text="游戏服务器:", style="Status.TLabel").grid(row=0, column=0, sticky="w")
        self.server_label = ttk.Label(server_frame, text="--", style="Status.TLabel")
        self.server_label.grid(row=0, column=1, sticky="w", padx=5)
        
        ttk.Label(server_frame, text="加速节点:", style="Status.TLabel").grid(row=1, column=0, sticky="w")
        self.node_label = ttk.Label(server_frame, text="--", style="Status.TLabel")
        self.node_label.grid(row=1, column=1, sticky="w", padx=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="5")
        log_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        # 配置日志处理器
        log_handler = logging.StreamHandler(self.LogRedirector(self.log_text))
        log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(log_handler)
        logging.getLogger().setLevel(logging.INFO)
        
        # 设置网格权重
        main_frame.grid_rowconfigure(1, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        
    def _load_config(self):
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            games = list(config.get('game_servers', {}).keys())
            self.game_combo['values'] = games
            if games:
                self.game_combo.set(games[0])
                
            regions = list(config.get('nodes', {}).keys())
            self.region_combo['values'] = regions
            if regions:
                self.region_combo.set(regions[0])
                
        except Exception as e:
            logging.error(f"加载配置失败: {str(e)}")
            
    def test_latency(self):
        """测试服务器延迟"""
        self.test_btn.configure(state="disabled")
        threading.Thread(target=self._test_latency_thread, daemon=True).start()
        
    def _test_latency_thread(self):
        try:
            game = self.game_var.get()
            region = self.region_var.get()
            
            if not game or not region:
                logging.error("请选择游戏和区域")
                return
                
            logging.info(f"开始测试 {game} {region} 服务器延迟...")
            
            # 获取服务器列表
            servers = self.optimizer.get_servers_for_game(game, region)
            if not servers:
                logging.error("未找到服务器")
                return
                
            logging.info(f"找到 {len(servers)} 个服务器:")
            
            # 测试服务器延迟
            best_server = None
            best_latency = 999.0
            
            for server in servers:
                latency = self.optimizer.test_latency(server)
                logging.info(f"服务器 {server} 延迟: {latency}ms")
                
                if latency < best_latency:
                    best_server = server
                    best_latency = latency
                    
            if best_server:
                self.current_server = best_server
                self.original_latency = best_latency
                self.original_latency_label.configure(text=f"{best_latency:.1f}ms")
                self.server_label.configure(text=best_server)
                
            # 获取加速节点
            nodes = self.optimizer.get_nodes_for_region(region)
            if not nodes:
                logging.error("未找到加速节点")
                return
                
            logging.info(f"\n找到 {len(nodes)} 个加速节点:")
            
            # 测试节点延迟
            for node in nodes:
                latency = self.optimizer.test_latency(node)
                logging.info(f"节点 {node} 延迟: {latency}ms")
                
            logging.info("\n延迟测试完成")
            
        except Exception as e:
            logging.error(f"测试延迟失败: {str(e)}")
        finally:
            self.test_btn.configure(state="normal")
            
    def start_acceleration(self):
        """开始加速"""
        if not self.current_server:
            logging.error("请先测试延迟")
            return
            
        # 禁用按钮，避免重复点击
        self.accelerate_btn.configure(state="disabled")
        self.test_btn.configure(state="disabled")
        
        # 在后台线程中执行优化
        threading.Thread(target=self._acceleration_thread, daemon=True).start()
        
    def _acceleration_thread(self):
        """后台执行加速优化"""
        try:
            game = self.game_var.get()
            region = self.region_var.get()
            
            logging.info(f"开始为 {game} {region} 优化路由...")
            
            # 开始优化
            if self.optimizer.optimize_route(self.current_server, region):
                self.monitoring = True
                
                # 更新UI状态
                self.root.after(0, lambda: self._update_ui_state(True))
                
                # 启动延迟监控
                threading.Thread(target=self._monitor_latency, daemon=True).start()
            else:
                logging.info("\n未能优化任何服务器的路由")
                # 恢复UI状态
                self.root.after(0, lambda: self._update_ui_state(False))
                
        except Exception as e:
            logging.error(f"开始加速失败: {str(e)}")
            # 恢复UI状态
            self.root.after(0, lambda: self._update_ui_state(False))
            
    def _update_ui_state(self, is_accelerating):
        """更新UI状态"""
        if is_accelerating:
            self.accelerate_btn.configure(text="停止加速", state="normal")
            self.status_label.configure(text="加速中")
        else:
            self.accelerate_btn.configure(text="开始加速", state="normal")
            self.test_btn.configure(state="normal")
            self.status_label.configure(text="未加速")
            self.optimized_latency_label.configure(text="--")
            self.latency_improvement_label.configure(text="--")
            self.node_label.configure(text="--")
            
    def stop_acceleration(self):
        """停止加速"""
        # 禁用按钮，避免重复点击
        self.accelerate_btn.configure(state="disabled")
        
        # 在后台线程中执行停止
        threading.Thread(target=self._stop_acceleration_thread, daemon=True).start()
        
    def _stop_acceleration_thread(self):
        """后台执行停止加速"""
        try:
            logging.info("\n正在停止路由优化...")
            
            if self.current_server:
                self.optimizer.remove_route(self.current_server)
                
            self.monitoring = False
            
            # 恢复UI状态
            self.root.after(0, lambda: self._update_ui_state(False))
            
            logging.info("路由优化已停止")
            
        except Exception as e:
            logging.error(f"停止加速失败: {str(e)}")
            # 恢复UI状态
            self.root.after(0, lambda: self._update_ui_state(False))
            
    def _monitor_latency(self):
        """监控延迟变化"""
        while self.monitoring:
            try:
                if self.current_server:
                    # 测试当前延迟
                    current_latency = self.optimizer.test_latency(self.current_server)
                    
                    # 更新UI
                    self.optimized_latency_label.configure(text=f"{current_latency:.1f}ms")
                    
                    if self.original_latency:
                        improvement = self.original_latency - current_latency
                        self.latency_improvement_label.configure(
                            text=f"{improvement:.1f}ms ({improvement/self.original_latency*100:.1f}%)"
                        )
                        
                    # 获取当前使用的节点
                    if self.current_server in self.optimizer.routes:
                        route_info = self.optimizer.routes[self.current_server]
                        self.node_label.configure(text=route_info['node'])
                        
            except Exception as e:
                logging.error(f"监控延迟失败: {str(e)}")
                
            time.sleep(1)  # 每秒更新一次
            
    class LogRedirector:
        def __init__(self, text_widget):
            self.text_widget = text_widget
            
        def write(self, message):
            self.text_widget.insert(tk.END, message)
            self.text_widget.see(tk.END)
            
        def flush(self):
            pass

def main():
    root = tk.Tk()
    app = AcceleratorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
