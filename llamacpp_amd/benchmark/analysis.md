# llama.cpp 性能测试报告

## 测试环境

- **硬件**: AMD Ryzen AI MAX+ 395
  - CPU: 16 核 32 线程 (Zen 5)
  - GPU: Radeon 8060S (gfx1151, Vulkan 后端)
  - 内存: 128GB LPDDR5X
- **模型**: Qwen3-30B-A3B-Q4_K_M.gguf (17.28 GB)
- **日期**: 2026-01-13
- **llama.cpp**: build 1051ecd28 (#7709)

## GPU vs CPU 性能对比

### Prefill (Prompt Processing)

| Tokens | GPU (t/s) | CPU (t/s) | GPU/CPU |
|--------|-----------|-----------|---------|
| 128    | 502       | 165       | 3.0x    |
| 512    | 988       | 462       | 2.1x    |
| 1024   | 856       | 433       | 2.0x    |
| 2048   | 798       | 402       | 2.0x    |
| 4096   | 705       | 356       | 2.0x    |

### Decode (Token Generation)

| Tokens | GPU (t/s) | CPU (t/s) | GPU/CPU |
|--------|-----------|-----------|---------|
| 128    | 88        | 10.3      | 8.5x    |
| 256    | 86        | 10.3      | 8.4x    |
| 512    | 84        | 10.2      | 8.2x    |

### 汇总

| 指标 | GPU (Vulkan) | CPU (32线程) | GPU/CPU |
|------|--------------|--------------|---------|
| **Prefill 平均** | 770 t/s | 364 t/s | 2.1x |
| **Decode 平均** | 86 t/s | 10 t/s | 8.4x |

## 分析

### GPU 性能特点

1. **Prefill 峰值在 512 tokens**: ~990 t/s
2. **长上下文性能衰减**: pp4096 比 pp512 慢约 30%
3. **Decode 非常稳定**: 83-90 t/s，标准差很小

### CPU 性能特点

1. **Prefill 相对较快**: ~360 t/s 平均
2. **Decode 明显较慢**: ~10 t/s
3. **32 线程利用率良好**

### 对比结论

1. **Decode 速度**: GPU 是 CPU 的 **8.4 倍** - 最显著差异
2. **Prefill 速度**: GPU 是 CPUURE的 **2.1 倍**
3. **长 prompt 场景**: GPU 优势更明显

## 使用建议

### 推荐配置

```bash
# 日常使用 (GPU)
llama-cli -m model.gguf -ngl 99 -c 4096 -cnv

# GPU 内存不足时 (CPU)
llama-cli -m model.gguf -ngl 0 -t 32 -c 4096 -cnv
```

### 场景选择

| 场景 | 推荐后端 | 原因 |
|------|----------|------|
| 交互对话 | GPU | Decode 8x 更快 |
| 长文档处理 | GPU | Prefill 2x 更快 |
| 批量处理 | GPU | 吞吐量更高 |
| GPU 内存不足 | CPU | 可行备选 |

## 原始数据

- GPU 结果: `results/benchmark_gpu_20260113_102207.csv`
- CPU 结果: `results/benchmark_cpu_20260113_103426.csv`
