default_config = """logging:    # 日志
    default: "info"
    handlers:
        info:
            -   &console_handler
                type: "console"
                format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            -   &file_handler
                type: "file"
                format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                log_path: "logs"
        debug:
            - 
                <<: *file_handler
        error:
            - 
                <<: *console_handler
            - 
                <<: *file_handler
system:     # 系统配置
    thread_workers: null
llm:        # 大模型
    default: "qwen"
    models: 
        "deepseek":
            name: "deepseek-v4-flash"
            key_name: "DEEPSEEK_API_KEY"
            base_url: "https://api.deepseek.com"
            stream: true
            extra_body:
                "thinking":
                    thinking: "disabled"
        "qwen":
            name: "qwen3.6-plus"
            key_name: "DASHSCOPE_API_KEY"
            base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
            stream: true
            extra_body:
                enable_thinking : false
        "kimi":
            name: "kimi-k2-thinking"
            key_name: "KIMI_API_KEY"
            base_url: "https://api.moonshot.cn/v1"
            extra_body:
                thinking:
                    type: "disabled"
        "doubao":
            name: "doubao-1-5-pro-32k-250115"
            key_name: "DOUAO_API_KEY"
            base_url: "https://ark.cn-beijing.volces.com/api/v3"
            extra_body:
                thinking: 
                    type: disabled
"""