# 模型转换指南

本文档说明如何将 HuggingFace 模型转换为 GGUF 格式。

## GGUF 格式简介

GGUF (GGML Unified Format) 是 llama.cpp 使用的模型格式：
- 单文件包含模型权重和元数据
- 支持多种量化方式
- 跨平台兼容

## 转换工具

llama.cpp 提供了转换脚本：

```bash
~/llama.cpp/convert_hf_to_gguf.py
```

## 环境准备

### 安装 Python 依赖

```bash
# 创建/激活 conda 环境
conda activate kllamacpp

# 安装依赖
pip install numpy torch transformers sentencepiece protobuf accelerate safetensors
```

## 标准转换流程

### 步骤1：转换为 GGUF (保持精度)

```bash
python ~/llama.cpp/convert_hf_to_gguf.py \
    /path/to/huggingface/model \
    --outfile /path/to/output.gguf \
    --outtype f16
```

**参数说明：**
- `--outtype f16`: 输出 FP16 精度
- `--outtype bf16`: 输出 BF16 精度 (如果支持)
- `--outtype f32`: 输出 FP32 精度

### 步骤2：量化 (可选但推荐)

```bash
~/llama.cpp/build/bin/llama-quantize \
    input.gguf \
    output-Q4_K_M.gguf \
    Q4_K_M
```

### 常用量化格式

| 格式 | 大小 | 质量 | 推荐场景 |
|------|------|------|---------|
| Q8_0 | ~50% | 很好 | 质量要求高 |
| Q6_K | ~42% | 好 | 平衡 |
| Q5_K_M | ~35% | 好 | 平衡 |
| Q4_K_M | ~29% | 可接受 | 内存有限 |
| Q4_0 | ~25% | 一般 | 最小内存 |
| Q3_K_M | ~22% | 较差 | 极限压缩 |

## 验证转换后的模型

### 检查模型信息

```bash
~/llama.cpp/build/bin/llama-cli -m model.gguf --verbose 2>&1 | head -50
```

### 比较参数

**原始模型 config.json:**
```json
{
  "hidden_size": 2048,
  "num_hidden_layers": 48,
  "num_attention_heads": 32,
  "num_key_value_heads": 4,
  "vocab_size": 151936
}
```

**GGUF 模型元数据:**
```
llama_model_loader: - kv  8: qwen3moe.embedding_length = 2048
llama_model_loader: - kv  6: qwen3moe.block_count = 48
llama_model_loader: - kv 10: qwen3moe.attention.head_count = 32
llama_model_loader: - kv 11: qwen3moe.attention.head_count_kv = 4
```

确保这些关键参数一致。

## 特殊情况处理

### Qwen3 MoE 模型 (switch_mlp)

某些 Qwen3 MoE 模型使用 `switch_mlp` 命名约定，llama.cpp 转换脚本可能不支持：

**错误示例:**
```
ValueError: Can not map tensor 'model.layers.0.mlp.switch_mlp.down_proj.weight'
```

**解决方案:**
1. 下载已转换的 GGUF 版本 (推荐)
2. 等待 llama.cpp 更新支持

### 查看模型权重结构

```python
from safetensors import safe_open

with safe_open("model.safetensors", framework="pt") as f:
    for key in f.keys():
        print(key)
```

## 已转换模型下载

对于常见模型，社区通常提供已转换的 GGUF 版本：

### HuggingFace 搜索

1. 访问 https://huggingface.co
2. 搜索 "模型名 GGUF"
3. 常见转换者: bartowski, TheBloke, etc.

### 示例

| 原始模型 | GGUF 版本 |
|---------|----------|
| Qwen3-30B-A3B | Qwen3-30B-A3B-Q4_K_M.gguf |
| Llama-3-70B | Llama-3-70B-Q4_K_M.gguf |

## 量化详解

### 基本量化 (无校准)

```bash
~/llama.cpp/build/bin/llama-quantize \
    model-f16.gguf \
    model-Q4_K_M.gguf \
    Q4_K_M
```

### 使用重要性矩阵 (imatrix)

更高质量的量化：

```bash
# 步骤1：生成重要性矩阵
~/llama.cpp/build/bin/llama-imatrix \
    -m model-f16.gguf \
    -f calibration-text.txt \
    --chunk 512 \
    -o model-imatrix.dat

# 步骤2：使用 imatrix 量化
~/llama.cpp/build/bin/llama-quantize \
    --imatrix model-imatrix.dat \
    model-f16.gguf \
    model-Q4_K_M.gguf \
    Q4_K_M
```

### 评估量化质量

使用困惑度 (perplexity) 评估：

```bash
# 下载测试数据
# wget https://huggingface.co/datasets/ggml-org/ci/resolve/main/wikitext-2-raw-v1.zip

~/llama.cpp/build/bin/llama-perplexity \
    -m model-Q4_K_M.gguf \
    -f wiki.test.raw \
    -ngl 99
```

困惑度越低越好，通常：
- FP16: 基准
- Q8_0: 接近 FP16
- Q4_K_M: 略有损失但可接受

## 当前系统模型

### 原始模型 (HuggingFace)

```
路径: ~/data/models/Qwen3-30B-A3B-bf16/
格式: safetensors (13个分片)
精度: BF16
大小: ~60GB
```

### 转换后模型 (GGUF)

```
路径: ~/data/models/Qwen3-30B-A3B-Q4_K_M.gguf
格式: GGUF V3
量化: Q4_K_M (4.86 BPW)
大小: 17.28 GB
```

### 参数对比验证

| 参数 | bf16 模型 | GGUF 模型 | 匹配 |
|------|----------|-----------|------|
| 架构 | Qwen3MoeForCausalLM | qwen3moe | ✅ |
| 层数 | 48 | 48 | ✅ |
| 隐藏维度 | 2048 | 2048 | ✅ |
| 注意力头 | 32 | 32 | ✅ |
| KV头 | 4 | 4 | ✅ |
| 专家数 | 128 | 128 | ✅ |
| 词汇表 | 151936 | 151936 | ✅ |

## 故障排除

### 问题1：内存不足

转换大模型时可能内存不足：

```bash
# 使用更多 swap
sudo fallocate -l 32G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 问题2：未知模型架构

```
Error: unknown model architecture
```

检查 llama.cpp 是否支持该模型，可能需要更新。

### 问题3：tokenizer 错误

确保安装了所有依赖：
```bash
pip install sentencepiece protobuf
```

## 参考资料

- [Qwen llama.cpp 量化指南](https://qwen.readthedocs.io/zh-cn/latest/quantization/llama.cpp.html)
- [llama.cpp 量化文档](https://github.com/ggml-org/llama.cpp/blob/master/docs/quantization.md)
