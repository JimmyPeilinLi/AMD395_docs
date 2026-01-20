# AMD Ryzen AI MAX+ 395 平台 llama.cpp 部署技术方案

**版本**: 内部版 v1.2
**日期**: 2026-01-15
**平台**: AMD Ryzen AI MAX+ 395 (Strix Halo)

---

## 目录

1. [执行摘要](#1-执行摘要)
2. [硬件平台架构分析](#2-硬件平台架构分析)
3. [驱动安装指南](#3-驱动安装指南)
4. [llama.cpp 部署](#4-llamacpp-部署)
5. [性能分析与优化](#5-性能分析与优化)
6. [常见问题与解决方案](#6-常见问题与解决方案)
7. [附录](#7-附录)

---

## 1. 执行摘要

### 1.1 项目背景

本文档详细记录在 AMD Ryzen AI MAX+ 395 (Strix Halo) 平台上部署 llama.cpp 进行大语言模型推理的完整技术方案。该平台具有独特的 **GPU-CPU-NPU 三合一异构计算架构**，是 AMD 面向 AI 工作站市场的旗舰级 APU 产品。

### 1.2 核心结论

| 项目 | 结论 |
|------|------|
| **推荐推理后端** | Vulkan (性能最佳) |
| **GPU 可用内存** | ~64GB (统一内存架构) |
| **适合模型规模** | 7B-70B (量化后) |
| **不推荐方案** | sglang/vLLM (不支持 gfx1151) |
| **NPU 状态** | llama.cpp 不支持，暂不可用 |

### 1.3 价值主张

> 通过 **Vulkan 后端 + 统一内存架构**，实现 **64GB 大容量模型加载能力**，使开发者能够在单一 APU 平台上运行 70B 级别的量化模型，无需昂贵的独立显卡。

---

## 2. 硬件平台架构分析

### 2.1 Strix Halo 架构概述

AMD Ryzen AI MAX+ 395 是基于 Strix Halo 架构的旗舰级 APU，采用 **CPU + GPU + NPU** 三合一异构设计：

```
┌─────────────────────────────────────────────────────────────────┐
│                    AMD Ryzen AI MAX+ 395                         │
│                      (Strix Halo SoC)                            │
├─────────────────┬─────────────────┬─────────────────────────────┤
│     Zen 5 CPU   │   RDNA 3.5 GPU  │         XDNA 2 NPU          │
│   (16C/32T)     │   (40 CUs)      │        (50+ TOPS)           │
├─────────────────┴─────────────────┴─────────────────────────────┤
│                   统一内存控制器 (Infinity Fabric)                │
├─────────────────────────────────────────────────────────────────┤
│                  128GB LPDDR5X 统一内存                          │
│                   (CPU/GPU/NPU 共享)                             │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 三大计算单元详解

#### 2.2.1 CPU - AMD Zen 5 架构

| 规格 | 参数 |
|------|------|
| **架构** | Zen 5 (Family 26, Model 112) |
| **核心数** | 16 核心 / 32 线程 |
| **基础频率** | 3.0 GHz |
| **最大加速频率** | 5.1 GHz |
| **L1 缓存** | 768 KB (数据) + 512 KB (指令) |
| **L2 缓存** | 16 MB (每核心 1MB) |
| **L3 缓存** | 64 MB (2 x 32MB CCX) |
| **指令集** | AVX-512, AVX2, FMA, SSE4.2 |
| **虚拟化** | AMD-V 支持 |

**AI 相关特性**：
- AVX-512 VNNI 支持，加速 INT8/BF16 向量运算
- 大容量 L3 缓存，有效降低内存访问延迟
- 可作为 llama.cpp 的备选计算后端 (32 线程)

#### 2.2.2 GPU - AMD RDNA 3.5 架构

| 规格 | 参数 |
|------|------|
| **架构** | RDNA 3.5 (gfx1151) |
| **产品名称** | AMD Radeon 8060S |
| **计算单元** | 40 CUs |
| **流处理器** | 2560 SPs (40 × 64) |
| **最大频率** | 2900 MHz |
| **理论 FP16 性能** | ~59.4 TFLOPS |
| **理论 FP32 性能** | ~14.8 TFLOPS |
| **共享内存** | 64 KB / 工作组 |
| **Warp 大小** | 64 (AMD Wavefront) |
| **PCI 地址** | c6:00.0 |
| **设备 ID** | 1002:1586 |

**Vulkan 特性** (来自 vulkaninfo):
- 统一内存架构 (UMA): 支持
- FP16 计算: 支持
- BF16 计算: 不支持
- 协作矩阵扩展 (KHR_coopmat): 支持
- 最大显存: ~64GB (与系统共享)

**与数据中心 GPU 对比**:

| 特性 | gfx1151 (本机) | gfx942 (MI300X) | 差异 |
|------|---------------|-----------------|------|
| **架构** | RDNA 3.5 | CDNA 3 | 游戏 vs AI |
| **FP16 性能** | 59.4 TFLOPS | 1307 TFLOPS | 22x |
| **显存** | 64GB (共享) | 192GB HBM3 | 3x |
| **带宽** | ~273 GB/s | ~5300 GB/s | 19x |
| **FP8 支持** | 否 | 是 | - |
| **定位** | 消费级 APU | 数据中心 AI | - |

**重要结论**: gfx1151 是 RDNA 架构 (游戏优化)，而非 CDNA 架构 (AI 优化)，这导致：
- sglang/vLLM 等框架不支持 (只支持 gfx942/gfx950)
- PyTorch ROCm 需要特殊配置 (HSA_OVERRIDE_GFX_VERSION)
- 推荐使用 Vulkan 后端而非 HIP/ROCm 后端

#### 2.2.3 NPU - AMD XDNA 2 架构

| 规格 | 参数 |
|------|------|
| **架构** | XDNA 2 |
| **AI 性能** | 50+ INT8 TOPS |
| **PCI 地址** | c7:00.1 |
| **设备 ID** | 1022:17f0 |
| **驱动** | amdxdna (需要 kernel 6.11+) |
| **当前状态** | llama.cpp 不支持 |

**NPU 现状说明**:
- NPU 硬件已检测到，但 llama.cpp 不支持 AMD XDNA NPU
- NPU 主要用于 Windows 上的 Copilot+ 功能
- Linux 下可用于其他 AI 加速场景 (如 ONNX Runtime)
- 对于 LLM 推理，建议使用 GPU (Vulkan) 后端

### 2.3 统一内存架构 (UMA) 的优势

Strix Halo 采用统一内存架构，CPU、GPU、NPU 共享 128GB LPDDR5X 物理内存：

```
                    物理内存分布
┌──────────────────────────────────────────────┐
│              128GB LPDDR5X                   │
├──────────────────────────────────────────────┤
│  系统保留   │  CPU 使用  │   GPU/NPU 可用    │
│  (~8GB)     │  (~20GB)   │    (~64GB)        │
└──────────────────────────────────────────────┘
              ▲
              │ 无 PCIe 拷贝开销
              │ 直接访问
              ▼
        ┌──────────────┐
        │  GPU 计算    │
        │  (Vulkan)    │
        └──────────────┘
```

**UMA 对 LLM 推理的影响**:

| 特性 | 传统独显 | Strix Halo UMA |
|------|----------|----------------|
| **显存容量** | 固定 (如 24GB) | 动态 (~64GB) |
| **数据传输** | PCIe 拷贝 | 无需拷贝 |
| **大模型支持** | 受显存限制 | 可加载更大模型 |
| **内存带宽** | 分离 | 共享 (~273 GB/s) |
| **功耗** | 较高 | 较低 |

### 2.4 当前系统配置

```bash
# 操作系统
OS: Ubuntu 24.04 LTS (Noble Numbat)
Kernel: 6.11.0-17-generic

# ROCm 版本
ROCm: 7.9.0 (Technology Preview)
amdgpu driver: 6.11.0-17

# GPU 状态
$ rocm-smi --showproductname
GPU[0]: Card Series: AMD Radeon Graphics
GPU[0]: GFX Version: gfx1151

# 内存状态
$ amd-smi
Mem-Usage: 18360/65536 MB
```

---

## 3. 驱动安装指南

### 3.1 安装前提条件

| 要求 | 最低版本 | 推荐版本 |
|------|----------|----------|
| **Ubuntu** | 22.04 LTS | 24.04 LTS |
| **Kernel** | 6.8.0 | 6.11.0+ |
| **ROCm** | 7.0 | 7.9.0 |

### 3.2 系统升级 (如需)

如果当前系统版本较旧，需要先升级：

```bash
# 从 Ubuntu 22.04 升级到 24.04
sudo apt update && sudo apt upgrade -y
sudo do-release-upgrade
```

### 3.3 安装 ROCm 7.9

ROCm 7.9 是首个官方支持 gfx1151 的版本，需要使用专用 tarball：

```bash
# 1. 下载 gfx1151 专用 tarball
cd /home/quings/lpl/install_driver/
wget https://repo.amd.com/rocm/tarball/therock-dist-linux-gfx1151-7.9.0rc1.tar.gz

# 2. 创建安装目录并解压
sudo mkdir -p /opt/rocm
sudo tar -xf therock-dist-linux-gfx1151-7.9.0rc1.tar.gz -C /opt/rocm --strip-components=1

# 3. 验证安装
ls /opt/rocm/bin/
# 应该看到: rocminfo, rocm-smi, hipcc 等
```

### 3.4 配置环境变量

在 `~/.bashrc` 中添加：

```bash
# ROCm 7.9 环境变量
export ROCM_HOME=/opt/rocm
export PATH=$ROCM_HOME/bin:$PATH
export LD_LIBRARY_PATH=$ROCM_HOME/lib:$ROCM_HOME/lib64:$LD_LIBRARY_PATH

# 关键: PyTorch 兼容性设置 (使用 11.0.0 而非 11.5.1)
export HSA_OVERRIDE_GFX_VERSION=11.0.0
```

应用配置：

```bash
source ~/.bashrc
```

### 3.5 配置 GRUB 参数

编辑 `/etc/default/grub`：

```bash
sudo nano /etc/default/grub

# 修改这一行:
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash amdgpu.dpm=1 amdgpu.ppfeaturemask=0xffffffff"
```

参数说明：
- `amdgpu.dpm=1`: 启用动态电源管理
- `amdgpu.ppfeaturemask=0xffffffff`: 启用所有 PowerPlay 功能

更新 GRUB 并重启：

```bash
sudo update-grub
sudo reboot
```

### 3.6 验证 GPU 驱动

```bash
# 检查 amdgpu 驱动绑定
lspci -k | grep -A 3 "Display"
# 预期输出应包含: Kernel driver in use: amdgpu

# 检查 DRM 设备
ls -la /dev/dri/
# 预期输出: card0, renderD128

# 检查 ROCm 检测
rocminfo | grep -E "Agent|Name|gfx"
# 预期输出: Agent 2 with gfx1151
```

### 3.7 验证 PyTorch ROCm

```bash
# 安装 PyTorch ROCm 版本
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.3

# 测试 GPU 检测
python3 -c "
import torch
print(f'GPU Available: {torch.cuda.is_available()}')
print(f'GPU Name: {torch.cuda.get_device_name(0)}')
print(f'GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB')
"
# 预期输出:
# GPU Available: True
# GPU Name: AMD Radeon 8060S
# GPU Memory: 33.52 GB
```

### 3.8 已知问题与解决方案

#### 问题 1: GPU 使用 simple-framebuffer

**症状**: `lspci -k` 显示 Kernel driver in use 为空或 simple-framebuffer

**解决方案**:
```bash
# 手动加载 amdgpu
sudo modprobe amdgpu

# 或添加到自动加载
echo "amdgpu" | sudo tee -a /etc/modules

# 重启后验证
sudo reboot
```

#### 问题 2: HSA_OVERRIDE_GFX_VERSION 设置

**症状**: PyTorch 报错 "HIP error: invalid device function"

**解决方案**:
```bash
# 使用 11.0.0 而非 11.5.1
export HSA_OVERRIDE_GFX_VERSION=11.0.0
```

#### 问题 3: amd-smi 无输出

**症状**: 运行 `amd-smi` 没有任何输出

**解决方案**:
```bash
# 确保使用 ROCm 版本的 amd-smi
which amd-smi
# 应为: /opt/rocm/bin/amd-smi

# 如果路径不对，手动指定
/opt/rocm/bin/amd-smi
```

---

## 4. llama.cpp 部署

### 4.1 为什么选择 Vulkan 后端

在 gfx1151 平台上，Vulkan 后端是最佳选择：

| 后端 | 支持状态 | 性能 | 推荐度 |
|------|----------|------|--------|
| **Vulkan** | 完全支持 | 最佳 | **强烈推荐** |
| **HIP/ROCm** | 支持但问题多 | 较差 | 不推荐 |
| **CPU** | 完全支持 | 中等 | 备选方案 |

**Vulkan vs HIP/ROCm 性能对比** (来自社区测试):

| 指标 | Vulkan | HIP/ROCm |
|------|--------|----------|
| pp512 效率 | 接近 M4 Max | 仅 40% 正常效率 |
| tg128 效率 | 接近 M4 Pro | 大量时间在内存拷贝 |
| Flash Attention | 正常工作 | 不工作 |
| 稳定性 | 稳定 | 有各种问题 |

### 4.2 安装 Vulkan 依赖

```bash
# 更新包列表
sudo apt update

# 安装 Vulkan 核心组件
sudo apt install -y cmake build-essential libvulkan-dev vulkan-tools mesa-vulkan-drivers

# 安装 GLSL 编译器 (llama.cpp 需要)
sudo apt install -y glslc libshaderc-dev glslang-tools

# 安装 libcurl (可选，用于模型下载功能)
sudo apt install -y libcurl4-openssl-dev
```

### 4.3 验证 Vulkan 安装

```bash
vulkaninfo --summary
```

预期输出：
```
GPU0:
    deviceName         = AMD Radeon 8060S (RADV GFX1151)
    driverName         = radv
    deviceType         = PHYSICAL_DEVICE_TYPE_INTEGRATED_GPU
```

### 4.4 编译 llama.cpp

```bash
# 克隆仓库
cd ~
git clone https://github.com/ggml-org/llama.cpp.git
cd llama.cpp

# 配置 cmake (启用 Vulkan)
cmake -B build -DGGML_VULKAN=ON -DCMAKE_BUILD_TYPE=Release

# 编译 (使用所有 CPU 核心)
cmake --build build --config Release -j$(nproc)
```

编译成功后，可执行文件位于 `~/llama.cpp/build/bin/` 目录。

### 4.5 验证 GPU 检测

```bash
~/llama.cpp/build/bin/llama-cli --version
```

预期输出：
```
ggml_vulkan: Found 1 Vulkan devices:
ggml_vulkan: 0 = AMD Radeon 8060S (RADV GFX1151) (radv) | uma: 1 | fp16: 1 | bf16: 0 | warp size: 64 | shared memory: 65536 | int dot: 0 | matrix cores: KHR_coopmat
version: 7709 (1051ecd28)
built with GNU 13.3.0 for Linux x86_64
```

**Vulkan 参数详解**:

| 参数 | 值 | 说明 |
|------|-----|------|
| uma | 1 | 统一内存架构，无需数据拷贝 |
| fp16 | 1 | 支持 FP16 半精度计算 |
| bf16 | 0 | 不支持 BF16 |
| warp size | 64 | AMD Wavefront 大小 |
| shared memory | 65536 | 64KB 共享内存 |
| matrix cores | KHR_coopmat | 支持协作矩阵扩展 (重要!) |

### 4.6 运行命令详解

#### 4.6.1 交互式对话

```bash
~/llama.cpp/build/bin/llama-cli \
    -m ~/data/models/Qwen3-30B-A3B-Q4_K_M.gguf \
    -ngl 99 \
    -c 4096 \
    -cnv
```

**参数说明**:
- `-m`: 模型文件路径 (GGUF 格式)
- `-ngl 99`: 所有层放到 GPU (99 表示尽可能多)
- `-c 4096`: 上下文长度
- `-cnv`: 启用对话模式 (conversation)

#### 4.6.2 单次生成

```bash
~/llama.cpp/build/bin/llama-cli \
    -m ~/data/models/Qwen3-30B-A3B-Q4_K_M.gguf \
    -ngl 99 \
    -c 4096 \
    -n 256 \
    -p "请用一句话解释什么是人工智能。"
```

#### 4.6.3 启动 API 服务器

```bash
~/llama.cpp/build/bin/llama-server \
    -m ~/data/models/Qwen3-30B-A3B-Q4_K_M.gguf \
    -ngl 99 \
    -c 4096 \
    --host 0.0.0.0 \
    --port 8080
```

#### 4.6.4 性能基准测试

```bash
~/llama.cpp/build/bin/llama-bench \
    -m ~/data/models/Qwen3-30B-A3B-Q4_K_M.gguf \
    -ngl 99 \
    -p 512 \
    -n 128
```

### 4.7 API 服务器使用

启动服务器后，可以使用 OpenAI 兼容的 API 调用：

**Chat Completions**:
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

**Python 调用**:
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

### 4.8 主要可执行文件

| 文件 | 用途 |
|------|------|
| `llama-cli` | 命令行推理工具 |
| `llama-server` | OpenAI 兼容 API 服务器 |
| `llama-quantize` | 模型量化工具 |
| `llama-bench` | 性能基准测试 |
| `llama-perplexity` | 困惑度评估 |

---

## 5. 性能分析与优化

### 5.1 测试环境

| 项目 | 配置 |
|------|------|
| **硬件** | AMD Ryzen AI MAX+ 395 |
| **GPU** | Radeon 8060S (gfx1151, Vulkan 后端) |
| **CPU** | 16 核 32 线程 (Zen 5) |
| **内存** | 128GB LPDDR5X |
| **测试模型** | Qwen3-30B-A3B-Q4_K_M.gguf (17.28 GB) |
| **llama.cpp 版本** | build #7709 (1051ecd28) |
| **测试日期** | 2026-01-13 |

### 5.2 GPU vs CPU 性能对比 (实测数据)

**测试命令**:

```bash
# GPU 测试 (Vulkan 后端, 所有层放到 GPU)
~/llama.cpp/build/bin/llama-bench \
    -m ~/data/models/Qwen3-30B-A3B-Q4_K_M.gguf \
    -ngl 99 \
    -p 128,512,1024,2048,4096 \
    -n 128,256,512 \
    -r 2

# CPU 测试 (32 线程)
~/llama.cpp/build/bin/llama-bench \
    -m ~/data/models/Qwen3-30B-A3B-Q4_K_M.gguf \
    -ngl 0 \
    -t 32 \
    -p 128,512,1024,2048,4096 \
    -n 128,256,512 \
    -r 2
```

#### 5.2.1 Prefill 性能 (Prompt Processing)

| Prompt 长度 | GPU Vulkan (t/s) | CPU 32线程 (t/s) | GPU/CPU 加速比 |
|-------------|------------------|------------------|----------------|
| 128 tokens | **502** | 165 | 3.0x |
| 512 tokens | **988** | 462 | 2.1x |
| 1024 tokens | **856** | 433 | 2.0x |
| 2048 tokens | **798** | 402 | 2.0x |
| 4096 tokens | **705** | 356 | 2.0x |

**Prefill 性能特点**:
- GPU 峰值性能出现在 **512 tokens**: ~988 t/s
- 长上下文性能衰减: pp4096 比 pp512 慢约 **30%**
- GPU 平均加速比: **2.1x**

#### 5.2.2 Decode 性能 (Token Generation)

| 生成长度 | GPU Vulkan (t/s) | CPU 32线程 (t/s) | GPU/CPU 加速比 |
|----------|------------------|------------------|----------------|
| 128 tokens | **88** | 10.3 | 8.5x |
| 256 tokens | **86** | 10.3 | 8.4x |
| 512 tokens | **84** | 10.2 | 8.2x |

**Decode 性能特点**:
- GPU 性能非常稳定: 83-90 t/s，标准差很小
- CPU 性能稳定但较慢: ~10 t/s
- GPU 平均加速比: **8.4x** (最显著差异)

#### 5.2.3 性能汇总

| 指标 | GPU (Vulkan) | CPU (32线程) | GPU 加速比 |
|------|--------------|--------------|------------|
| **Prefill 平均** | 770 t/s | 364 t/s | **2.1x** |
| **Decode 平均** | 86 t/s | 10 t/s | **8.4x** |
| **Prefill 峰值** | 988 t/s (pp512) | 462 t/s (pp512) | 2.1x |
| **Decode 稳定性** | 低波动 (±3%) | 低波动 (±2%) | - |

#### 5.2.4 性能曲线分析

```
Prefill 性能 (tokens/s)
1000 ┤                    ●
 900 ┤                   ╱ ╲
 800 ┤         ●────────●   ●────●
 700 ┤        ╱                   ╲────● GPU
 600 ┤       ╱
 500 ┤      ●
 400 ┤    ●────●────●────●────● CPU
 300 ┤   ╱
 200 ┤  ●
 100 ┤
   0 ┼──────────────────────────────
      128  512  1024 2048 4096 (tokens)

Decode 性能 (tokens/s)
 100 ┤
  80 ┤  ●────●────● GPU (稳定 ~86 t/s)
  60 ┤
  40 ┤
  20 ┤
  10 ┤  ●────●────● CPU (稳定 ~10 t/s)
   0 ┼──────────────────
      128  256  512 (tokens)
```

#### 5.2.5 完整测试配置

测试共 8 组配置，覆盖不同的 Prompt/Generate 长度组合：

| 测试ID | Prompt (pp) | Generate (tg) | 典型应用场景 |
|--------|-------------|---------------|--------------|
| T1 | 128 | 128 | 简单问答 |
| T2 | 128 | 256 | 短提示 + 中等生成 |
| T3 | 512 | 256 | 中等提示 + 中等生成 |
| T4 | 1024 | 128 | 长提示 + 短生成 (文档摘要) |
| T5 | 2048 | 256 | 长上下文场景 |
| T6 | 4096 | 256 | 超长上下文场景 |
| T7 | 512 | 512 | 中等提示 + 长生成 |
| T8 | 1024 | 512 | 长提示 + 长生成 (深度分析) |

**llama-bench 测试参数**:

| 参数 | GPU 测试 | CPU 测试 | 说明 |
|------|----------|----------|------|
| `-ngl` | 99 | 0 | GPU 层数 (99=全部) |
| `-t` | 16 | 32 | CPU 线程数 |
| `-r` | 2 | 2 | 重复次数 |
| `n_batch` | 2048 | 2048 | 批处理大小 |
| `n_ubatch` | 512 | 512 | 微批处理大小 |
| `type_k/v` | f16 | f16 | KV 缓存精度 |

#### 5.2.6 完整测试结果

**GPU (Vulkan) 详细结果**:

| 测试 | n_prompt | n_gen | avg_ts (t/s) | stddev_ts | 说明 |
|------|----------|-------|--------------|-----------|------|
| T1 | 128 | 0 | 509.13 | 29.27 | Prefill |
| T1 | 0 | 128 | 90.12 | 0.23 | Decode |
| T2 | 128 | 0 | 494.89 | 19.67 | Prefill |
| T2 | 0 | 256 | 87.17 | 2.17 | Decode |
| T3 | 512 | 0 | **998.24** | 2.86 | Prefill (峰值) |
| T3 | 0 | 256 | 85.84 | 0.16 | Decode |
| T4 | 1024 | 0 | 858.86 | 23.51 | Prefill |
| T4 | 0 | 128 | 85.47 | 0.07 | Decode |
| T5 | 2048 | 0 | 797.77 | 1.94 | Prefill |
| T5 | 0 | 256 | 85.40 | 0.27 | Decode |
| T6 | 4096 | 0 | 704.74 | 0.82 | Prefill |
| T6 | 0 | 256 | 85.43 | 0.26 | Decode |
| T7 | 512 | 0 | 977.49 | 2.82 | Prefill |
| T7 | 0 | 512 | 83.91 | 0.02 | Decode |
| T8 | 1024 | 0 | 853.51 | 25.74 | Prefill |
| T8 | 0 | 512 | 83.89 | 0.06 | Decode |

**CPU (32 线程) 详细结果**:

| 测试 | n_prompt | n_gen | avg_ts (t/s) | stddev_ts | 说明 |
|------|----------|-------|--------------|-----------|------|
| T1 | 128 | 0 | 149.98 | 2.11 | Prefill |
| T1 | 0 | 128 | 10.12 | 0.37 | Decode |
| T2 | 128 | 0 | 180.56 | 8.39 | Prefill |
| T2 | 0 | 256 | 10.45 | 0.37 | Decode |
| T3 | 512 | 0 | **446.53** | 45.79 | Prefill (峰值) |
| T3 | 0 | 256 | 10.43 | 0.16 | Decode |
| T4 | 1024 | 0 | 416.66 | 21.56 | Prefill |
| T4 | 0 | 128 | 10.50 | 0.09 | Decode |
| T5 | 2048 | 0 | 402.14 | 27.40 | Prefill |
| T5 | 0 | 256 | 10.26 | 0.10 | Decode |
| T6 | 4096 | 0 | 355.66 | 6.93 | Prefill |
| T6 | 0 | 256 | 9.95 | 0.10 | Decode |
| T7 | 512 | 0 | 478.41 | 11.98 | Prefill |
| T7 | 0 | 512 | 10.13 | 0.06 | Decode |
| T8 | 1024 | 0 | 449.88 | 13.50 | Prefill |
| T8 | 0 | 512 | 10.28 | 0.03 | Decode |

### 5.3 场景选择建议

| 使用场景 | 推荐后端 | 原因 |
|----------|----------|------|
| **交互对话** | GPU | Decode 8.4x 更快，响应更流畅 |
| **长文档处理** | GPU | Prefill 2.1x 更快 |
| **批量推理** | GPU | 吞吐量显著更高 |
| **GPU 内存不足** | CPU | 可行备选方案 |
| **超大模型 (>64GB)** | CPU | GPU 内存受限时使用 |

### 5.4 模型大小与内存估算

| 量化方式 | 7B 模型 | 30B 模型 | 70B 模型 |
|----------|---------|----------|----------|
| FP16 | ~14 GB | ~60 GB | ~140 GB |
| Q8_0 | ~7 GB | ~30 GB | ~70 GB |
| Q5_K_M | ~4.8 GB | ~20 GB | ~48 GB |
| Q4_K_M | ~4 GB | ~17 GB | ~40 GB |
| Q4_0 | ~3.5 GB | ~15 GB | ~35 GB |

**推荐配置** (基于 64GB 可用显存):

| 模型规模 | 推荐量化 | 预期内存占用 | 预期 Decode 速度 |
|----------|----------|--------------|------------------|
| 7B | Q8_0 或 FP16 | 7-14 GB | ~150+ t/s |
| 30B | Q4_K_M 或 Q5_K_M | 17-20 GB | ~86 t/s (实测) |
| 70B | Q4_0 或 Q4_K_M | 35-40 GB | ~40-50 t/s |

### 5.5 与其他平台对比

基于本次实测数据与社区数据对比：

| 平台 | pp512 (t/s) | tg128 (t/s) | 备注 |
|------|-------------|-------------|------|
| **Strix Halo (本机, Vulkan)** | **988** | **88** | 实测数据 |
| Strix Halo (HIP/ROCm) | ~400 | ~35 | 效率仅 40% |
| Apple M4 Max (Metal) | ~900 | ~80 | 接近本机 |
| Apple M4 Pro (Metal) | ~600 | ~50 | 略慢 |
| RTX 4090 (CUDA) | ~2000+ | ~150+ | 独显优势 |

**结论**: Strix Halo + Vulkan 后端的性能接近 Apple M4 Max，在消费级 APU 中表现优异。

### 5.6 Q4_K_M vs F16 量化对比 (2026-01-15 新增)

除了量化模型 Q4_K_M，我们还测试了 F16 全精度模型以对比性能差异。

**测试模型**:
| 模型 | 量化格式 | 大小 | 精度 |
|------|----------|------|------|
| Qwen3-30B-A3B | Q4_K_M | 17.28 GB | 4-bit 量化 |
| Qwen3-30B-A3B | F16 | 56.89 GB | 16-bit 浮点 |

**注意**: 原始 BF16 模型 Vulkan 不支持 (`bf16: 0`)，需转换为 F16 格式。

**测试命令**:

```bash
# Q4_K_M 测试
~/llama.cpp/build/bin/llama-bench \
    -m ~/data/models/Qwen3-30B-A3B-Q4_K_M.gguf \
    -ngl 99 \
    -p 128,512,1024,2048 \
    -n 128,256 \
    -r 2 \
    -o csv

# F16 测试
~/llama.cpp/build/bin/llama-bench \
    -m ~/data/models/Qwen3-30B-A3B-F16.gguf \
    -ngl 99 \
    -p 128,512,1024,2048 \
    -n 128,256 \
    -r 2 \
    -o csv
```

#### 5.6.1 Prefill 速度对比 (tokens/s)

| Prompt 长度 | Q4_K_M | F16 | Q4_K_M/F16 加速比 |
|-------------|--------|-----|-------------------|
| 128 tokens | **498** | 269 | 1.85x |
| 512 tokens | **1004** | 640 | 1.57x |
| 1024 tokens | **906** | 613 | 1.48x |
| 2048 tokens | **811** | 589 | 1.38x |

#### 5.6.2 Decode 速度对比 (tokens/s)

| 生成长度 | Q4_K_M | F16 | Q4_K_M/F16 加速比 |
|----------|--------|-----|-------------------|
| 128 tokens | **86.0** | 21.9 | **3.93x** |
| 256 tokens | **85.8** | 21.9 | **3.92x** |

#### 5.6.3 性能分析

```
Decode 速度对比 (tokens/s)

Q4_K_M ████████████████████████████████████████████ 86 t/s
F16    ███████████ 22 t/s

                    ~4x 差距
```

**关键发现**:

1. **Q4_K_M 在所有场景下都更快**
   - Prefill: 1.4x - 1.9x 更快
   - Decode: **~4x 更快** (最显著差异)

2. **内存效率**
   - Q4_K_M: 17GB (可在 64GB VRAM 中轻松运行)
   - F16: 57GB (接近 64GB VRAM 上限)

3. **精度 vs 速度权衡**
   - F16 保留完整精度，适合对准确性要求高的场景
   - Q4_K_M 速度优势明显，**推荐日常使用**

#### 5.6.4 适用场景推荐

| 场景 | 推荐模型 | 原因 |
|------|----------|------|
| **日常对话** | Q4_K_M | 速度快，响应及时 |
| **批量处理** | Q4_K_M | 吞吐量高 |
| **代码生成** | Q4_K_M | 通常足够准确 |
| **学术研究** | F16 | 需要最高精度 |
| **模型评估** | F16 | 避免量化误差 |

#### 5.6.5 BF16 转 F16 方法

```bash
# BF16 -> F16 转换
~/llama.cpp/build/bin/llama-quantize \
    model-bf16.gguf \
    model-f16.gguf \
    F16

# BF16 -> Q4_K_M 量化 (更小更快)
~/llama.cpp/build/bin/llama-quantize \
    model-bf16.gguf \
    model-q4km.gguf \
    Q4_K_M
```

### 5.7 Vulkan 驱动选择

AMD GPU 有两种 Vulkan 驱动可选：

| 驱动 | 优点 | 缺点 | 推荐场景 |
|------|------|------|----------|
| **RADV (Mesa)** | 开源，更新频繁，长上下文扩展性好 | pp512 比 AMDVLK 慢 16% | 长上下文场景 |
| **AMDVLK** | pp512 更快 | tg128 比 RADV 慢 4% | 短上下文场景 |

当前系统使用 **RADV** 驱动 (Mesa 25.0.7)。

### 5.8 优化建议

#### 5.8.1 量化格式选择

对于 gfx1151，推荐 **Q4_K_M** 或 **Q5_K_M**：
- 平衡性能和质量
- 适合统一内存带宽

#### 5.8.2 上下文长度调整

```bash
# 默认 512 (适合简单问答)
llama-cli -m model.gguf -ngl 99 -c 512

# 中等上下文 (适合对话)
llama-cli -m model.gguf -ngl 99 -c 4096

# 长上下文 (会占用更多内存)
llama-cli -m model.gguf -ngl 99 -c 8192
```

#### 5.8.3 批处理大小 (服务器场景)

```bash
llama-server -m model.gguf -ngl 99 -c 4096 --batch-size 512 --parallel 4
```

#### 5.8.4 GPU 监控

```bash
# 实时监控 GPU 状态
watch -n 2 amd-smi

# 监控内存使用
watch -n 2 'amd-smi | grep "Mem-Usage"'
```

### 5.9 与其他方案对比

| 方案 | 支持状态 | 性能 | 推荐度 |
|------|----------|------|--------|
| **llama.cpp + Vulkan** | 完全支持 | 最佳 | **强烈推荐** |
| **llama.cpp + CPU** | 完全支持 | 中等 | 备选方案 |
| **sglang** | 不支持 gfx1151 | - | 不可用 |
| **vLLM** | 有初步支持但问题多 | 较差 | 不推荐 |
| **mlc-llm** | 支持 | 不如 llama.cpp | 不推荐 |
| **transformers + PyTorch** | 支持 (需配置) | 功能完整但性能较低 | 开发/测试用 |

---

## 6. 常见问题与解决方案

### 6.1 编译问题

#### 问题: 找不到 glslc

```
CMake Error: Could NOT find Vulkan (missing: glslc)
```

**解决方案**:
```bash
sudo apt install -y glslc libshaderc-dev
```

#### 问题: 找不到 CURL

```
CMake Error: Could NOT find CURL
```

**解决方案**:
```bash
sudo apt install -y libcurl4-openssl-dev
```

### 6.2 运行问题

#### 问题: Vulkan 设备未检测到

**解决方案**:
```bash
# 确保 amdgpu 驱动已加载
sudo modprobe amdgpu

# 检查 DRM 设备
ls -la /dev/dri/

# 验证 Vulkan
vulkaninfo --summary
```

#### 问题: 首次运行编译着色器很慢

这是正常现象，首次运行时需要编译 Vulkan 着色器：
```
ggml_vulkan: compiling shaders...
```

后续运行会使用缓存，速度会显著提升。

#### 问题: 某些操作回退到 CPU

如果看到警告：
```
ggml_vulkan: op XYZ not supported, falling back to CPU
```

这是正常的，某些不常用的操作可能在 CPU 上执行，不影响主要推理性能。

### 6.3 内存问题

#### 问题: Out of Memory

**解决方案**:
1. 使用更小的量化格式 (如 Q4_0)
2. 减少上下文长度 (-c 参数)
3. 使用较小的模型

```bash
# 检查当前内存使用
amd-smi | grep "Mem-Usage"
```

---

## 7. 附录

### 7.1 完整参数列表

#### llama-cli 参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `-m, --model` | 模型文件路径 | `-m model.gguf` |
| `-ngl, --n-gpu-layers` | GPU 层数 | `-ngl 99` |
| `-c, --ctx-size` | 上下文长度 | `-c 4096` |
| `-n, --n-predict` | 最大生成 token 数 | `-n 256` |
| `-p, --prompt` | 输入提示词 | `-p "Hello"` |
| `-cnv, --conversation` | 启用对话模式 | |
| `-sys, --system-prompt` | 系统提示词 | |
| `--temp` | 温度 | `--temp 0.7` |
| `--top-k` | Top-K 采样 | `--top-k 40` |
| `--top-p` | Top-P 采样 | `--top-p 0.95` |
| `-t, --threads` | CPU 线程数 | `-t 32` |
| `--device` | GPU 设备 ID | `--device 0` |

#### llama-server 参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--host` | 监听地址 | `--host 0.0.0.0` |
| `--port` | 监听端口 | `--port 8080` |
| `--api-key` | API 密钥 | `--api-key secret` |
| `--parallel` | 并行请求数 | `--parallel 4` |
| `--batch-size` | 批处理大小 | `--batch-size 512` |

### 7.2 目录结构

```
~/llama.cpp/
├── build/
│   └── bin/
│       ├── llama-cli          # 命令行工具
│       ├── llama-server       # API 服务器
│       ├── llama-quantize     # 量化工具
│       ├── llama-bench        # 基准测试
│       └── ...
├── convert_hf_to_gguf.py      # HF 转 GGUF 脚本
└── ...

~/data/models/                  # 模型存放目录 (示例)
├── Qwen3-30B-A3B-Q4_K_M.gguf
└── ...
```

### 7.3 监控命令速查

```bash
# GPU 状态
amd-smi
rocm-smi

# GPU 详细信息
rocminfo

# Vulkan 设备信息
vulkaninfo --summary

# 实时监控
watch -n 2 amd-smi
watch -n 2 'rocm-smi | grep -E "(GPU|Temp|Memory)"'

# CPU/内存监控
htop
free -h
```

### 7.4 参考资料

#### 官方文档
- [ROCm 7.9 Documentation](https://rocm.docs.amd.com/en/7.9.0-preview/)
- [llama.cpp GitHub](https://github.com/ggml-org/llama.cpp)
- [AMD Radeon 8060S](https://www.amd.com/en/products/processors/laptop/ryzen/ai-300-series/amd-ryzen-ai-max-plus-395.html)

#### 社区资源
- [AMD Strix Halo GPU Performance](https://llm-tracker.info/AMD-Strix-Halo-(Ryzen-AI-Max+-395)-GPU-Performance)
- [llama.cpp Vulkan Performance Discussion](https://github.com/ggml-org/llama.cpp/discussions/10879)
- [Framework Strix Halo Setup Guide](https://github.com/Gygeek/Framework-strix-halo-llm-setup)
- [Strix Halo llama.cpp Performance](https://strixhalo.wiki/AI/llamacpp-performance)

### 7.5 测试可复现性说明

#### 测试脚本

本报告的性能数据使用以下脚本生成：

```bash
# 测试脚本位置
~/lpl_docs/llamacpp_amd/benchmark/run_benchmark.sh

# 结果分析脚本
~/lpl_docs/llamacpp_amd/benchmark/analyze_results.py
```

#### 重现测试

```bash
# 1. 确保模型文件存在
ls ~/data/models/Qwen3-30B-A3B-Q4_K_M.gguf

# 2. 单项 GPU 测试 (示例: pp512, tg256)
~/llama.cpp/build/bin/llama-bench \
    -m ~/data/models/Qwen3-30B-A3B-Q4_K_M.gguf \
    -ngl 99 \
    -p 512 -n 256 \
    -r 2

# 3. 单项 CPU 测试 (示例: pp512, tg256)
~/llama.cpp/build/bin/llama-bench \
    -m ~/data/models/Qwen3-30B-A3B-Q4_K_M.gguf \
    -ngl 0 -t 32 \
    -p 512 -n 256 \
    -r 2

# 4. 运行完整测试
cd ~/lpl_docs/llamacpp_amd/benchmark
./run_benchmark.sh
```

#### 原始数据文件

| 文件 | 路径 |
|------|------|
| GPU 测试结果 (Q4_K_M) | `benchmark/results/benchmark_gpu_20260113_102207.csv` |
| CPU 测试结果 (Q4_K_M) | `benchmark/results/benchmark_cpu_20260113_103426.csv` |
| Q4_K_M 对比测试 | `benchmark/results/q4km_20260115_090831.csv` |
| F16 对比测试 | `benchmark/results/f16_20260115_090831.csv` |
| 分析报告 | `benchmark/analysis.md` |

### 7.6 测试环境配置清单

```bash
# 系统信息
$ uname -a
Linux 6.11.0-17-generic

$ lsb_release -a
Ubuntu 24.04 LTS

# llama.cpp 版本
$ llama-cli --version
version: 7709 (1051ecd28)

# GPU 信息
$ vulkaninfo --summary | grep deviceName
deviceName = AMD Radeon 8060S (RADV GFX1151)

# 内存信息
$ free -h
total: 125Gi

# ROCm 版本
$ cat /opt/rocm/.info/version
7.9.0
```

---

**文档版本**: 1.2 (内部版)
**最后更新**: 2026-01-15
**状态**: 已完成
