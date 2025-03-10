import psutil
import win32process
import win32gui
import win32con
import logging
from typing import Dict, Optional, List
import json
import os

class GameDetector:
    def __init__(self):
        self.game_processes = {
            "dota2.exe": "DotA2",
            "cs2.exe": "CS2",
            "steam.exe": "Steam"
        }
        self.current_game = None
        self.game_window = None
        self._load_game_configs()
        
    def _load_game_configs(self):
        """加载游戏配置"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            logging.error(f"加载游戏配置失败: {str(e)}")
            self.config = {}
            
    def get_game_servers(self, game: str) -> Dict[str, List[str]]:
        """获取游戏服务器列表"""
        try:
            return self.config.get("game_servers", {}).get(game, {})
        except Exception as e:
            logging.error(f"获取服务器列表失败: {str(e)}")
            return {}
            
    def detect_game(self) -> Optional[str]:
        """检测正在运行的游戏"""
        try:
            for proc in psutil.process_iter(['name', 'pid']):
                if proc.info['name'] in self.game_processes:
                    game_name = self.game_processes[proc.info['name']]
                    pid = proc.info['pid']
                    
                    # 获取窗口句柄
                    def callback(hwnd, hwnds):
                        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
                            _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
                            if found_pid == pid:
                                hwnds.append(hwnd)
                        return True
                        
                    hwnds = []
                    win32gui.EnumWindows(callback, hwnds)
                    
                    if hwnds:
                        self.game_window = hwnds[0]
                        self.current_game = game_name
                        return game_name
                        
            self.current_game = None
            self.game_window = None
            return None
            
        except Exception as e:
            logging.error(f"检测游戏失败: {str(e)}")
            return None
            
    def is_game_window_active(self) -> bool:
        """检查游戏窗口是否激活"""
        try:
            if not self.game_window:
                return False
            return win32gui.GetForegroundWindow() == self.game_window
        except Exception as e:
            logging.error(f"检查窗口状态失败: {str(e)}")
            return False
            
    def get_game_region(self) -> Optional[str]:
        """智能判断游戏区域"""
        try:
            if not self.current_game:
                return None
                
            # 获取Steam当前下载区域
            steam_config = os.path.expanduser('~/AppData/Local/Steam/config/config.vdf')
            if os.path.exists(steam_config):
                with open(steam_config, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'china' in content.lower():
                        return '国服'
                    elif 'hong kong' in content.lower():
                        return '香港'
                    elif 'singapore' in content.lower():
                        return '东南亚'
                        
            return None
            
        except Exception as e:
            logging.error(f"获取游戏区域失败: {str(e)}")
            return None
