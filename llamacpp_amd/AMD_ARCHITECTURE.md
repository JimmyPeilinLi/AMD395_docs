# AMD GPU 架构说明

本文档解释 AMD 不同 GPU 架构之间的差异，特别是 gfx1151 (消费级) 与 gfx942 (数据中心) 的区别，以及为什么某些 AI 框架不支持消费级 GPU。

## 架构家族对比

### gfx1151 (您的 GPU - Radeon 8060S)

| 属性 | 值 |
|------|-----|
| **架构** | RDNA 3.5 |
| **产品** | AMD Ryzen AI MAX+ 395 (Strix Halo APU) |
| **类型** | 集成显卡 (APU) |
| **计算单元** | 40 CUs |
| **最大频率** | 2900 MHz |
| **峰值性能** | 59.4 FP16 TFLOPS |
| **内存** | 统一内存 (与 CPU 共享，最大 64GB 可用) |
| **内存带宽** | ~500 GB/s |
| **FP8 支持** | 否 |
| **设计目标** | 游戏、消费级应用、轻量级 AI |

### gfx942 (数据中心 GPU - MI300X)

| 属性 | 值 |
|------|-----|
| **架构** | CDNA 3 |
| **产品** | AMD Instinct MI300X / MI325X |
| **类型** | 独立数据中心 GPU |
| **计算单元** | 304 CUs |
| **峰值性能** | 1307 FP16 TFLOPS |
| **内存** | 192 GB HBM3 专用显存 |
| **内存带宽** | ~5300 GB/s |
| **FP8 支持** | 是 (原生硬件支持) |
| **设计目标** | 大规模 AI 训练和推理 |

### gfx950 (下一代数据中心 GPU - MI350X)

| 属性 | 值 |
|------|-----|
| **架构** | CDNA 系列 (下一代) |
| **产品** | AMD Instinct MI350X |
| **类型** | 独立数据中心 GPU |
| **FP8 支持** | 是 |
| **设计目标** | 更高端的 AI 工作负载 |

## 核心差异对比表

| 特性 | gfx1151 (RDNA 3.5) | gfx942 (CDNA 3) | 差异倍数 |
|------|-------------------|-----------------|---------|
| **市场定位** | 消费级 APU | 数据中心 AI 加速器 | - |
| **FP8 硬件** | 无 | 原生支持 | - |
| **FP16 TFLOPS** | 59.4 | 1307 | **22x** |
| **显存** | 64GB (共享) | 192GB (专用) | 3x |
| **内存带宽** | ~500 GB/s | ~5300 GB/s | **10x** |
| **价格** | ~$1500 (整机) | ~$15000+ (单卡) | 10x |

## 架构设计目标差异

### RDNA 架构 (gfx1151)
- **主要用途**: 游戏和图形渲染
- **优化方向**: 光栅化、纹理采样、几何处理
- **AI 能力**: 有限，主要通过通用着色器实现
- **指令集**: 针对图形工作负载优化

### CDNA 架构 (gfx942)
- **主要用途**: AI/ML 计算
- **优化方向**: 矩阵运算 (GEMM)、张量操作
- **AI 能力**: 专用矩阵核心、FP8/BF8 硬件单元
- **指令集**: 针对 AI 工作负载优化

## 为什么 sglang/vLLM 不支持 gfx1151？

### 硬件层面原因

1. **缺少 FP8 硬件单元**
   - sglang/vLLM 大量使用 FP8 量化优化
   - gfx1151 没有 FP8 硬件加速，只能软件模拟

2. **内存带宽不足**
   - LLM 推理是内存密集型任务
   - gfx1151 带宽是 MI300X 的 1/10
   - 会导致严重的内存瓶颈

3. **架构优化方向不同**
   - RDNA 针对光栅化和游戏优化
   - CDNA 针对矩阵运算和 AI 优化

### 软件层面原因

1. **ROCm 支持不完善**
   - PyTorch 在 gfx1151 上存在 Flash Attention 问题
   - 参考: [PyTorch Issue #171687](https://github.com/pytorch/pytorch/issues/171687)

2. **优化内核缺失**
   - sglang/vLLM 只为 CDNA 架构编写优化内核
   - 没有针对 RDNA 的专门优化

3. **TensorFlow 不支持**
   - TensorFlow ROCm 只支持 gfx900 系列
   - 不支持 gfx1151

## LLM 推理性能实测

### gfx1151 (Strix Halo) 的问题

根据社区测试 ([llm-tracker.info](https://llm-tracker.info/AMD-Strix-Halo-(Ryzen-AI-Max+-395)-GPU-Performance)):

- **解码时 90-95% 时间花在内存拷贝上** (hipMemcpyWithStream)
- **70B 模型推理速度仅 1.4-1.6 tok/s** (HIP 后端)
- **Flash Attention 不工作**
- **实际算力利用率仅 ~1 TFLOPS** (理论 59 TFLOPS 的 2%)

### 解决方案：使用 Vulkan 后端

Vulkan 后端在 gfx1151 上表现更好：
- **pp512 性能接近 Apple M4 Max**
- **tg128 性能接近 Apple M4 Pro**
- **120B MXFP4 模型: pp512 达到 339 tok/s, tg128 达到 49 tok/s**

## AMD GPU 架构历史

| 架构 | 代号 | 系列 | 主要产品 |
|------|------|------|---------|
| GCN 1 | gfx600 | 消费级 | HD 7000 |
| GCN 5 | gfx900 | 消费级/数据中心 | Vega, MI25 |
| CDNA 1 | gfx908 | 数据中心 | MI100 |
| CDNA 2 | gfx90a | 数据中心 | MI200 |
| CDNA 3 | gfx942 | 数据中心 | MI300 |
| RDNA 1 | gfx1010 | 消费级 | RX 5000 |
| RDNA 2 | gfx1030 | 消费级 | RX 6000 |
| RDNA 3 | gfx1100 | 消费级 | RX 7000 |
| RDNA 3.5 | gfx1151 | 消费级 APU | Strix Halo |

## 实际建议

### 在 gfx1151 上运行 LLM 的最佳方案

1. **llama.cpp + Vulkan 后端** (推荐)
   - 性能最好，稳定性高
   - 支持多种量化格式

2. **llama.cpp + CPU**
   - 可作为备选方案
   - 32 线程 Zen 5 性能也不错

3. **transformers + PyTorch ROCm**
   - 需要设置 `HSA_OVERRIDE_GFX_VERSION=11.0.0`
   - 功能完整但性能不如 llama.cpp

### 不推荐的方案

- **sglang**: 硬件不支持，无法编译
- **vLLM**: 有初步支持但问题较多
- **mlc-llm**: 性能不如 llama.cpp

## 参考资料

- [ROCm GPU Specifications](https://rocm.docs.amd.com/en/latest/reference/gpu-arch-specs.html)
- [AMD Strix Halo GPU Performance](https://llm-tracker.info/AMD-Strix-Halo-(Ryzen-AI-Max+-395)-GPU-Performance)
- [PyTorch gfx1151 Issues](https://github.com/pytorch/pytorch/issues/171687)
- [vLLM gfx1151 Support](https://github.com/vllm-project/vllm/issues/16621)
- [AMD Data Center GPUs Explained](https://www.bentoml.com/blog/amd-data-center-gpus-mi250x-mi300x-mi350x-and-beyond)
