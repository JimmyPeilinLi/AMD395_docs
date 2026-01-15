# llama.cpp on AMD Ryzen AI MAX+ 395 (Strix Halo)

本文档记录了在 AMD Ryzen AI MAX+ 395 (Strix Halo) 平台上安装和运行 llama.cpp 的完整过程。

## 硬件平台

| 组件 | 规格 |
|------|------|
| **CPU** | AMD Ryzen AI MAX+ 395 (Zen 5, 16核32线程) |
| **GPU** | AMD Radeon 8060S (RDNA 3.5, gfx1151, 40 CUs) |
| **NPU** | AMD XDNA 2 (不支持llama.cpp) |
| **内存** | 128GB LPDDR5X (统一内存架构) |
| **GPU可用内存** | ~64GB (与CPU共享) |

## 软件环境

| 组件 | 版本 |
|------|------|
| **操作系统** | Ubuntu 24.04 LTS |
| **内核** | 6.11.0-17-generic |
| **ROCm** | 7.9.0 |
| **amdgpu驱动** | 6.11.0-17 |
| **llama.cpp** | build 7709 (Vulkan后端) |

## 文档目录

| 文档 | 说明 |
|------|------|
| [INSTALLATION.md](INSTALLATION.md) | 完整安装指南 |
| [AMD_ARCHITECTURE.md](AMD_ARCHITECTURE.md) | AMD GPU架构说明 (gfx1151 vs gfx942) |
| [VULKAN_BACKEND.md](VULKAN_BACKEND.md) | Vulkan后端详解 |
| [USAGE.md](USAGE.md) | 运行命令和参数说明 |
| [MONITORING.md](MONITORING.md) | amd-smi监控工具说明 |
| [MODEL_CONVERSION.md](MODEL_CONVERSION.md) | 模型转换指南 |
| [FAQ.md](FAQ.md) | 常见问题和解决方案 |

## 快速开始

```bash
# 运行交互式对话
~/llama.cpp/build/bin/llama-cli -m ~/data/models/Qwen3-30B-A3B-Q4_K_M.gguf -ngl 99 -c 4096 -cnv

# 单次生成
~/llama.cpp/build/bin/llama-cli -m ~/data/models/Qwen3-30B-A3B-Q4_K_M.gguf -ngl 99 -c 4096 -n 256 -p "你好"

# 启动API服务器
~/llama.cpp/build/bin/llama-server -m ~/data/models/Qwen3-30B-A3B-Q4_K_M.gguf -ngl 99 -c 4096 --host 0.0.0.0 --port 8080
```

## 关键发现

1. **Vulkan后端是最佳选择** - 在gfx1151上，Vulkan后端比HIP/ROCm后端性能更好
2. **sglang/vLLM不支持gfx1151** - 这些框架只支持数据中心GPU (gfx942/gfx950)
3. **NPU不可用** - llama.cpp不支持AMD XDNA NPU
4. **统一内存优势** - 64GB GPU可用内存可以运行大模型

## 创建日期

2026-01-13
