import socket
import time
import statistics

def test_tcp_latency(host, port=80, count=2, timeout=2):
    """测试TCP连接延迟"""
    latencies = []
    
    try:
        # 解析域名
        try:
            ip = socket.gethostbyname(host)
        except socket.gaierror:
            print(f"无法解析主机名: {host}")
            return 999.0
            
        # 测试连接延迟
        for _ in range(count):
            try:
                start_time = time.time()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                
                result = sock.connect_ex((ip, port))
                end_time = time.time()
                
                if result == 0:
                    latency = (end_time - start_time) * 1000
                    latencies.append(latency)
                
                sock.close()
                
            except (socket.timeout, socket.error) as e:
                print(f"连接 {host} 失败: {str(e)}")
                continue
                
            time.sleep(0.2)
            
        if latencies:
            return statistics.mean(latencies)
            
        return 999.0
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return 999.0

def format_latency(latency):
    return f"{latency:.1f}ms" if latency < 999.0 else "超时"

def main():
    # 关键服务器
    servers = {
        "Steam商店": ("store.steampowered.com", 443),
        "Steam社区": ("steamcommunity.com", 443),
        "Steam API": ("api.steampowered.com", 443)
    }
    
    # 加速节点
    nodes = [
        {"name": "上海电信", "ip": "116.211.105.100"},
        {"name": "北京联通", "ip": "123.125.81.6"},
        {"name": "香港节点", "ip": "119.81.135.50"}
    ]
    
    print("测试服务器直连延迟...")
    print("-" * 30)
    server_latencies = {}
    for name, (host, port) in servers.items():
        latency = test_tcp_latency(host, port)
        server_latencies[name] = latency
        print(f"{name}: {format_latency(latency)}")
    
    print("\n测试加速节点延迟...")
    print("-" * 30)
    for node in nodes:
        print(f"\n{node['name']} ({node['ip']}):")
        latency = test_tcp_latency(node['ip'])
        if latency < 999.0:
            print(f"节点延迟: {format_latency(latency)}")
            
            # 测试通过节点访问服务器
            for name, (host, port) in servers.items():
                server_latency = server_latencies[name]
                if server_latency < 999.0:
                    total_latency = latency + test_tcp_latency(host, port)
                    if total_latency < server_latency:
                        improvement = ((server_latency - total_latency) / server_latency) * 100
                        print(f"{name}:")
                        print(f"  直连延迟: {format_latency(server_latency)}")
                        print(f"  优化延迟: {format_latency(total_latency)}")
                        print(f"  改善程度: {improvement:.1f}%")
        else:
            print("节点不可用")

if __name__ == '__main__':
    main()
