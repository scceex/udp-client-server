import socket
import random
import time
import struct
import threading

# 定义报文格式和头部大小
_PACKET_FORMAT = '!IHQ8s'  # 网络字节序，无符号整数，无符号短整数，无符号长长整数，8字节字符串
_PACKET_HEADER_SIZE = struct.calcsize(_PACKET_FORMAT)

# 解析接收到的报文
def _parse_packet(packet):
    if len(packet) < _PACKET_HEADER_SIZE:
        return None
    sequence_number, ver, timestamp, payload = struct.unpack(_PACKET_FORMAT, packet)
    return sequence_number, ver, timestamp, payload.decode('utf-8')

# 模拟丢包
def _simulate_packet_loss(drop_rate):
    return random.random() < drop_rate

# 处理客户端请求的函数
def _handle_client_request(client_address, data):
    # 解析客户端发送的数据
    packet = _parse_packet(data)
    if packet is None:
        print("Invalid packet received.")
        return
    
    sequence_number, ver, timestamp, payload = packet
    print(f"Received request from {client_address}, Seq No: {sequence_number}, Ver: {ver}, Timestamp: {timestamp}, Payload: {payload}")
    
    # 模拟丢包
    if _simulate_packet_loss(0.15):  # 假设丢包率为15%
        print(f"Simulating packet loss for Seq No: {sequence_number}")
        return

    # 构建响应报文
    response_payload = f"Response to request {sequence_number}".encode('utf-8')
    response_timestamp = int(time.time() * 1000)  # 更新响应的系统时间戳
    response_data = struct.pack(_PACKET_FORMAT, sequence_number, ver, response_timestamp, response_payload)
    
    # 发送响应报文
    _server_socket.sendto(response_data, client_address)
    sent_response_time = time.time()  # 记录发送响应的时间
    print(f"Sent response to {client_address}, Seq No: {sequence_number}, Sent Time: {sent_response_time}")

    # 更新服务器响应时间
    global _first_response_time
    if _first_response_time is None:
        _first_response_time = sent_response_time
    server_response_duration = sent_response_time - _first_response_time
    print(f"Server's overall response time: {server_response_duration:.2f} seconds")

# 客户端处理线程
def _client_thread(client_address, data):
    _handle_client_request(client_address, data)

# 服务器的IP和端口
_server_ip = '127.0.0.1'
_server_port = 12345

# 创建UDP套接字并绑定
_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
_server_socket.bind((_server_ip, _server_port))
print(f"Server is listening on {_server_ip}:{_server_port}")

# 第一次响应的时间戳
_first_response_time = None

# 主循环
try:
    while True:
        data, client_address = _server_socket.recvfrom(1024)
        threading.Thread(target=_client_thread, args=(client_address, data)).start()
except KeyboardInterrupt:
    print("Server shutting down...")
finally:
    _server_socket.close()  # 关闭套接字
    print("服务器关闭连接。")
