content = """
# Stdio类型配置
# [(MCP名称)]
# command = "启动命令"
# disabled = "[可选]是否禁用此MCP Server，默认false"
# args = "[可选]启动参数"
# env = "[可选]环境变量"
# desc = "[可选]描述"
# ------------------是分割线------------------
# StreamableHTTP类型配置
# [(MCP名称)]
# url = "MCP Server地址"
# disabled = "[可选]是否禁用此MCP Server，默认false"
# headers = "[可选]请求头"
# auth = "[可选]Auth授权配置"
# desc = "[可选]描述"

# Auth授权配置内容
# [auth]
# callback_url = "回调地址，授权成功后请求的地址"
# redirect_uris = "重定向地址"

# ------------------最小实例------------------
# [WebSearch]
# url = "https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/mcp"
# headers = { Authorization = "Bearer ${API_KEY}" }     # '${ENV_NAME}'会从系统环境变量中查找并替换ENV_NAME的值

# ["@modelcontextprotocol/server-filesystem"]
# command = "npx"
# args = [ "-y", "@modelcontextprotocol/server-filesystem" ]
"""