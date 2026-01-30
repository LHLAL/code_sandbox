# Manus Safe Sandbox

这是一个基于 FastAPI 实现的高性能、多层限制的 Python 执行沙箱。

## 核心安全特性

1.  **AST 静态分析**：在执行前对 Python 代码进行抽象语法树分析，禁止危险的导入（如 `os`, `sys`）和危险的属性访问（如 `__subclasses__`）。
2.  **Builtins 限制**：通过自定义 `__builtins__` 环境，在运行时禁用 `eval`, `exec`, `open` 等高危函数。
3.  **gVisor 隔离**：推荐在生产环境中使用 gVisor (runsc) 运行时，提供内核级的强隔离。
4.  **请求限流**：内置基于 IP 的限流机制，防止拒绝服务攻击（DoS）。
5.  **资源限制**：支持通过线程池和配置参数优化并发处理能力。

## 快速开始

### 1. 配置文件

配置文件位于 `config/config.yaml`，您可以修改线程池大小、端口、限流规则等。

### 2. Docker 部署

```bash
# 构建镜像
docker build -t manus-sandbox .

# 运行镜像（挂载宿主机配置）
docker run -p 8000:8000 -v $(pwd)/config/config.yaml:/app/config/config.yaml manus-sandbox
```

### 3. 使用 gVisor (生产环境推荐)

确保宿主机已安装 gVisor，运行：

```bash
docker run --runtime=runsc -p 8000:8000 manus-sandbox
```

## API 接口

### 执行代码

**POST** `/execute`

**请求体**:

```json
{
  "code": "result = a + b",
  "inputs": {"a": 1, "b": 2},
  "language": "python"
}
```

**响应**:

```json
{
  "success": true,
  "stdout": "",
  "result": {"result": 3},
  "error": null
}
```

## Node.js 扩展

项目已在 `app/api/router.py` 中预留了 `nodejs` 执行分支，您可以后续集成 `vm2` 或 `isolated-vm` 来实现 Node.js 沙箱。

## 多架构支持 (x86_64 & 麒麟 V10 ARM64)

本项目支持在不同 CPU 架构下构建镜像：

### 1. 针对 x86_64 架构
```bash
docker build -f Dockerfile.x86 -t sandbox:x86_64 .
```

### 2. 针对 麒麟 V10 (ARM64) 架构
```bash
docker build -f Dockerfile.arm64 -t sandbox:arm64 .
```

### 3. 使用构建脚本
我们提供了一个交互式脚本 `build.sh` 来简化构建过程：
```bash
chmod +x build.sh
./build.sh
```

**注意**：在麒麟 V10 环境下，`Dockerfile.arm64` 默认使用了华为云镜像源以加速构建过程。
