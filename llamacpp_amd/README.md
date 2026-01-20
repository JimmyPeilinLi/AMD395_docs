# llama.cpp on AMD Ryzen AI MAX+ 395 (Strix Halo)

本文档记录了在 AMD Ryzen AI MAX+ 395 (Strix Halo) 平台上安装和运行 llama.cpp 的完整过程。

## 硬件平台

| 组件 | 规格 |
|------|------|
| **CPU** | AMD Ryzen AI MAX+ 395 (Zen 5, 16核32线程) |
| **GPU** | AMD Radeon 8060S (RDNA 3.5, gfx1151, 40 CUs) |
| **NPU** | AMD XDNA 2 (不支持llama.cpp) |
| **内存** | 128GB LPDDR5X (统一内存架构) |
| **GPU VRAM** | 默认 64GB，最大可配置 96GB |
| **系统内存** | 与 GPU 共享，分配后剩余部分 |

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
| [MEMORY_ARCHITECTURE.md](MEMORY_ARCHITECTURE.md) | **统一内存架构与 VRAM 配置** |
| [VULKAN_BACKEND.md](VULKAN_BACKEND.md) | Vulkan后端详解 |
| [USAGE.md](USAGE.md) | 运行命令和参数说明 |
| [MONITORING.md](MONITORING.md) | amd-smi监控工具说明 |
| [MODEL_CONVERSION.md](MODEL_CONVERSION.md) | 模型转换指南 |
| [FAQ.md](FAQ.md) | 常见问题和解决方案 |
| [benchmark/](benchmark/) | 性能测试脚本和结果 |

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
4. **统一内存架构** - GPU/CPU/NPU 共享 128GB 内存，可配置分配比例
5. **VRAM 可扩展至 96GB** - 通过 GRUB 参数可将 GPU VRAM 从默认 64GB 增加到 96GB

## 性能测试结果 (Q4_K_M)

| 指标 | GPU (Vulkan) | CPU (32线程) | GPU/CPU |
|------|--------------|--------------|---------|
| Prefill 平均 | 770 t/s | 364 t/s | 2.1x |
| Decode 平均 | 86 t/s | 10 t/s | 8.4x |

详见 [benchmark/analysis.md](benchmark/analysis.md)

## 创建/更新日期

- 创建: 2026-01-13
- 更新: 2026-01-15 (添加内存架构文档)
