FROM ubuntu:22.04

# 避免交互式提示
ENV DEBIAN_FRONTEND=noninteractive

# 安装基础依赖和软件源管理工具
RUN apt-get update && apt-get install -y \
    software-properties-common \
    curl \
    zip \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update

# 安装不同版本的 Python
RUN apt-get install -y \
    python3.9 python3.9-dev \
    python3.10 python3.10-dev \
    python3.11 python3.11-dev \
    python3-pip

# 设置工作目录
WORKDIR /app

# 安装项目所需的 Python 依赖
# 使用系统默认 Python (3.10) 安装服务端依赖
RUN pip3 install --no-cache-dir fastapi uvicorn PyYAML pydantic slowapi pytest httpx

# 复制项目文件
COPY . .

# 创建配置目录
RUN mkdir -p /app/config

# 环境变量
ENV SANDBOX_CONFIG_PATH=/app/config/config.yaml

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python3", "main.py"]
