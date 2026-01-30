# Manus Safe Sandbox - 生产级 Python 执行沙箱

## 概述

本项目实现了一个基于 **FastAPI** 的高性能、多层安全限制的 Python 代码执行沙箱服务。它旨在提供一个类似 Dify-Sandbox 的、可信赖的、高并发的代码执行环境，特别针对生产环境的安全性和可扩展性进行了优化。

## 核心架构与安全机制

本沙箱采用了 **“层层限制”** 的多级安全防护体系，确保用户代码在隔离环境中安全运行。

| 安全层级 | 机制 | 描述 | 目的 |
| :--- | :--- | :--- | :--- |
| **L1: 静态分析** | **AST 检查** | 在代码执行前，通过抽象语法树（AST）静态分析，禁止导入 `os`, `sys`, `subprocess` 等危险模块，以及访问高危属性（如 `__subclasses__`）。 | 预防代码注入和系统级操作。 |
| **L2: 运行时限制** | **Builtins 隔离** | 在子进程执行环境中，通过自定义 `__builtins__` 字典，禁用 `eval`, `exec`, `open` 等高危内置函数。 | 阻止运行时动态代码执行和文件系统访问。 |
| **L3: 进程隔离** | **子进程执行** | 每次代码执行都在一个独立的子进程中完成，并通过 `subprocess` 严格控制 I/O 和超时。 | 避免用户代码污染主服务进程，实现资源隔离。 |
| **L4: 容器隔离** | **gVisor 集成** | 推荐在生产环境中使用 gVisor (`--runtime=runsc`) 容器运行时，提供内核级的强隔离，显著降低容器逃逸风险。 | 提供最强的系统级安全边界。 |
| **L5: 服务限流** | **SlowAPI 限流** | 内置基于 IP 的请求限流机制，防止恶意用户通过高频请求进行拒绝服务攻击（DoS）。 | 保护 API 服务的可用性。 |

## 功能特性

*   **高性能**：基于 FastAPI + Uvicorn，支持高并发和可配置的线程池优化。
*   **多版本 Python**：支持通过 `language` 参数指定 Python 版本（如 `python3.9`, `python3.10`, `python3.11`）。
*   **参数化执行**：支持通过 Base64 编码的 JSON 参数，自动解码后作为 `main(obj)` 函数的参数传入。
*   **配置化管理**：通过 `config/config.yaml` 文件集中管理所有核心参数（端口、线程池、限流规则、受限函数/模块）。
*   **多架构支持**：提供针对 **x86_64** 和 **麒麟 V10 (ARM64)** 的 Dockerfile，方便在不同国产化平台上部署。
*   **Node.js 预留**：预留了 Node.js 语言分支，方便未来扩展。

## 部署指南

### 1. 环境准备

确保您已安装 Docker 和 Docker Compose。

### 2. 配置修改

修改 `config/config.yaml` 文件以适应您的生产环境需求：

| 参数 | 描述 | 默认值 |
| :--- | :--- | :--- |
| `port` | 服务监听端口 | `8000` |
| `workers` | Uvicorn 工作进程数 | `4` |
| `max_thread_pool_size` | Python 执行线程池最大线程数（影响并发） | `100` |
| `rate_limit` | API 限流规则（例如：100次/分钟） | `"100/minute"` |
| `python_forbidden_modules` | AST 检查禁止导入的模块列表 | `["os", "sys", ...]` |

### 3. 多架构 Docker 构建

本项目提供了针对不同架构的 Dockerfile，并附带了构建脚本。

| 架构 | Dockerfile | 描述 |
| :--- | :--- | :--- |
| **x86_64** | `Dockerfile.x86` | 适用于标准 Intel/AMD 服务器。 |
| **ARM64** | `Dockerfile.arm64` | 适用于麒麟 V10、鲲鹏等 ARM 架构服务器。 |

**使用构建脚本 (推荐)**：
```bash
chmod +x build.sh
./build.sh
```

**手动构建示例**：
```bash
# 构建 x86_64 镜像
docker build -f Dockerfile.x86 -t manus-sandbox:x86_64 .

# 运行镜像（挂载宿主机配置）
docker run -d -p 8000:8000 \
    -v $(pwd)/config/config.yaml:/app/config/config.yaml \
    manus-sandbox:x86_64
```

### 4. gVisor 增强隔离 (生产环境推荐)

如果您的宿主机支持 gVisor，请使用 `--runtime=runsc` 启动容器以获得更强的隔离性：

```bash
docker run -d -p 8000:8000 --runtime=runsc manus-sandbox:x86_64
```

## API 接口文档

### 1. 健康检查

用于验证服务是否正常运行。

*   **方法**: `GET`
*   **路径**: `/health`
*   **响应**: `{"status": "ok", "message": "Sandbox is healthy"}`

### 2. 代码执行

用于提交代码并获取执行结果。

*   **方法**: `POST`
*   **路径**: `/v1/sandbox/run`
*   **请求体**:

| 字段 | 类型 | 描述 | 示例 |
| :--- | :--- | :--- | :--- |
| `code` | `string` | 完整的 Python 代码块，包含 `main(obj)` 函数定义。 | `def main(obj):\n    print(obj['data'])` |
| `language` | `string` | 指定 Python 版本。 | `"python3.10"` |
| `args` | `string` | Base64 编码的 JSON 字符串，将作为 `main(obj)` 的参数。 | `"eyJuYW1lIjogIk1hbnVzIn0="` |

*   **响应体**:

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "stdout": "Processing user: Manus", // 包含标准输出和执行结果
    "error": ""                       // 错误详情（如安全拦截或运行时异常）
  }
}
```

| 响应字段 | 描述 |
| :--- | :--- |
| `code` | `0` 表示成功（代码执行完成），`1` 表示失败（系统错误或安全拦截）。 |
| `message` | 状态描述。 |
| `data.stdout` | 用户代码的标准输出。 |
| `data.error` | 详细的错误信息（如 AST 拦截信息、超时信息等）。 |

## 安全测试

项目内置了全面的安全测试套件 (`tests/`)，覆盖了 AST 检查、Builtins 限制、API 功能和多版本执行。

```bash
# 在项目根目录执行
PYTHONPATH=. pytest tests/
```
