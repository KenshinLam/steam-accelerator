import sys
import os
import json
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QPushButton, QLabel, QComboBox, QHBoxLayout, QGroupBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import winreg
import psutil
import requests
from scapy.all import *
from .route_optimizer import RouteOptimizer
import time

class GameDetector:
    def __init__(self):
        self.steam_games = {
            "DotA2": {
                "process": "dota2.exe",
                "servers": {
                    "国服": ["cm.dota2.com.cn", "api.steampowered.com.cn"],
                    "东南亚": ["sgp-1.valve.net", "sgp-2.valve.net"],
                    "日本": ["tok.valve.net"],
                    "韩国": ["kor.valve.net"]
                }
            },
            "CS2": {
                "process": "cs2.exe",
                "servers": {
                    "完美世界": ["perfect.csgo.com.cn"],
                    "香港": ["hkg.valve.net"],
                    "日本": ["tok.valve.net"],
                    "新加坡": ["sgp-1.valve.net"]
                }
            },
            "PUBG": {
                "process": "TslGame.exe",
                "servers": {
                    "亚服": ["prod-live-asia.playbattlegrounds.com"],
                    "韩服": ["prod-live-korea.playbattlegrounds.com"]
                }
            }
        }
        
    def get_running_steam_games(self):
        """获取当前运行的Steam游戏"""
        running_games = []
        for proc in psutil.process_iter(['name']):
            for game, info in self.steam_games.items():
                if proc.info['name'] and proc.info['name'].lower() == info['process'].lower():
                    running_games.append(game)
        return running_games
    
    def get_game_servers(self, game):
        """获取指定游戏的可用服务器"""
        if game in self.steam_games:
            return list(self.steam_games[game]['servers'].keys())
        return []
    
    def get_server_hosts(self, game, server):
        """获取指定游戏服务器的主机列表"""
        if game in self.steam_games and server in self.steam_games[game]['servers']:
            return self.steam_games[game]['servers'][server]
        return []

class AcceleratorCore:
    def __init__(self):
        self.steam_path = self._get_steam_path()
        self.game_detector = GameDetector()
        self.route_optimizer = RouteOptimizer()
        self.current_game = None
        self.current_server = None
        self.is_accelerating = False
        
    def _get_steam_path(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
            path = winreg.QueryValueEx(key, "InstallPath")[0]
            winreg.CloseKey(key)
            return path
        except:
            return None

    def get_available_games(self):
        """获取可用的游戏列表"""
        return list(self.game_detector.steam_games.keys())

    def get_game_servers(self, game):
        """获取指定游戏的服务器列表"""
        return self.game_detector.get_game_servers(game)

    def start_acceleration(self, game, server):
        if self.is_accelerating:
            return False
            
        self.current_game = game
        self.current_server = server
        self.is_accelerating = True
        
        # 获取需要加速的主机列表
        hosts = self.game_detector.get_server_hosts(game, server)
        
        # 优化每个主机的路由
        for host in hosts:
            try:
                if self.route_optimizer.optimize_route(host, server):
                    self.route_optimizer.apply_route(host, self.route_optimizer.get_route_stats(host)['node'])
                else:
                    print(f"无法优化路由: {host}")
                    return False
            except Exception as e:
                print(f"路由优化失败: {str(e)}")
                return False
                
        return True

    def stop_acceleration(self):
        if not self.is_accelerating:
            return
            
        if self.current_game and self.current_server:
            hosts = self.game_detector.get_server_hosts(self.current_game, self.current_server)
            for host in hosts:
                self.route_optimizer.clear_route(host)
                
        self.is_accelerating = False
        self.current_game = None
        self.current_server = None

    def get_current_status(self):
        """获取当前加速状态信息"""
        if not self.is_accelerating:
            return "未加速"
            
        running_games = self.game_detector.get_running_steam_games()
        if self.current_game in running_games:
            return f"正在加速 {self.current_game} ({self.current_server})"
        else:
            return f"已加速 {self.current_game} ({self.current_server})，但游戏未运行"

class LatencyMonitor(QThread):
    latency_updated = pyqtSignal(float)
    
    def __init__(self, core):
        super().__init__()
        self.core = core
        self.running = False
        
    def run(self):
        self.running = True
        while self.running:
            if self.core.is_accelerating:
                try:
                    hosts = self.core.game_detector.get_server_hosts(
                        self.core.current_game,
                        self.core.current_server
                    )
                    if hosts:
                        # 测试第一个主机的延迟
                        latency = self.core.route_optimizer.test_latency(hosts[0])
                        self.latency_updated.emit(latency)
                except Exception as e:
                    print(f"延迟监控错误: {str(e)}")
            time.sleep(1)
            
    def stop(self):
        self.running = False

class AcceleratorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.core = AcceleratorCore()
        self.latency_monitor = LatencyMonitor(self.core)
        self.latency_monitor.latency_updated.connect(self.update_latency)
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Steam游戏加速器')
        self.setFixedSize(500, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 游戏选择组
        game_group = QGroupBox("游戏选择")
        game_layout = QVBoxLayout()
        
        self.game_combo = QComboBox()
        self.game_combo.addItems(self.core.get_available_games())
        self.game_combo.currentTextChanged.connect(self.on_game_changed)
        game_layout.addWidget(self.game_combo)
        
        game_group.setLayout(game_layout)
        layout.addWidget(game_group)
        
        # 服务器选择组
        server_group = QGroupBox("服务器选择")
        server_layout = QVBoxLayout()
        
        self.server_combo = QComboBox()
        self.update_server_list()
        server_layout.addWidget(self.server_combo)
        
        server_group.setLayout(server_layout)
        layout.addWidget(server_group)
        
        # 状态显示
        status_group = QGroupBox("状态信息")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("当前状态：未加速")
        status_layout.addWidget(self.status_label)
        
        # 延迟显示
        self.latency_label = QLabel("当前延迟：-")
        status_layout.addWidget(self.latency_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # 控制按钮
        self.toggle_button = QPushButton("开始加速")
        self.toggle_button.clicked.connect(self.toggle_acceleration)
        layout.addWidget(self.toggle_button)
        
    def on_game_changed(self, game):
        self.update_server_list()
        
    def update_server_list(self):
        game = self.game_combo.currentText()
        self.server_combo.clear()
        servers = self.core.get_game_servers(game)
        if servers:
            self.server_combo.addItems(servers)
            self.toggle_button.setEnabled(True)
        else:
            self.toggle_button.setEnabled(False)
        
    def toggle_acceleration(self):
        try:
            if not self.core.is_accelerating:
                game = self.game_combo.currentText()
                server = self.server_combo.currentText()
                self.toggle_button.setEnabled(False)
                self.toggle_button.setText("正在启动加速...")
                
                if self.core.start_acceleration(game, server):
                    self.status_label.setText(f"当前状态：{self.core.get_current_status()}")
                    self.toggle_button.setText("停止加速")
                    self.latency_monitor.start()
                else:
                    self.status_label.setText("加速失败，请检查网络连接")
                    self.toggle_button.setText("开始加速")
            else:
                self.latency_monitor.stop()
                self.core.stop_acceleration()
                self.status_label.setText("当前状态：未加速")
                self.latency_label.setText("当前延迟：-")
                self.toggle_button.setText("开始加速")
        except Exception as e:
            print(f"加速器错误: {str(e)}")
            self.status_label.setText(f"发生错误: {str(e)}")
        finally:
            self.toggle_button.setEnabled(True)
            
    def update_latency(self, latency):
        if latency < 999.0:
            self.latency_label.setText(f"当前延迟：{latency:.1f}ms")
        else:
            self.latency_label.setText("当前延迟：超时")
            
    def closeEvent(self, event):
        self.latency_monitor.stop()
        self.core.stop_acceleration()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = AcceleratorGUI()
    window.show()
    sys.exit(app.exec_()) 