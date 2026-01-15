# Vulkan 后端详解

本文档详细说明 llama.cpp 的 Vulkan 后端在 AMD gfx1151 上的工作原理和优化建议。

## 为什么选择 Vulkan？

在 AMD Strix Halo (gfx1151) 上，有三种可能的后端：

| 后端 | 支持状态 | 性能 | 推荐程度 |
|------|---------|------|---------|
| **Vulkan** | 完全支持 | 最佳 | 强烈推荐 |
| **HIP/ROCm** | 支持但有问题 | 较差 | 不推荐 |
| **CPU** | 完全支持 | 中等 | 备选方案 |

### Vulkan vs HIP/ROCm 对比

根据社区测试，在 gfx1151 上：

| 指标 | Vulkan | HIP/ROCm |
|------|--------|----------|
| **pp512 效率** | 接近 M4 Max | 仅 40% 正常效率 |
| **tg128 效率** | 接近 M4 Pro | 大量时间在内存拷贝 |
| **Flash Attention** | 正常工作 | 不工作 |
| **稳定性** | 稳定 | 有各种问题 |

## Vulkan 设备信息

运行 `llama-cli --version` 显示的 Vulkan 设备信息：

```
ggml_vulkan: Found 1 Vulkan devices:
ggml_vulkan: 0 = AMD Radeon 8060S (RADV GFX1151) (radv)
    | uma: 1
    | fp16: 1
    | bf16: 0
    | warp size: 64
    | shared memory: 65536
    | int dot: 0
    | matrix cores: KHR_coopmat
```

### 参数详解

| 参数 | 值 | 说明 |
|------|-----|------|
| **uma** | 1 | 统一内存架构 - GPU 和 CPU 共享物理内存，无需数据拷贝 |
| **fp16** | 1 | 支持 FP16 半精度计算，适合大多数 LLM 推理 |
| **bf16** | 0 | 不支持 BF16，某些模型可能需要转换 |
| **warp size** | 64 | AMD GPU 的 wavefront 大小 (NVIDIA 是 32) |
| **shared memory** | 65536 | 64KB 共享内存，用于工作组内数据共享 |
| **int dot** | 0 | 不支持整数点积硬件加速 |
| **matrix cores** | KHR_coopmat | 支持 Vulkan 协作矩阵扩展 (重要!) |

### KHR_coopmat 的重要性

`KHR_coopmat` (Cooperative Matrix) 是 Vulkan 的矩阵运算扩展：
- 允许多个线程协作完成矩阵乘法
- 类似于 NVIDIA 的 Tensor Cores
- 对 LLM 推理性能至关重要

## Vulkan 驱动选择

AMD GPU 有两种 Vulkan 驱动：

### RADV (Mesa 开源驱动)
- **优点**: 开源，更新频繁，社区支持好
- **缺点**: pp512 比 AMDVLK 慢 16%
- **推荐场景**: 长上下文场景 (扩展性更好)

### AMDVLK (AMD 官方驱动)
- **优点**: pp512 更快
- **缺点**: tg128 比 RADV 慢 4%
- **推荐场景**: 短上下文场景

### 性能对比

| 场景 | RADV | AMDVLK | 差异 |
|------|------|--------|------|
| pp512 (短上下文) | 基准 | +16% | AMDVLK 更好 |
| tg128 | +4% | 基准 | RADV 更好 |
| 长上下文扩展 | 更好 | 较差 | RADV 更好 |

当前系统使用的是 **RADV** 驱动 (Mesa 25.0.7)。

## 编译选项

### 启用 Vulkan 后端

```bash
cmake -B build -DGGML_VULKAN=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j$(nproc)
```

### 其他可用后端

```bash
# Vulkan (推荐)
cmake -B build -DGGML_VULKAN=ON

# HIP/ROCm (不推荐在 gfx1151 上使用)
cmake -B build -DGGML_HIP=ON

# CPU only
cmake -B build

# 多后端同时编译
cmake -B build -DGGML_VULKAN=ON -DGGML_CPU=ON
```

## 运行时参数

### GPU 层数控制 (-ngl)

```bash
# 所有层在 GPU
llama-cli -m model.gguf -ngl 99

# 只有部分层在 GPU
llama-cli -m model.gguf -ngl 20

# 全部在 CPU
llama-cli -m model.gguf -ngl 0
```

### 选择 GPU 设备

如果有多个 Vulkan 设备：

```bash
# 使用第一个 GPU
llama-cli -m model.gguf -ngl 99 --device 0

# 使用第二个 GPU
llama-cli -m model.gguf -ngl 99 --device 1
```

## 内存管理

### 统一内存架构 (UMA) 的优势

gfx1151 是 APU，使用统一内存架构：

1. **无需 PCIe 传输**: CPU 和 GPU 共享物理内存
2. **更大的有效显存**: 可以使用系统内存的一部分作为 GPU 内存
3. **更低的延迟**: 数据不需要在 CPU 和 GPU 之间复制

### 内存分配

从 `amd-smi` 可以看到：
- **总可用**: 65536 MB (64GB)
- **当前占用**: ~18GB (系统和桌面)
- **可用于模型**: ~46GB

### 模型大小估算

| 量化方式 | 30B 模型大小 | 是否适合 |
|----------|-------------|---------|
| FP16 | ~60 GB | 刚好 |
| Q8_0 | ~30 GB | 舒适 |
| Q4_K_M | ~17 GB | 宽裕 |
| Q4_0 | ~15 GB | 宽裕 |

## 性能优化建议

### 1. 使用合适的量化

对于 gfx1151，推荐 Q4_K_M 或 Q5_K_M：
- 平衡了性能和质量
- 适合统一内存带宽

### 2. 调整上下文长度

```bash
# 默认 512
llama-cli -m model.gguf -ngl 99 -c 512

# 较长上下文 (会占用更多内存)
llama-cli -m model.gguf -ngl 99 -c 4096

# 最大上下文 (根据模型支持)
llama-cli -m model.gguf -ngl 99 -c 40960
```

### 3. 批处理大小

对于服务器场景：

```bash
llama-server -m model.gguf -ngl 99 -c 4096 --batch-size 512
```

## 已知问题

### 1. bf16 不支持

gfx1151 的 Vulkan 驱动不支持 bf16：
- 需要将 bf16 模型转换为 fp16 或量化格式
- 或使用已转换的 GGUF 模型

### 2. 某些操作可能回退到 CPU

如果看到警告：
```
ggml_vulkan: op XYZ not supported, falling back to CPU
```

这是正常的，某些不常用的操作可能在 CPU 上执行。

### 3. 首次运行编译着色器

首次运行时可能需要编译 Vulkan 着色器：
```
ggml_vulkan: compiling shaders...
```

这是一次性的，后续运行会使用缓存。

## 调试和诊断

### 启用详细输出

```bash
llama-cli -m model.gguf -ngl 99 --verbose
```

### 检查 Vulkan 设备

```bash
vulkaninfo --summary
```

### 监控 GPU 使用

```bash
watch -n 2 amd-smi
```

## 参考资料

- [llama.cpp Vulkan Performance Discussion](https://github.com/ggml-org/llama.cpp/discussions/10879)
- [Strix Halo llama.cpp Performance](https://strixhalo.wiki/AI/llamacpp-performance)
- [AMD Strix Halo Backend Benchmarks](https://kyuz0.github.io/amd-strix-halo-toolboxes/)
