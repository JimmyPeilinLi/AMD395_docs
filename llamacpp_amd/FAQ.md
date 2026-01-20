# 常见问题 (FAQ)

本文档收集了在 AMD Strix Halo 上使用 llama.cpp 时遇到的常见问题和解决方案。

## 安装相关

### Q1: 编译时找不到 glslc

**错误：**
```
CMake Error: Could NOT find Vulkan (missing: glslc)
```

**解决方案：**
```bash
sudo apt install -y glslc libshaderc-dev
```

### Q2: 编译时找不到 CURL

**错误：**
```
CMake Error: Could NOT find CURL
```

**解决方案：**
```bash
sudo apt install -y libcurl4-openssl-dev
```

### Q3: Vulkan 设备未检测到

**检查步骤：**
```bash
# 1. 检查 amdgpu 驱动
lsmod | grep amdgpu

# 2. 如果未加载，手动加载
sudo modprobe amdgpu

# 3. 检查 DRM 设备
ls -la /dev/dri/

# 4. 检查 Vulkan
vulkaninfo --summary
```

## 运行相关

### Q4: `--interactive` 参数无效

**错误：**
```
error: invalid argument: --interactive
```

**解决方案：**
新版 llama.cpp 使用 `-cnv` 或 `--conversation` 替代：
```bash
llama-cli -m model.gguf -ngl 99 -cnv
```

### Q5: 模型加载失败

**检查步骤：**
1. 确认模型文件存在且完整
2. 检查文件权限
3. 确认是 GGUF 格式

```bash
# 检查文件
ls -lh model.gguf

# 检查格式
file model.gguf
```

### Q6: GPU 内存不足

**症状：**
```
ggml_vulkan: not enough memory
或
Not enough memory for command submission
```

**解决方案：**
1. 使用更小的量化版本 (Q4_K_M instead of BF16)
2. 减少上下文长度 (`-c 2048` instead of `-c 8192`)
3. 部分层放在 CPU (`-ngl 20` instead of `-ngl 99`)
4. **扩展 GPU VRAM 分配** (见 Q6.1)

### Q6.1: 如何增加 GPU VRAM？

当前 Vulkan 可访问内存约 **95GB** (64GB VRAM + 31GB GTT)。

**查看实际可用内存:**
```bash
vulkaninfo 2>/dev/null | grep -A5 "memoryHeaps"
# Device Local (VRAM): ~63 GB
# Host Visible (GTT): ~31 GB
# 总计: ~95 GB
```

**要获得完整 96GB VRAM 显示:**
1. **升级内核到 6.16.9+** (推荐) - 无需任何参数
2. 或在 BIOS 中调整 UMA/VRAM 设置

**注意:** `amdttm` 参数是给 AMD Instinct 专业卡用的，对消费级 Strix Halo **无效**。

详见 [MEMORY_ARCHITECTURE.md](MEMORY_ARCHITECTURE.md)

### Q6.2: 为什么系统内存只显示 62GB？

这是正常的。AMD APU 使用统一内存架构：

```
128GB 物理内存 = GPU VRAM (64GB) + 系统可用 (62GB) + 系统保留 (~2GB)
```

GPU VRAM 从系统内存中预留，所以系统可用会相应减少。

### Q6.3: CPU 和 GPU 的内存可以互相访问吗？

是的，这是 UMA 的优势：
- GPU 可以**读取**整个 128GB 内存
- GPU 只能**写入**其预留的 VRAM 部分
- 没有 PCIe 传输开销

### Q6.4: 内存分配需要重启吗？

| 操作 | 是否需要重启 |
|------|-------------|
| 修改 VRAM/系统内存比例 (BIOS) | ✅ 需要 |
| 升级内核版本 | ✅ 需要 |
| GPU/CPU 使用已分配内存 | ❌ 动态 |

### Q6.5: NPU 能用多少内存？

NPU (XDNA 2) 从系统内存动态分配，通常只需几 GB。但需要 kernel 6.14+ 才能加载 amdxdna 驱动。llama.cpp 不支持 NPU。

### Q6.6: 哪个内核版本最适合 Strix Halo？

| 内核版本 | GPU (Vulkan) | GPU (ROCm) | NPU | 稳定性 |
|---------|--------------|------------|-----|--------|
| **6.11 (当前)** | ~95GB ✅ | ~15GB ⚠️ | ❌ | ✅ 稳定 |
| 6.14 | ~95GB | ~15GB ⚠️ | ✅ | ✅ 稳定 |
| 6.16.9+ | 96GB ✅ | 96GB ✅ | ✅ | ⚠️ 部分问题 |
| 6.17.9 | ? | ? | ? | ❌ 有崩溃 |
| 6.18+ | ? | ❌ | ? | ❌ 破坏 ROCm |

**推荐**: llama.cpp 用户保持 6.11；需要 ROCm 完整内存则升级到 6.16.9。

## 性能相关

### Q7: 为什么不用 HIP/ROCm 后端？

在 gfx1151 (Strix Halo) 上，HIP/ROCm 后端存在严重性能问题：
- 90%+ 时间花在内存拷贝
- Flash Attention 不工作
- 实际利用率只有 ~2%

**Vulkan 后端是 gfx1151 的最佳选择。**

### Q8: 为什么不能用 sglang/vLLM？

sglang 和 vLLM 只支持数据中心 GPU (gfx942/gfx950)：
- 缺少 gfx1151 的优化内核
- 硬件不支持 FP8
- 编译会直接失败

详见 [AMD_ARCHITECTURE.md](AMD_ARCHITECTURE.md)。

### Q9: CPU vs GPU 哪个更快？

在当前配置下：
- **GPU (Vulkan)**: 推荐，性能更好
- **CPU (32线程)**: 备选方案

```bash
# GPU 运行
llama-cli -m model.gguf -ngl 99

# CPU 运行
llama-cli -m model.gguf -t 32
```

### Q10: 怎么提高推理速度？

1. **使用更激进的量化**: Q4_K_M > Q5_K_M > Q8_0
2. **减少上下文长度**: `-c 2048` instead of `-c 8192`
3. **确保所有层在 GPU**: `-ngl 99`
4. **调整批处理大小** (服务器): `--batch-size 512`

## 模型相关

### Q11: HuggingFace 模型怎么转换？

```bash
# 标准转换
python ~/llama.cpp/convert_hf_to_gguf.py \
    /path/to/model \
    --outfile model.gguf \
    --outtype f16

# 然后量化
~/llama.cpp/build/bin/llama-quantize \
    model.gguf \
    model-Q4_K_M.gguf \
    Q4_K_M
```

### Q12: 转换 Qwen3 MoE 失败

**错误：**
```
ValueError: Can not map tensor 'model.layers.0.mlp.switch_mlp.down_proj.weight'
```

**原因：** 某些 Qwen3 MoE 变体使用非标准命名，llama.cpp 暂不支持。

**解决方案：**
1. 下载已转换的 GGUF 版本
2. 等待 llama.cpp 更新

### Q13: 怎么验证 GGUF 模型正确？

```bash
# 查看模型信息
llama-cli -m model.gguf --verbose 2>&1 | head -50

# 比较关键参数是否与原始模型一致：
# - 层数 (block_count)
# - 隐藏维度 (embedding_length)
# - 注意力头 (attention.head_count)
# - 词汇表大小 (vocab_size)
```

## 监控相关

### Q14: amd-smi 显示很多 N/A

这是**正常的**。APU (集成显卡) 与独立显卡不同：
- 统一内存架构无法精确测量 GPU 专用内存
- 功耗/温度集成在 SoC 中
- 无独立风扇

关注 `Mem-Usage` 即可。

### Q15: 怎么监控 GPU 使用？

```bash
# 方法1: amd-smi (推荐)
watch -n 2 amd-smi

# 方法2: rocm-smi
watch -n 1 rocm-smi

# 方法3: 系统内存
watch -n 2 free -h
```

## API 服务器相关

### Q16: 怎么测试 API 服务器？

**启动服务器：**
```bash
llama-server -m model.gguf -ngl 99 --host 0.0.0.0 --port 8080
```

**测试请求：**
```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 100
  }'
```

### Q17: Python 怎么调用 API？

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="qwen",
    messages=[{"role": "user", "content": "你好"}]
)
print(response.choices[0].message.content)
```

## NPU 相关

### Q18: 能用 NPU 加速吗？

**不能。** llama.cpp 不支持 AMD XDNA NPU。

NPU 需要：
- Kernel 6.14+ (amdxdna 驱动)
- 专门的框架 (如 AMD Ryzen AI SDK)
- 不适合大模型 (主要用于小模型低功耗推理)

### Q19: 未来会支持 NPU 吗？

可能需要等待：
1. llama.cpp 添加 XDNA 后端
2. AMD 提供更好的 NPU 软件栈
3. 社区开发相关支持

## 其他问题

### Q20: 怎么查看帮助？

```bash
# 命令行工具
llama-cli --help

# 服务器
llama-server --help

# 量化工具
llama-quantize --help
```

### Q21: 怎么更新 llama.cpp？

```bash
cd ~/llama.cpp
git pull
cmake -B build -DGGML_VULKAN=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j$(nproc)
```

### Q22: 哪里报告问题？

- **llama.cpp issues**: https://github.com/ggml-org/llama.cpp/issues
- **ROCm issues**: https://github.com/ROCm/ROCm/issues
- **Strix Halo Wiki**: https://strixhalo.wiki/

## 快速参考

### 最常用命令

```bash
# 交互对话
~/llama.cpp/build/bin/llama-cli -m ~/data/models/Qwen3-30B-A3B-Q4_K_M.gguf -ngl 99 -c 4096 -cnv

# 单次生成
~/llama.cpp/build/bin/llama-cli -m ~/data/models/Qwen3-30B-A3B-Q4_K_M.gguf -ngl 99 -c 4096 -n 256 -p "你好"

# API 服务器
~/llama.cpp/build/bin/llama-server -m ~/data/models/Qwen3-30B-A3B-Q4_K_M.gguf -ngl 99 -c 4096 --host 0.0.0.0 --port 8080

# 监控 GPU
watch -n 2 amd-smi
```

### 关键参数速查

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `-m` | 模型路径 | - |
| `-ngl` | GPU 层数 | 99 (全部) |
| `-c` | 上下文长度 | 4096 |
| `-n` | 最大生成 | 256 |
| `-cnv` | 对话模式 | - |
| `-t` | CPU 线程 | 32 |
