# GPU 监控工具说明

本文档说明如何使用 amd-smi 等工具监控 AMD GPU 状态。

## amd-smi 概览

`amd-smi` 是 AMD 的系统管理接口工具，类似于 NVIDIA 的 `nvidia-smi`。

### 基本命令

```bash
# 实时监控 (每 2 秒刷新)
watch -n 2 amd-smi

# 单次查看
amd-smi

# 查看详细信息
amd-smi static
```

## amd-smi 输出解读

### 示例输出

```
+------------------------------------------------------------------------------+
| AMD-SMI 26.1.0+f41fc94b      amdgpu version: 6.11.0-17 ROCm version: 7.9.0    |
| VBIOS version: 023.011.000.039.000001                                        |
| Platform: Linux Baremetal                                                    |
|-------------------------------------+----------------------------------------|
| BDF                        GPU-Name | Mem-Uti   Temp   UEC       Power-Usage |
| GPU  HIP-ID  OAM-ID  Partition-Mode | GFX-Uti    Fan               Mem-Usage |
|=====================================+========================================|
| 0000:c6:00.0    AMD Radeon Graphics | N/A        N/A   0             N/A/0 W |
|   0       0     N/A             N/A | N/A        N/A          18360/65536 MB |
+-------------------------------------+----------------------------------------+
+------------------------------------------------------------------------------+
| Processes:                                                                   |
|  GPU        PID  Process Name          GTT_MEM  VRAM_MEM  MEM_USAGE     CU % |
|==============================================================================|
|  No running processes found                                                  |
+------------------------------------------------------------------------------+
```

### 头部信息

| 字段 | 值 | 说明 |
|------|-----|------|
| **AMD-SMI** | 26.1.0+f41fc94b | amd-smi 工具版本 |
| **amdgpu version** | 6.11.0-17 | 内核驱动版本 (对应 kernel 6.11) |
| **ROCm version** | 7.9.0 | ROCm 软件栈版本 |
| **VBIOS version** | 023.011.000.039 | GPU 固件版本 |
| **Platform** | Linux Baremetal | 物理机 (非虚拟机) |

### GPU 状态信息

| 字段 | 说明 | APU 特殊情况 |
|------|------|-------------|
| **BDF** | PCI 总线地址 | 0000:c6:00.0 |
| **GPU-Name** | GPU 名称 | AMD Radeon Graphics |
| **HIP-ID** | HIP 设备 ID | 0 (用于 PyTorch/ROCm) |
| **OAM-ID** | OAM 模块 ID | N/A (数据中心 GPU 用) |
| **Partition-Mode** | GPU 分区模式 | N/A (APU 不支持) |

### 资源使用信息

| 字段 | 说明 | APU 显示 |
|------|------|---------|
| **Mem-Uti** | 显存利用率 | N/A (统一内存无法精确测量) |
| **Temp** | GPU 温度 | N/A (APU 可能不单独报告) |
| **UEC** | 未纠正错误计数 | 0 (正常) |
| **Power-Usage** | 功耗 | N/A (APU 集成在 SoC) |
| **GFX-Uti** | 图形引擎利用率 | N/A |
| **Fan** | 风扇转速 | N/A (APU 无独立风扇) |
| **Mem-Usage** | 内存使用/总量 | 18360/65536 MB |

### 进程信息

运行 llama.cpp 时会显示：

| 字段 | 说明 |
|------|------|
| **GPU** | GPU 设备 ID |
| **PID** | 进程 ID |
| **Process Name** | 进程名称 |
| **GTT_MEM** | GTT 内存使用 |
| **VRAM_MEM** | 显存使用 |
| **MEM_USAGE** | 总内存使用 |
| **CU %** | 计算单元利用率 |

## 为什么很多值显示 N/A？

APU (集成显卡) 与独立显卡不同：

1. **统一内存架构**: GPU 和 CPU 共享物理内存，难以精确测量 GPU 专用内存
2. **集成在 SoC**: 功耗、温度等集成在整个芯片中，不单独报告 GPU 部分
3. **无独立风扇**: APU 使用整机散热，没有 GPU 专用风扇
4. **传感器差异**: APU 的硬件传感器与数据中心 GPU 不同

这些 N/A 是**正常的**，不影响功能。

## 关键指标解读

### Mem-Usage (最重要)

```
Mem-Usage: 18360/65536 MB
```

- **18360 MB**: 当前已使用的 GPU 可访问内存
- **65536 MB**: 总可用 GPU 内存 (64GB)
- **可用**: 65536 - 18360 = 47176 MB (~46GB)

### 运行模型时的预期变化

| 模型 | 量化 | 预期内存增加 |
|------|------|-------------|
| Qwen3-30B | Q4_K_M | ~17 GB |
| Qwen3-30B | Q8_0 | ~30 GB |
| Llama-70B | Q4_K_M | ~40 GB |

## 其他监控工具

### rocm-smi

```bash
# 如果安装了 ROCm
rocm-smi

# 监控模式
watch -n 1 rocm-smi
```

### rocminfo

```bash
# 查看 GPU 硬件信息
rocminfo
```

输出包含：
- Agent 信息 (CPU/GPU)
- 计算单元数
- 最大频率
- 内存信息

### vulkaninfo

```bash
# 查看 Vulkan 设备信息
vulkaninfo --summary
```

### htop

```bash
# 监控 CPU 使用
htop
```

## 监控脚本示例

### 实时监控脚本

```bash
#!/bin/bash
# monitor_gpu.sh

while true; do
    clear
    echo "=== GPU 状态 ==="
    amd-smi 2>/dev/null | grep -A 10 "AMD-SMI"
    echo ""
    echo "=== 内存使用 ==="
    free -h
    echo ""
    echo "=== CPU 负载 ==="
    uptime
    sleep 2
done
```

### llama.cpp 运行时监控

在一个终端运行 llama.cpp：
```bash
~/llama.cpp/build/bin/llama-cli -m model.gguf -ngl 99 -cnv
```

在另一个终端监控：
```bash
watch -n 2 amd-smi
```

## 故障排除

### 问题1: amd-smi 显示 Python 错误

```bash
# 这是已知问题，不影响 GPU 功能
# 可以使用 rocm-smi 替代
rocm-smi
```

### 问题2: 看不到进程信息

确保进程正在使用 GPU：
```bash
# 检查 llama-cli 是否使用 GPU
ps aux | grep llama
```

### 问题3: 内存使用不更新

APU 的统一内存可能不会实时反映在 amd-smi 中：
```bash
# 使用 free 查看系统内存
free -h
```

## 性能监控建议

### 运行前

```bash
# 记录基线内存
amd-smi | grep "Mem-Usage"
free -h
```

### 运行中

```bash
# 持续监控
watch -n 2 'amd-smi; echo "---"; free -h'
```

### 运行后

```bash
# 检查是否释放内存
amd-smi | grep "Mem-Usage"
```
