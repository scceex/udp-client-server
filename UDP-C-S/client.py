import socket
import time
import struct
import sys
import threading

# 定义报文格式和头部大小
_PACKET_FORMAT = '!IHQ8s'  # 网络字节序，无符号整数，无符号短整数，无符号长长整数，8字节字符串
_PACKET_HEADER_SIZE = struct.calcsize(_PACKET_FORMAT)

# 构建报文
def _build_packet(sequence_number, ver, payload):
    timestamp = int(time.time() * 1000)  # 毫秒级时间戳
    packet = struct.pack(_PACKET_FORMAT, sequence_number, ver, timestamp, payload.encode('utf-8'))
    return packet

# 发送请求
def _send_request(seq_no, ver, payload, server_ip, server_port, client_socket):
    request_data = _build_packet(seq_no, ver, payload)
    client_socket.sendto(request_data, (server_ip, server_port))
    print(f"Sent request, Seq No: {seq_no}, Payload: {payload}")

# 接收响应
def _receive_response(client_socket):
    try:
        data, server_address = client_socket.recvfrom(1024)
        sequence_number, ver, timestamp, response_payload = struct.unpack(_PACKET_FORMAT, data)
        return sequence_number, timestamp, response_payload.decode('utf-8')
    except socket.timeout:
        return None, None, None

# 主循环
_received_packets = 0
_total_packets = 12
_dropped_packets = 0
_rtt_values = []
_start_time = time.time()

# 从命令行参数获取服务器IP、端口和有效载荷
if len(sys.argv) != 4:
    print("Usage: client.py server_ip server_port payload")
    sys.exit(1)

_server_ip = sys.argv[1]
_server_port = int(sys.argv[2])
_payload = sys.argv[3]

# 创建UDP套接字并设置超时
_client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
_client_socket.bind(('127.0.0.1', 54321))  # 绑定客户端IP和端口
_client_socket.settimeout(0.1)  # 设置超时时间为100ms

# 模拟 TCP 连接建立过程
time.sleep(1)

try:
    for seq_no in range(1, _total_packets + 1):
        _send_request(seq_no, 2, _payload, _server_ip, _server_port, _client_socket)
        
        # 接收响应
        for _ in range(3):  # 尝试接收3次
            seq_no_response, server_timestamp, response_payload = _receive_response(_client_socket)
            if seq_no_response is not None:
                _received_packets += 1
                rtt = (time.time() - _start_time) * 1000  # 计算RTT，单位为毫秒
                _rtt_values.append(rtt)
                print(f"Received response, Seq No: {seq_no_response}, Server IP:Port {_server_ip}:{_server_port}, RTT: {rtt} ms")
                break
        else:
            print(f"Request {seq_no} timed out")
            _dropped_packets += 1
        time.sleep(0.1)  # 重传间隔

    # 计算统计信息
    if _rtt_values:
        max_rtt = max(_rtt_values)
        min_rtt = min(_rtt_values)
        avg_rtt = sum(_rtt_values) / len(_rtt_values)
        std_dev_rtt = (sum((x - avg_rtt) ** 2 for x in _rtt_values) / len(_rtt_values)) ** 0.5
    else:
        max_rtt = min_rtt = avg_rtt = std_dev_rtt = 0

    # 打印汇总信息
    print("\n汇总：")
    print(f"接收到 UDP 数据包：{_received_packets}")
    print(f"丢包率：{_dropped_packets / _total_packets * 100}%")
    print(f"最大 RTT：{max_rtt} 毫秒，最小 RTT：{min_rtt} 毫秒，平均 RTT：{avg_rtt} 毫秒，RTT 标准差：{std_dev_rtt} 毫秒")

    # 计算服务器整体响应时间
    server_overall_response_time = time.time() - _start_time
    print(f"服务器整体响应时间：{server_overall_response_time:.2f} 秒")

    # 模拟 TCP 连接释放过程
    time.sleep(1)  # 等待1秒以模拟 TCP 连接释放过程

except KeyboardInterrupt:
    print("Client shutting down...")
finally:
    _client_socket.close()  # 关闭套接字
    print("客户端关闭连接。")

