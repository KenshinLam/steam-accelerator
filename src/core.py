import subprocess
import threading
import logging
import json
import os
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from queue import Queue
from typing import Dict, Optional, List
import time

class AcceleratorCore:
    def __init__(self):
        self.active = False
        self.routes = {}
        self.lock = threading.Lock()
        self.status_queue = Queue()
        self.executor = ThreadPoolExecutor(max_workers=5)  # 增加并发数
        self.monitor_future: Optional[Future] = None
        self._load_config()
        
    def _load_config(self):
        """加载配置"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            logging.info("配置加载成功")
        except Exception as e:
            logging.error(f"加载配置失败: {str(e)}")
            self.config = {}

    def test_latency(self, host: str, count: int = 4, timeout: int = 1000) -> float:
        """测试延迟"""
        try:
            # 使用更快的ping参数
            cmd = f'ping -n {count} -w {timeout} {host}'
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                # 提取平均延迟
                for line in result.stdout.split('\n'):
                    if '平均 = ' in line:
                        avg = line.split('=')[-1].strip('ms').strip()
                        return float(avg)
                    elif 'Average = ' in line:
                        avg = line.split('=')[-1].strip('ms').strip()
                        return float(avg)
                        
            logging.warning(f"Ping {host} 失败: {result.stderr}")
            return 999.0
            
        except Exception as e:
            logging.error(f"测试延迟失败: {str(e)}")
            return 999.0

    def _test_node_quality(self, node: Dict) -> Dict:
        """测试节点质量"""
        try:
            node_ip = node["ip"]
            logging.info(f"测试节点: {node_ip}")
            
            # 快速测试节点延迟
            node_latency = self.test_latency(node_ip, count=2, timeout=500)
            if node_latency >= 100:  # 跳过高延迟节点
                logging.warning(f"节点 {node_ip} 延迟过高: {node_latency}ms")
                return {"ip": node_ip, "score": 0, "latency": node_latency}
                
            # 测试节点到目标服务器的连通性
            success_count = 0
            total_latency = 0
            test_count = 0
            
            # 只测试当前游戏和区服的服务器
            game_servers = self.current_game_servers
            if game_servers:
                for server_group in game_servers.values():
                    for server in server_group:
                        test_count += 1
                        server_latency = self.test_latency(server, count=2, timeout=500)
                        if server_latency < 999.0:
                            success_count += 1
                            total_latency += server_latency
                            
            connectivity = success_count / test_count if test_count > 0 else 0
            avg_latency = total_latency / success_count if success_count > 0 else 999.0
            
            # 计算节点得分 (0-100)
            score = (
                (1 - node_latency/200) * 40 +  # 节点延迟占40%
                connectivity * 30 +            # 连通性占30%
                (1 - avg_latency/500) * 30     # 平均延迟占30%
            ) if node_latency < 200 else 0
            
            result = {
                "ip": node_ip,
                "score": max(0, min(100, score)),
                "latency": node_latency,
                "connectivity": connectivity,
                "avg_latency": avg_latency
            }
            
            logging.info(f"节点 {node_ip} 测试结果: 得分={result['score']:.1f}, "
                        f"延迟={node_latency:.0f}ms, 连通性={connectivity:.1%}")
            return result
            
        except Exception as e:
            logging.error(f"测试节点质量失败: {str(e)}")
            return {"ip": node["ip"], "score": 0, "latency": 999.0}

    def _find_best_nodes(self, region: str) -> List[Dict]:
        """查找最佳节点"""
        try:
            nodes = []
            if region == "国服":
                # 对于国服，测试所有运营商的节点
                for isp_nodes in self.config["nodes"][region].values():
                    nodes.extend(isp_nodes)
            else:
                # 对于其他区域，直接获取节点列表
                nodes = self.config["nodes"][region]
                
            if not nodes:
                logging.error(f"区服 {region} 未找到可用节点")
                return []
                
            logging.info(f"开始测试 {region} 的 {len(nodes)} 个节点")
            start_time = time.time()
                
            # 并行测试所有节点
            futures = []
            for node in nodes:
                future = self.executor.submit(self._test_node_quality, node)
                futures.append(future)
                
            # 收集测试结果
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result["score"] > 0:  # 只保留有效节点
                        results.append(result)
                except Exception as e:
                    logging.error(f"节点测试失败: {str(e)}")
                    
            # 按得分排序，返回前5个最佳节点
            best_nodes = sorted(results, key=lambda x: x["score"], reverse=True)[:5]
            
            elapsed = time.time() - start_time
            logging.info(f"节点测试完成，耗时 {elapsed:.1f} 秒，"
                        f"找到 {len(best_nodes)} 个可用节点")
            return best_nodes
            
        except Exception as e:
            logging.error(f"查找最佳节点失败: {str(e)}")
            return []

    def _add_route(self, target: str, gateway: str) -> bool:
        """添加路由"""
        try:
            # 先删除已存在的路由
            self._delete_route(target)
            
            # 添加新路由（使用永久路由）
            cmd = f'route add {target} mask 255.255.255.255 {gateway} -p'
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            
            if result.returncode != 0:
                logging.error(f"添加路由失败: {result.stderr}")
                return False
                
            # 验证路由是否添加成功
            verify_cmd = f'route print {target}'
            verify = subprocess.run(verify_cmd, capture_output=True, text=True, shell=True)
            success = gateway in verify.stdout
            
            if success:
                logging.info(f"成功添加路由: {target} -> {gateway}")
            else:
                logging.error(f"路由添加验证失败: {target} -> {gateway}")
            
            return success
            
        except Exception as e:
            logging.error(f"添加路由失败: {str(e)}")
            return False

    def _delete_route(self, target: str) -> bool:
        """删除路由"""
        try:
            cmd = f'route delete {target}'
            result = subprocess.run(cmd, capture_output=True, shell=True)
            success = result.returncode == 0
            
            if success:
                logging.info(f"成功删除路由: {target}")
            else:
                logging.warning(f"删除路由失败: {target}")
                
            return success
        except Exception as e:
            logging.error(f"删除路由失败: {str(e)}")
            return False

    def _monitor_routes(self):
        """监控路由质量"""
        while self.active:
            try:
                with self.lock:
                    if not self.active:
                        break
                        
                    for server, route in self.routes.items():
                        # 测试当前延迟
                        current_latency = self.test_latency(server, count=2)
                        route["current_latency"] = current_latency
                        
                        # 如果延迟显著增加，提交优化任务
                        if current_latency > route["original_latency"] * 1.5:
                            logging.info(f"服务器 {server} 延迟显著增加，"
                                       f"从 {route['original_latency']:.0f}ms "
                                       f"到 {current_latency:.0f}ms，准备重新优化")
                            self.executor.submit(self._optimize_route, server)
                            
                        # 更新状态队列
                        self.status_queue.put({
                            "server": server,
                            "latency": current_latency,
                            "improvement": ((route["original_latency"] - current_latency) 
                                         / route["original_latency"] * 100)
                        })
                        
                # 每秒检查一次
                time.sleep(1.0)
                
            except Exception as e:
                logging.error(f"路由监控失败: {str(e)}")
                time.sleep(5.0)

    def _optimize_route(self, server: str) -> bool:
        """优化单个服务器的路由"""
        try:
            logging.info(f"开始优化服务器 {server} 的路由")
            start_time = time.time()
            
            # 获取服务器所属区域
            region = self.current_region
            if not region:
                logging.error(f"未找到服务器 {server} 所属的区域")
                return False
                
            # 获取最佳节点
            best_nodes = self._find_best_nodes(region)
            if not best_nodes:
                logging.error("未找到可用节点")
                return False
                
            # 测试当前延迟作为基准
            current_latency = self.test_latency(server)
            best_latency = current_latency
            best_node = None
            
            # 测试每个候选节点
            for node in best_nodes:
                node_ip = node["ip"]
                logging.info(f"测试节点 {node_ip} 到服务器 {server} 的路由")
                
                # 测试通过节点访问服务器
                if self._add_route(server, node_ip):
                    route_latency = self.test_latency(server)
                    self._delete_route(server)
                    
                    logging.info(f"节点 {node_ip} 延迟: {route_latency:.0f}ms "
                               f"(当前最佳: {best_latency:.0f}ms)")
                    
                    if route_latency < best_latency:
                        best_latency = route_latency
                        best_node = node_ip
                        
            # 如果找到更好的节点，应用新路由
            if best_node and self._add_route(server, best_node):
                with self.lock:
                    self.routes[server].update({
                        "node": best_node,
                        "current_latency": best_latency
                    })
                    
                elapsed = time.time() - start_time
                improvement = ((current_latency - best_latency) / current_latency * 100 
                             if current_latency > 0 else 0)
                             
                logging.info(f"服务器 {server} 路由优化完成，耗时 {elapsed:.1f} 秒\n"
                           f"原始延迟: {current_latency:.0f}ms\n"
                           f"优化后: {best_latency:.0f}ms\n"
                           f"改善: {improvement:+.1f}%")
                return True
                
            logging.warning(f"服务器 {server} 未找到更好的路由")
            return False
            
        except Exception as e:
            logging.error(f"优化路由失败: {str(e)}")
            return False

    def start_acceleration(self, game: str, region: str) -> bool:
        """启动加速"""
        try:
            if self.active:
                logging.warning("加速已在运行中")
                return False
                
            # 获取服务器列表
            self.current_game_servers = self.config.get("game_servers", {}).get(game, {}).get(region, {})
            self.current_region = region
            
            if not self.current_game_servers:
                logging.error(f"未找到游戏 {game} 区服 {region} 的服务器配置")
                return False
                
            logging.info(f"开始加速 {game} - {region}")
            start_time = time.time()
                
            # 清空状态队列
            while not self.status_queue.empty():
                self.status_queue.get_nowait()
                
            # 获取最佳节点
            best_nodes = self._find_best_nodes(region)
            if not best_nodes:
                logging.error("未找到可用节点")
                return False
                
            # 优化每个服务器的路由
            success = True
            total_servers = sum(len(servers) for servers in self.current_game_servers.values())
            processed_servers = 0
            
            for server_group, server_list in self.current_game_servers.items():
                logging.info(f"正在处理服务器组: {server_group}")
                
                for server in server_list:
                    processed_servers += 1
                    logging.info(f"正在优化服务器 ({processed_servers}/{total_servers}): {server}")
                    
                    # 测试原始延迟
                    original_latency = self.test_latency(server)
                    
                    # 初始化路由信息
                    with self.lock:
                        self.routes[server] = {
                            "original_latency": original_latency,
                            "current_latency": original_latency,
                            "node": None
                        }
                        
                    # 优化路由
                    if not self._optimize_route(server):
                        success = False
                        
            if success and self.routes:
                self.active = True
                # 启动监控线程
                self.monitor_future = self.executor.submit(self._monitor_routes)
                
                elapsed = time.time() - start_time
                logging.info(f"加速启动完成，耗时 {elapsed:.1f} 秒，"
                           f"共处理 {len(self.routes)} 个服务器")
                return True
                
            logging.error("加速启动失败，正在清理...")
            self.stop_acceleration()
            return False
            
        except Exception as e:
            logging.error(f"启动加速失败: {str(e)}")
            self.stop_acceleration()
            return False

    def stop_acceleration(self):
        """停止加速"""
        try:
            logging.info("正在停止加速...")
            self.active = False
            
            # 等待监控线程结束
            if self.monitor_future:
                self.monitor_future.cancel()
                self.monitor_future = None
                
            # 清理路由
            with self.lock:
                for server in list(self.routes.keys()):
                    self._delete_route(server)
                self.routes.clear()
                
            # 清空状态队列
            while not self.status_queue.empty():
                self.status_queue.get_nowait()
                
            logging.info("加速已停止，所有路由已清理")
                
        except Exception as e:
            logging.error(f"停止加速失败: {str(e)}")

    def get_status(self) -> Dict:
        """获取状态"""
        with self.lock:
            status = {
                "active": self.active,
                "routes": self.routes.copy()
            }
            
        # 添加实时状态更新
        while not self.status_queue.empty():
            try:
                update = self.status_queue.get_nowait()
                server = update["server"]
                if server in status["routes"]:
                    status["routes"][server]["current_latency"] = update["latency"]
            except:
                break
                
        return status
