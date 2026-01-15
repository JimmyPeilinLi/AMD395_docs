# llama.cpp 运行指南

本文档详细说明如何在 AMD Strix Halo 上运行 llama.cpp。

## 可执行文件位置

```
~/llama.cpp/build/bin/
├── llama-cli          # 命令行推理工具
├── llama-server       # OpenAI 兼容 API 服务器
├── llama-quantize     # 模型量化工具
├── llama-bench        # 性能基准测试
├── llama-perplexity   # 困惑度评估
└── ...
```

## 基本命令格式

```bash
~/llama.cpp/build/bin/llama-cli -m <模型路径> [选项]
```

## 常用运行方式

### 1. 交互式对话

```bash
~/llama.cpp/build/bin/llama-cli -m ~/data/models/Qwen3-30B-A3B-Q4_K_M.gguf -ngl 99 -c 4096 -cnv
```

**参数说明：**
- `-m`: 模型文件路径
- `-ngl 99`: 所有层放到 GPU
- `-c 4096`: 上下文长度
- `-cnv`: 启用对话模式 (conversation)

### 2. 单次生成

```bash
~/llama.cpp/build/bin/llama-cli -m ~/data/models/Qwen3-30B-A3B-Q4_K_M.gguf -ngl 99 -c 4096 -n 256 -p "请用一句话解释什么是人工智能。"
```

**参数说明：**
- `-n 256`: 最大生成 256 个 token
- `-p "..."`: 输入提示词

### 3. 启动 API 服务器

```bash
~/llama.cpp/build/bin/llama-server -m ~/data/models/Qwen3-30B-A3B-Q4_K_M.gguf -ngl 99 -c 4096 --host 0.0.0.0 --port 8080
```

**参数说明：**
- `--host 0.0.0.0`: 监听所有网络接口
- `--port 8080`: 服务端口

### 4. 性能基准测试

```bash
~/llama.cpp/build/bin/llama-bench -m ~/data/models/Qwen3-30B-A3B-Q4_K_M.gguf -ngl 99 -p 512 -n 128
```

**参数说明：**
- `-p 512`: 测试 512 token 的 prompt processing
- `-n 128`: 测试生成 128 token

## 完整参数列表

### 模型相关

| 参数 | 说明 | 示例 |
|------|------|------|
| `-m, --model` | 模型文件路径 | `-m model.gguf` |
| `-ngl, --n-gpu-layers` | GPU 层数 | `-ngl 99` (全部) |
| `--device` | GPU 设备 ID | `--device 0` |

### 上下文相关

| 参数 | 说明 | 示例 |
|------|------|------|
| `-c, --ctx-size` | 上下文长度 | `-c 4096` |
| `--batch-size` | 批处理大小 | `--batch-size 512` |

### 生成相关

| 参数 | 说明 | 示例 |
|------|------|------|
| `-n, --n-predict` | 最大生成 token 数 | `-n 256` |
| `-p, --prompt` | 输入提示词 | `-p "Hello"` |
| `-f, --file` | 从文件读取提示词 | `-f prompt.txt` |

### 采样参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--temp` | 温度 | 0.8 |
| `--top-k` | Top-K 采样 | 40 |
| `--top-p` | Top-P (nucleus) 采样 | 0.95 |
| `--repeat-penalty` | 重复惩罚 | 1.1 |

### 对话相关

| 参数 | 说明 |
|------|------|
| `-cnv, --conversation` | 启用对话模式 |
| `-sys, --system-prompt` | 系统提示词 |
| `-r, --reverse-prompt` | 停止生成的标记 |

### 服务器相关 (llama-server)

| 参数 | 说明 | 示例 |
|------|------|------|
| `--host` | 监听地址 | `--host 0.0.0.0` |
| `--port` | 监听端口 | `--port 8080` |
| `--api-key` | API 密钥 | `--api-key secret` |
| `--parallel` | 并行请求数 | `--parallel 4` |

## 使用示例

### 示例1：简单问答

```bash
~/llama.cpp/build/bin/llama-cli \
    -m ~/data/models/Qwen3-30B-A3B-Q4_K_M.gguf \
    -ngl 99 \
    -c 2048 \
    -n 512 \
    --temp 0.7 \
    -p "请解释量子计算的基本原理。"
```

### 示例2：带系统提示的对话

```bash
~/llama.cpp/build/bin/llama-cli \
    -m ~/data/models/Qwen3-30B-A3B-Q4_K_M.gguf \
    -ngl 99 \
    -c 4096 \
    -cnv \
    -sys "你是一个专业的编程助手，擅长 Python 和机器学习。"
```

### 示例3：启动生产服务器

```bash
~/llama.cpp/build/bin/llama-server \
    -m ~/data/models/Qwen3-30B-A3B-Q4_K_M.gguf \
    -ngl 99 \
    -c 8192 \
    --host 0.0.0.0 \
    --port 8080 \
    --parallel 4 \
    --batch-size 512
```

### 示例4：纯 CPU 运行 (备用方案)

```bash
~/llama.cpp/build/bin/llama-cli \
    -m ~/data/models/Qwen3-30B-A3B-Q4_K_M.gguf \
    -c 4096 \
    -n 256 \
    -t 32 \
    -p "你好"
```

**参数说明：**
- 不加 `-ngl` 表示 CPU 运行
- `-t 32`: 使用 32 个 CPU 线程

## API 服务器使用

### 启动服务器

```bash
~/llama.cpp/build/bin/llama-server -m ~/data/models/Qwen3-30B-A3B-Q4_K_M.gguf -ngl 99 -c 4096 --host 0.0.0.0 --port 8080
```

### 调用 API (OpenAI 兼容)

**Chat Completions:**

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "messages": [
      {"role": "user", "content": "你好，请介绍一下你自己。"}
    ],
    "max_tokens": 256,
    "temperature": 0.7
  }'
```

**Completions:**

```bash
curl http://localhost:8080/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "prompt": "人工智能是",
    "max_tokens": 100
  }'
```

### Python 调用示例

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="qwen",
    messages=[
        {"role": "user", "content": "你好，请介绍一下你自己。"}
    ],
    max_tokens=256,
    temperature=0.7
)

print(response.choices[0].message.content)
```

## 性能调优

### 1. 上下文长度

- 更短的上下文 = 更少内存占用 + 更快速度
- 建议从 2048 或 4096 开始

### 2. 量化格式

| 格式 | 大小 | 质量 | 速度 |
|------|------|------|------|
| F16 | 最大 | 最好 | 最慢 |
| Q8_0 | 中等 | 很好 | 中等 |
| Q5_K_M | 较小 | 好 | 较快 |
| Q4_K_M | 小 | 可接受 | 快 |
| Q4_0 | 最小 | 一般 | 最快 |

### 3. 批处理大小

对于服务器场景，增加批处理大小可以提高吞吐量：

```bash
llama-server -m model.gguf -ngl 99 --batch-size 1024
```

## 硬件使用情况

| 参数 | 影响 |
|------|------|
| `-ngl 99` | 使用 GPU (Vulkan) |
| `-ngl 0` 或不加 | 使用 CPU |
| `-t 32` | CPU 线程数 |

**当前配置：**
- GPU: AMD Radeon 8060S (Vulkan)
- CPU: AMD Ryzen AI MAX+ 395 (32 线程)
- NPU: 不支持 llama.cpp

## 日志和调试

### 启用详细输出

```bash
llama-cli -m model.gguf -ngl 99 --verbose
```

### 查看帮助

```bash
llama-cli --help
llama-server --help
```
