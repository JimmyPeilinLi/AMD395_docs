# llama.cpp 安装指南 (AMD Strix Halo)

本文档记录在 AMD Ryzen AI MAX+ 395 上安装 llama.cpp Vulkan 后端的完整步骤。

## 前提条件

- Ubuntu 24.04 LTS
- Kernel 6.11+
- ROCm 7.9 已安装
- amdgpu 驱动已加载

## 第一步：安装 Vulkan 依赖

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

## 第二步：验证 Vulkan 安装

```bash
vulkaninfo --summary
```

预期输出应包含：
```
GPU0:
    deviceName         = AMD Radeon 8060S (RADV GFX1151)
    driverName         = radv
    deviceType         = PHYSICAL_DEVICE_TYPE_INTEGRATED_GPU
```

## 第三步：克隆 llama.cpp

```bash
cd ~
git clone https://github.com/ggml-org/llama.cpp.git
cd llama.cpp
```

## 第四步：编译 Vulkan 后端

```bash
# 配置 cmake (启用 Vulkan)
cmake -B build -DGGML_VULKAN=ON -DCMAKE_BUILD_TYPE=Release

# 编译 (使用所有 CPU 核心)
cmake --build build --config Release -j$(nproc)
```

编译成功后，可执行文件位于 `~/llama.cpp/build/bin/` 目录。

### 主要可执行文件

| 文件 | 用途 |
|------|------|
| `llama-cli` | 命令行推理工具 |
| `llama-server` | OpenAI 兼容 API 服务器 |
| `llama-quantize` | 模型量化工具 |
| `llama-bench` | 性能基准测试 |
| `llama-perplexity` | 困惑度评估 |

## 第五步：验证 GPU 检测

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

### GPU 参数说明

| 参数 | 值 | 说明 |
|------|-----|------|
| `uma` | 1 | 统一内存架构 (与CPU共享内存) |
| `fp16` | 1 | 支持 FP16 半精度 |
| `bf16` | 0 | 不支持 BF16 |
| `warp size` | 64 | 线程束大小 |
| `shared memory` | 65536 | 共享内存 64KB |
| `matrix cores` | KHR_coopmat | 支持协作矩阵 (重要!) |

## 第六步：设置 Python 环境 (可选)

如果需要模型转换功能：

```bash
# 创建 conda 环境
conda create -n kllamacpp python=3.11 -y
conda activate kllamacpp

# 安装依赖
pip install numpy torch transformers sentencepiece protobuf accelerate safetensors
```

## 安装验证清单

- [ ] `vulkaninfo --summary` 显示 AMD Radeon 8060S
- [ ] `~/llama.cpp/build/bin/llama-cli --version` 显示 Vulkan 设备
- [ ] `amd-smi` 显示 GPU 状态
- [ ] 运行测试推理成功

## 常见安装问题

### 问题1：找不到 glslc

```
CMake Error: Could NOT find Vulkan (missing: glslc)
```

**解决方案：**
```bash
sudo apt install -y glslc libshaderc-dev
```

### 问题2：找不到 CURL

```
CMake Error: Could NOT find CURL
```

**解决方案：**
```bash
sudo apt install -y libcurl4-openssl-dev
```

### 问题3：Vulkan 设备未检测到

**解决方案：**
```bash
# 确保 amdgpu 驱动已加载
sudo modprobe amdgpu

# 检查 DRM 设备
ls -la /dev/dri/
```

## 目录结构

安装完成后的目录结构：

```
~/llama.cpp/
├── build/
│   └── bin/
│       ├── llama-cli          # 命令行工具
│       ├── llama-server       # API 服务器
│       ├── llama-quantize     # 量化工具
│       └── ...
├── convert_hf_to_gguf.py      # HF 转 GGUF 脚本
└── ...
```

## 下一步

- 阅读 [USAGE.md](USAGE.md) 了解如何运行模型
- 阅读 [MODEL_CONVERSION.md](MODEL_CONVERSION.md) 了解如何转换模型
- 阅读 [VULKAN_BACKEND.md](VULKAN_BACKEND.md) 了解 Vulkan 后端详情
