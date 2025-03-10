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
    # 东南亚服务器
    servers = {
        "新加坡DotA2": ("103.28.54.1", 27015),     # DotA2 新加坡服务器
        "新加坡CS2": ("103.10.124.1", 27015),      # CS2 新加坡服务器
        "香港Steam": ("119.81.135.1", 443),        # 香港 Steam CDN
        "日本Steam": ("203.104.128.31", 443)       # 日本 Steam CDN
    }
    
    # 东南亚加速节点
    nodes = [
        {"name": "香港 PCCW", "ip": "203.186.83.208"},
        {"name": "新加坡 M1", "ip": "103.102.128.68"},
        {"name": "东京 NTT", "ip": "203.104.128.31"},
        {"name": "台北 HiNet", "ip": "210.71.198.1"}
    ]
    
    print("测试东南亚服务器直连延迟...")
    print("-" * 30)
    server_latencies = {}
    for name, (host, port) in servers.items():
        latency = test_tcp_latency(host, port)
        server_latencies[name] = latency
        print(f"{name}: {format_latency(latency)}")
    
    print("\n测试东南亚加速节点延迟...")
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
