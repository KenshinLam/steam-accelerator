import subprocess
import socket
import threading
import time
from scapy.all import *
import requests
import json
import concurrent.futures
import os
import logging
import ipaddress
from typing import Dict, List, Tuple

class RouteOptimizer:
    def __init__(self):
        self.routes = {}
        self.config = self._load_config()
        self.lock = threading.Lock()
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.config.get('settings', {}).get('parallel_tests', 5)
        )
        
    def _load_config(self):
        """从配置加载配置信息"""
        try:
            config_path = os.getenv('ACCELERATOR_CONFIG', 'config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    logging.info("成功加载配置文件")
                    return config
            logging.warning("配置文件不存在，使用默认配置")
            return {}
        except json.JSONDecodeError as e:
            logging.error(f"配置文件格式错误: {str(e)}")
            return {}
        except Exception as e:
            logging.error(f"加载配置失败: {str(e)}")
            return {}

    def _validate_ip(self, ip):
        """验证IP地址格式"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    def test_latency(self, host: str, count: int = 4, timeout: int = 1, max_retries: int = 3) -> float:
        """测试到目标主机的延迟，支持重试"""
        if not self._validate_ip(host):
            logging.error(f"无效的IP地址: {host}")
            return 999.0
            
        for retry in range(max_retries):
            try:
                # 直接测试到目标的延迟
                result = subprocess.run(
                    ['ping', '-n', str(count), '-w', str(timeout * 1000), host],
                    capture_output=True,
                    text=True,
                    timeout=timeout * count
                )
                
                if result.returncode == 0:
                    output = result.stdout
                    if "平均 = " in output:
                        avg = output.split("平均 = ")[-1].split("ms")[0]
                        latency = float(avg)
                        logging.debug(f"测试延迟成功: {host} -> {latency}ms")
                        return latency
                    elif "Average = " in output:
                        avg = output.split("Average = ")[-1].split("ms")[0]
                        latency = float(avg)
                        logging.debug(f"测试延迟成功: {host} -> {latency}ms")
                        return latency
                        
                if retry < max_retries - 1:
                    logging.warning(f"Ping失败，正在重试({retry + 1}/{max_retries}): {host}")
                    time.sleep(0.5)  # 重试前等待
                    continue
                    
                logging.warning(f"无法解析ping结果: {host}")
                return 999.0
                
            except subprocess.TimeoutExpired:
                if retry < max_retries - 1:
                    logging.warning(f"Ping超时，正在重试({retry + 1}/{max_retries}): {host}")
                    time.sleep(0.5)  # 重试前等待
                    continue
                logging.warning(f"Ping超时: {host}")
                return 999.0
            except Exception as e:
                if retry < max_retries - 1:
                    logging.error(f"测试延迟失败，正在重试({retry + 1}/{max_retries}): {host} - {str(e)}")
                    time.sleep(0.5)  # 重试前等待
                    continue
                logging.error(f"测试延迟失败: {host} - {str(e)}")
                return 999.0
                
        return 999.0

    def _test_latency_parallel(self, hosts: List[str]) -> Dict[str, float]:
        """并行测试多个主机的延迟"""
        futures = []
        results = {}
        
        # 提交所有测试任务
        for host in hosts:
            future = self.executor.submit(
                self.test_latency,
                host,
                self.config.get('settings', {}).get('test_count', 4),
                self.config.get('settings', {}).get('test_timeout', 2),
                self.config.get('settings', {}).get('max_retries', 3)
            )
            futures.append((host, future))
            
        # 收集测试结果
        for host, future in futures:
            try:
                latency = future.result()
                results[host] = latency
            except Exception as e:
                logging.error(f"测试延迟失败: {host} - {str(e)}")
                results[host] = 999.0
                
        return results

    def get_servers_for_game(self, game: str, region: str) -> List[str]:
        """获取指定游戏和区域的服务器列表"""
        try:
            servers = []
            game_servers = self.config.get("game_servers", {}).get(game, {}).get(region, {})
            
            if not game_servers:
                logging.warning(f"未找到游戏服务器配置: {game} - {region}")
                return []
                
            for provider, provider_servers in game_servers.items():
                if provider_servers:
                    servers.extend(provider_servers)
                    logging.debug(f"加载 {provider} 服务器: {len(provider_servers)}个")
                    
            if servers:
                logging.info(f"找到 {len(servers)} 个服务器: {game} - {region}")
            else:
                logging.warning(f"未找到任何服务器: {game} - {region}")
                
            return servers
            
        except Exception as e:
            logging.error(f"获取服务器列表失败: {str(e)}")
            return []

    def get_nodes_for_region(self, region: str) -> List[str]:
        """获取指定区域的加速节点列表"""
        try:
            nodes = []
            region_nodes = self.config.get("nodes", {}).get(region, [])
            
            if not region_nodes:
                logging.warning(f"未找到区域节点配置: {region}")
                return []
                
            if isinstance(region_nodes, list):
                nodes.extend([node["ip"] for node in region_nodes])
                logging.debug(f"加载区域节点: {len(nodes)}个")
            else:
                for isp, isp_nodes in region_nodes.items():
                    if isp_nodes:
                        isp_ips = [node["ip"] for node in isp_nodes]
                        nodes.extend(isp_ips)
                        logging.debug(f"加载 {isp} 节点: {len(isp_ips)}个")
                        
            if nodes:
                logging.info(f"找到 {len(nodes)} 个加速节点: {region}")
            else:
                logging.warning(f"未找到任何加速节点: {region}")
                
            return nodes
            
        except Exception as e:
            logging.error(f"获取节点列表失败: {str(e)}")
            return []

    def apply_route(self, host: str, node: str) -> bool:
        """应用路由规则"""
        if not self._validate_ip(host) or not self._validate_ip(node):
            logging.error(f"无效的IP地址: host={host}, node={node}")
            return False
            
        try:
            with self.lock:
                # 删除现有路由
                subprocess.run(['route', 'delete', host], capture_output=True)
                
                # 添加新路由
                result = subprocess.run(
                    ['route', 'add', host, 'mask', '255.255.255.255', node],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    logging.error(f"添加路由失败: {result.stderr}")
                    return False
                    
                # 验证路由是否添加成功
                verify = subprocess.run(
                    ['route', 'print', host],
                    capture_output=True,
                    text=True
                )
                
                if node in verify.stdout:
                    logging.info(f"成功添加路由: {host} -> {node}")
                    return True
                else:
                    logging.error(f"路由验证失败: {host} -> {node}")
                    return False
                    
        except Exception as e:
            logging.error(f"应用路由失败: {host} -> {node} - {str(e)}")
            return False

    def _find_best_route(self, server: str, nodes: List[str]) -> Tuple[str, float, float]:
        """找到最佳的加速路径
        
        评分标准：
        1. 节点延迟权重: 40%
        2. 节点到游戏服务器延迟权重: 40%
        3. 节点稳定性权重: 20%
        """
        # 测试服务器原始延迟
        original_latency = self.test_latency(server)
        logging.info(f"测试原始延迟: {server} -> {original_latency}ms")
        
        # 并行测试所有节点延迟
        node_scores = {}
        stability_tests = 3  # 测试3次来评估稳定性
        
        for node in nodes:
            # 1. 测试节点延迟（权重40%）
            node_latencies = []
            for _ in range(stability_tests):
                latency = self.test_latency(node)
                if latency < 999.0:  # 排除超时的测试
                    node_latencies.append(latency)
                time.sleep(0.2)  # 短暂延迟避免过于频繁
                
            if not node_latencies:
                logging.warning(f"节点 {node} 无法连接")
                continue
                
            avg_node_latency = sum(node_latencies) / len(node_latencies)
            latency_variance = sum((l - avg_node_latency) ** 2 for l in node_latencies) / len(node_latencies)
            
            # 2. 测试节点到游戏服务器的延迟（权重40%）
            server_latencies = []
            for _ in range(stability_tests):
                # 临时应用路由规则
                if self.apply_route(server, node):
                    latency = self.test_latency(server)
                    if latency < 999.0:
                        server_latencies.append(latency)
                    self.remove_route(server)  # 清理临时路由
                time.sleep(0.2)
                
            if not server_latencies:
                logging.warning(f"无法通过节点 {node} 连接服务器")
                continue
                
            avg_server_latency = sum(server_latencies) / len(server_latencies)
            server_variance = sum((l - avg_server_latency) ** 2 for l in server_latencies) / len(server_latencies)
            
            # 3. 计算稳定性得分（权重20%）
            stability_score = 100 - min(100, (latency_variance + server_variance) / 2)
            
            # 4. 计算综合得分
            # 延迟得分满分100分，延迟越低分越高
            node_latency_score = max(0, 100 - (avg_node_latency / 2))  # 200ms以上得0分
            server_latency_score = max(0, 100 - (avg_server_latency / 2))  # 200ms以上得0分
            
            total_score = (
                node_latency_score * 0.4 +    # 节点延迟权重40%
                server_latency_score * 0.4 +  # 服务器延迟权重40%
                stability_score * 0.2         # 稳定性权重20%
            )
            
            node_scores[node] = {
                'score': total_score,
                'node_latency': avg_node_latency,
                'server_latency': avg_server_latency,
                'stability': stability_score
            }
            
            logging.info(f"节点评分 - {node}:")
            logging.info(f"  节点延迟: {avg_node_latency:.1f}ms (得分: {node_latency_score:.1f})")
            logging.info(f"  服务器延迟: {avg_server_latency:.1f}ms (得分: {server_latency_score:.1f})")
            logging.info(f"  稳定性: {stability_score:.1f}%")
            logging.info(f"  总分: {total_score:.1f}")
            
        if not node_scores:
            logging.warning("没有找到可用的加速节点")
            return None, 999.0, original_latency
            
        # 选择得分最高的节点
        best_node = max(node_scores.items(), key=lambda x: x[1]['score'])
        node_ip = best_node[0]
        node_data = best_node[1]
        
        logging.info(f"\n选择最优节点: {node_ip}")
        logging.info(f"  综合得分: {node_data['score']:.1f}")
        logging.info(f"  预期延迟: {node_data['server_latency']:.1f}ms")
        logging.info(f"  延迟改善: {original_latency - node_data['server_latency']:.1f}ms")
        logging.info(f"  稳定性: {node_data['stability']:.1f}%")
        
        return node_ip, node_data['server_latency'], original_latency

    def optimize_route(self, host: str, region: str) -> bool:
        """优化到指定主机的路由"""
        if not self._validate_ip(host):
            logging.error(f"无效的IP地址: {host}")
            return False
            
        try:
            # 获取区域节点
            nodes = self.get_nodes_for_region(region)
            if not nodes:
                logging.warning(f"未找到加速节点: {region}")
                return False
                
            # 找到最佳路径
            best_node, best_latency, original_latency = self._find_best_route(host, nodes)
            
            if best_node and best_latency < original_latency:
                logging.info(f"尝试优化路由: {host} -> {best_node}")
                
                # 应用路由规则
                if self.apply_route(host, best_node):
                    # 测试优化后的延迟
                    optimized_latency = self.test_latency(host)
                    logging.info(f"测试优化后延迟: {host} -> {optimized_latency}ms")
                    
                    if optimized_latency < original_latency:
                        with self.lock:
                            self.routes[host] = {
                                'node': best_node,
                                'original_latency': original_latency,
                                'optimized_latency': optimized_latency,
                                'improvement': original_latency - optimized_latency
                            }
                        logging.info(f"成功优化路由: {host} -> {best_node} (优化前: {original_latency}ms, 优化后: {optimized_latency}ms)")
                        return True
                    else:
                        # 如果优化后延迟反而更高，回滚路由
                        self.remove_route(host)
                        logging.warning(f"优化效果不佳，已回滚: {host} (优化前: {original_latency}ms, 优化后: {optimized_latency}ms)")
                        return False
                        
            logging.info(f"未找到更优路径: {host}")
            return False
            
        except Exception as e:
            logging.error(f"优化路由失败: {host} - {str(e)}")
            return False

    def remove_route(self, host: str) -> bool:
        """移除指定主机的路由规则"""
        if not self._validate_ip(host):
            logging.error(f"无效的IP地址: {host}")
            return False
            
        try:
            with self.lock:
                # 删除路由规则
                result = subprocess.run(
                    ['route', 'delete', host],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    logging.error(f"删除路由失败: {host} - {result.stderr}")
                    return False
                
                if host in self.routes:
                    del self.routes[host]
                    
                logging.info(f"成功移除路由: {host}")
                return True
                
        except Exception as e:
            logging.error(f"移除路由失败: {host} - {str(e)}")
            return False