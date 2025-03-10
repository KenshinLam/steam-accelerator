import socket
import time
import statistics
from concurrent.futures import ThreadPoolExecutor

def test_tcp_latency(host, port=80, count=4, timeout=2):
    """使用TCP连接测试延迟"""
    latencies = []
    
    try:
        # 首先解析域名
        try:
            ip = socket.gethostbyname(host)
        except socket.gaierror:
            print(f"无法解析主机名: {host}")
            return 999.0
            
        # 测试多次连接延迟
        for _ in range(count):
            try:
                start_time = time.time()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                
                # 尝试连接
                result = sock.connect_ex((ip, port))
                end_time = time.time()
                
                if result == 0:
                    latency = (end_time - start_time) * 1000  # 转换为毫秒
                    latencies.append(latency)
                
                sock.close()
                
            except (socket.timeout, socket.error) as e:
                print(f"连接 {host} 失败: {str(e)}")
                continue
                
            time.sleep(0.2)  # 短暂延迟避免过快发送请求
            
        # 计算平均延迟
        if latencies:
            # 移除最高和最低值，计算平均值
            if len(latencies) > 2:
                latencies.remove(max(latencies))
                latencies.remove(min(latencies))
            return statistics.mean(latencies)
            
        return 999.0
        
    except Exception as e:
        print(f"测试延迟失败: {str(e)}")
        return 999.0

def main():
    # 游戏服务器列表（使用实际可访问的服务器）
    game_servers = {
        "DotA2": {
            "国服": [
                ("steamcn.com", 80),           # Steam中文社区
                ("store.steampowered.com", 80)  # Steam商店
            ],
            "东南亚": [
                ("steamcommunity.com", 443),    # Steam社区
                ("api.steampowered.com", 443)   # Steam API
            ]
        },
        "CS2": {
            "国服": [
                ("steamcn.com", 80),           # Steam中文社区
                ("steamcommunity.com", 443)     # Steam社区
            ],
            "香港": [
                ("store.steampowered.com", 443), # Steam商店
                ("api.steampowered.com", 443)    # Steam API
            ]
        },
        "通用服务器": {
            "国内": [
                ("steamcn.com", 80),            # Steam中文社区
                ("store.steampowered.com", 80)  # Steam商店
            ],
            "海外": [
                ("store.steampowered.com", 443), # Steam商店
                ("steamcommunity.com", 443)      # Steam社区
            ]
        }
    }

    print("开始测试游戏服务器延迟...")
    print("=" * 50)
    
    for game, regions in game_servers.items():
        print(f"\n{game}:")
        print("-" * 20)
        
        for region, servers in regions.items():
            print(f"\n{region}:")
            for server, port in servers:
                latency = test_tcp_latency(server, port)
                status = f"{latency:.1f}ms" if latency < 999.0 else "超时"
                print(f"  {server}:{port} - {status}")

if __name__ == '__main__':
    main()
