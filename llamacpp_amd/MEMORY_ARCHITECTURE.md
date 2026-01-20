# AMD Ryzen AI MAX+ 395 内存架构

## 统一内存架构 (UMA)

AMD Ryzen AI MAX+ 395 使用**统一内存架构**，CPU、GPU 和 NPU 共享同一块物理内存。

```
┌─────────────────────────────────────────────────────────┐
│              128GB LPDDR5X 统一物理内存                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   ┌─────────────────┐  ┌─────────────────────────────┐  │
│   │   GPU VRAM      │  │      系统内存               │  │
│   │   (iGPU 专用)    │  │   (CPU + NPU 共享)         │  │
│   │                 │  │                             │  │
│   │   默认: 64GB    │  │   默认: ~62GB              │  │
│   │   最大: 96GB    │  │   最小: ~32GB              │  │
│   │                 │  │                             │  │
│   │   ┌───────────┐ │  │  ┌───────┐  ┌───────────┐  │  │
│   │   │ Radeon    │ │  │  │ Zen 5 │  │ XDNA 2    │  │  │
│   │   │ 8060S     │ │  │  │ CPU   │  │ NPU       │  │  │
│   │   │ (gfx1151) │ │  │  │16C/32T│  │ 50 TOPS   │  │  │
│   │   └───────────┘ │  │  └───────┘  └───────────┘  │  │
│   └─────────────────┘  └─────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 与独显的区别

| 特性 | 独立显卡 (如 RTX 4090) | APU (Ryzen AI MAX+ 395) |
|------|----------------------|-------------------------|
| GPU 显存 | 独立 GDDR6X (24GB) | 从系统内存分配 |
| CPU 内存 | 独立 DDR5 | 与 GPU 共享 |
| 内存总量 | GPU + CPU 分开 | 统一 128GB |
| 内存带宽 | GPU 1TB/s, CPU 90GB/s | 统一 256GB/s |
| 数据传输 | 需 PCIe 传输 | 零拷贝直接访问 |

## 内存分配方案

### AMD Variable Graphics Memory (VGM)

AMD 允许灵活配置 GPU 和系统内存的分配比例：

| 系统内存 | 最大 GPU VRAM | 剩余系统内存 |
|---------|--------------|-------------|
| 32 GB | 24 GB | 8 GB |
| 64 GB | 48 GB | 16 GB |
| **128 GB** | **96 GB** | **32 GB** |

### 本机配置

| 项目 | 默认值 | 修改后 |
|------|--------|--------|
| GPU VRAM | 64 GB | **96 GB** |
| 系统可用 (CPU+NPU) | 62 GB | 32 GB |
| GTT (传输缓冲) | 31 GB | ~31 GB |

## 查看当前配置

```bash
# GPU VRAM 大小
cat /sys/class/drm/card*/device/mem_info_vram_total | awk '{print $1/1024/1024/1024 " GB"}'

# GTT 大小
cat /sys/class/drm/card*/device/mem_info_gtt_total | awk '{print $1/1024/1024/1024 " GB"}'

# 系统可用内存
free -h | grep Mem | awk '{print $2}'

# 内核启动参数
cat /proc/cmdline
```

## CPU/GPU/NPU 实际可用内存

### 当前配置 (Kernel 6.11, BIOS 默认)

| 处理器 | 实际可用 | 后端 | 说明 |
|--------|---------|------|------|
| **GPU** | **~95 GB** | Vulkan | 64GB VRAM + 31GB GTT |
| **GPU** | ~15 GB | ROCm/HIP | 内核 bug，只能看到部分 |
| **CPU** | **~62 GB** | - | 系统内存 |
| **NPU** | 0 GB | - | 需要 kernel 6.14+ 驱动 |

### 升级后 (Kernel 6.16.9+, BIOS 设为 96GB VRAM)

| 处理器 | 实际可用 | 后端 | 说明 |
|--------|---------|------|------|
| **GPU** | **96 GB** | Vulkan | 完整 VRAM |
| **GPU** | **96 GB** | ROCm/HIP | Bug 已修复 |
| **CPU** | **~32 GB** | - | 系统内存 (减少) |
| **NPU** | 动态 | XDNA | 从系统内存分配，通常几 GB |

### 内存分配图示

```
当前 (Kernel 6.11, 64GB VRAM):
┌─────────────────────────────────────────────────────────────┐
│                    128GB LPDDR5X                            │
├────────────────────────────┬────────────────────────────────┤
│   GPU VRAM: 64GB           │   系统内存: ~62GB              │
│   ┌────────────────────┐   │   ┌────────────────────────┐   │
│   │ Vulkan: 64GB VRAM  │   │   │ CPU: ~62GB             │   │
│   │ + 31GB GTT = ~95GB │   │   │ NPU: 驱动未加载        │   │
│   │ ROCm: 只能用 ~15GB │   │   │                        │   │
│   └────────────────────┘   │   └────────────────────────┘   │
└────────────────────────────┴────────────────────────────────┘

升级后 (Kernel 6.16.9+, 96GB VRAM):
┌─────────────────────────────────────────────────────────────┐
│                    128GB LPDDR5X                            │
├──────────────────────────────────────┬──────────────────────┤
│   GPU VRAM: 96GB                     │  系统内存: ~32GB     │
│   ┌────────────────────────────┐     │  ┌────────────────┐  │
│   │ Vulkan: 96GB               │     │  │ CPU: ~30GB     │  │
│   │ ROCm: 96GB (bug 已修复)    │     │  │ NPU: 动态分配  │  │
│   └────────────────────────────┘     │  └────────────────┘  │
└──────────────────────────────────────┴──────────────────────┘
```

## 内存分配是否需要重启？

| 操作 | 是否需要重启 | 说明 |
|------|-------------|------|
| **修改 VRAM/系统内存比例** | ✅ 需要重启 | BIOS 设置，启动时确定 |
| **升级内核版本** | ✅ 需要重启 | 新内核需重启生效 |
| GPU 使用已分配的内存 | ❌ 动态 | 运行时按需使用 |
| CPU 使用已分配的内存 | ❌ 动态 | 运行时按需使用 |
| NPU 使用系统内存 | ❌ 动态 | 运行时按需分配 |

**总结**: VRAM 和系统内存的**分配比例**在启动时确定，需要重启才能修改。但在各自的内存池内，使用是**动态**的。

## 内核版本兼容性

| 内核版本 | GPU (Vulkan) | GPU (ROCm) | NPU | 稳定性 |
|---------|--------------|------------|-----|--------|
| **6.11 (当前)** | ~95GB ✅ | ~15GB ⚠️ | ❌ | ✅ 稳定 |
| 6.14 | ~95GB | ~15GB ⚠️ | ✅ | ✅ 稳定 |
| **6.16.9+** | 96GB ✅ | 96GB ✅ | ✅ | ⚠️ 部分问题 |
| 6.17.9 | ? | ? | ? | ❌ 有崩溃报告 |
| 6.18+ | ? | ❌ | ? | ❌ 破坏 ROCm |

**注意**: `amdttm` 内核参数是给 **AMD Instinct 专业卡** 使用的，对消费级 Strix Halo **无效**。

## 推荐配置

### 场景 1: llama.cpp 推理 (当前最佳)

- **内核**: 6.11 (保持当前)
- **后端**: Vulkan
- **GPU 可用**: ~95GB
- **优点**: 稳定，已验证

### 场景 2: PyTorch/ROCm 训练

- **内核**: 6.16.9 (需升级)
- **后端**: ROCm/HIP
- **GPU 可用**: 96GB
- **风险**: 可能有其他兼容性问题

### 场景 3: NPU 使用

- **内核**: 6.14+ (需升级)
- **驱动**: amdxdna
- **适用**: 小模型低功耗推理

## 修改 VRAM 分配

### 方法 1: BIOS 设置

1. 重启进入 BIOS (通常按 F2 或 Del)
2. 查找以下选项：
   - UMA Frame Buffer Size
   - VRAM Size / iGPU Memory
   - Variable Graphics Memory (VGM)
3. 设置为 96GB 或最大值
4. 保存并重启

### 方法 2: 升级内核到 6.16.9+

```bash
# Ubuntu - 安装 mainline 工具
sudo add-apt-repository ppa:cappelikan/ppa
sudo apt update && sudo apt install mainline

# 安装新内核
sudo mainline --install 6.16.9
sudo reboot
```

**升级前注意**:
- 避免 linux-firmware-20251125 (AMD 已召回)
- 6.17.9 有崩溃报告
- 6.18+ 破坏 ROCm

## 查看当前配置

```bash
# GPU VRAM (需要 amdgpu 驱动加载)
cat /sys/class/drm/card*/device/mem_info_vram_total 2>/dev/null | awk '{print $1/1024/1024/1024 " GB"}'

# Vulkan 可见内存 (推荐)
vulkaninfo 2>/dev/null | grep -A10 "memoryHeaps"

# 系统可用内存
free -h | grep Mem | awk '{print $2}'

# 内核版本
uname -r

# 内核启动参数
cat /proc/cmdline
```

## 模型内存需求参考

| 模型 | 大小 | 当前可用 (~95GB) | 升级后 (96GB) |
|------|------|-----------------|---------------|
| Qwen3-30B Q4_K_M | 17 GB | ✅ 充裕 | ✅ 充裕 |
| Qwen3-30B Q8_0 | ~32 GB | ✅ 可行 | ✅ 充裕 |
| Qwen3-30B BF16 | 60 GB | ✅ 可行 | ✅ 充裕 |
| 70B Q4_K_M | ~40 GB | ✅ 可行 | ✅ 充裕 |
| 70B BF16 | ~140 GB | ❌ 不够 | ❌ 不够 |

## NPU 内存使用

XDNA 2 NPU 特点：
- **驱动要求**: kernel 6.14+ (amdxdna)
- **内存分配**: 从系统内存动态分配
- **典型使用量**: 几 GB
- **适用场景**: 小模型、低功耗推理
- **不适用**: llama.cpp (不支持 XDNA)

## 参考资料

- [AMD Variable Graphics Memory FAQ](https://www.amd.com/en/blogs/2025/faqs-amd-variable-graphics-memory-vram-ai-model-sizes-quantization-mcp-more.html)
- [Linux VRAM 分配调整 (Jeff Geerling)](https://www.jeffgeerling.com/blog/2025/increasing-vram-allocation-on-amd-ai-apus-under-linux)
- [AMD Ryzen AI MAX+ 395 官方页面](https://www.amd.com/en/products/processors/laptop/ryzen/ai-300-series/amd-ryzen-ai-max-plus-395.html)
