default_config = """mode="server"       # 网关模式

[server]
host="127.0.0.1"    # 监听地址
port=8866           # 监听端口
token="token_abc"   # token
max_count=5         # 最大连接数
timeout_ms=5000     # 心跳超时时间，0时不检查

[client]
protocal="ws"       # 连接协议
host="127.0.0.1"    # 连接地址
port=8866           # 连接端口
token="token_abc"   # 连接token
health_ms=5000      # 心跳间隔，0时不发送


# 应用列表 mode 为 server 时有效
[[apps]]
appid="123456"
name="app1"
"""