# 趋境科技 8 卡 H200 方案 DeepSeek-V3.2 测试报告

**测试时间**：2026.01.10

---

## 1. 测试环境

### 1.1 硬件配置

| 硬件名称 | 配置信息 | 数量 |
| :------- | :------- | :--- |
| CPU | Intel Xeon Platinum 8558 | 2 |
| GPU | NVIDIA H200 | 8 |
| 内存 | DDR5 64GB | 32 条 |

**服务器数量**：3 台

### 1.2 软件配置

| 软件名称 | 版本信息 |
| :------- | :------- |
| 操作系统 | Ubuntu 22.04.5 LTS |
| 内核版本 | 5.15.0-164-generic |
| 测试工具 | evalscope v1.4.1 |

---

## 2. 测试用例

### 2.1 性能测试

**测试目的**：验证趋境方案 DeepSeek-V3.2 性能表现（TTFT/TPS 等）符合预期。

**测试命令**：
```bash
evalscope perf --rate 5 --parallel 84 --number 512 \
  --model DeepSeek-V3.2 \
  --tokenizer-path /data/models/DeepSeek-V3.2 \
  --url http://127.0.0.1:8000/v1/completions \
  --api openai --dataset random \
  --max-tokens 1000 --min-tokens 1000 \
  --prefix-length 0 --min-prompt-length 6000 --max-prompt-length 6000 \
  --extra-args '{"ignore_eos": true}'
```

**预期结果**：TTFT ≤ 2s；TPOT ≤ 20ms

**测试结果**：

![性能测试结果](https://swcil84qspu.feishu.cn/space/api/box/stream/download/asynccode/?code=OWQ1OTFjMzdjZTM3M2RiZWIyYzJjODUxM2U5NThhMzBfN0xiYWlOSnpwcFQ4S2Z6b2xYVEtaZVRqaXQ1NlF2SGxfVG9rZW46QUZ3QWJIbWdFb3JGU3J4dDNGaGNyZUFxbjJmXzE3NjgwNDQ1NTg6MTc2ODA0ODE1OF9WNA)

**结论**：✅ 通过

---

### 2.2 正确性测试

**测试目的**：验证趋境方案 DeepSeek-V3.2 精度表现符合预期。

**测试命令**：
```bash
evalscope eval --model DeepSeek-V3.2 \
  --api-url http://127.0.0.1:8000/v1/ --api-key EMPTY \
  --eval-type openai_api --datasets 'aime25' \
  --stream --timeout 6000 \
  --generation-config '{"do_sample":true,"temperature":0.6,"max_tokens":56000,"extra_body":{"chat_template_kwargs":{"thinking": true}}}' \
  --dataset-args '{"aime25": {"prompt_template": "{question}\nPlease reason step by step and place your final answer within boxed{{}}. Force Requirement: 1.only the final answer should be wrapped in boxed{{}}; 2.no other numbers or text should be enclosed in boxed{{}}. 3.Answer in English"}}' \
  --eval-batch-size 16
```

**评分标准**：官方分数

**测试结果**：

![正确性测试结果](https://swcil84qspu.feishu.cn/space/api/box/stream/download/asynccode/?code=NzdjZTdjNTM0NjdhZWI1OWQzNDg5YzYzOTkzMmMxMzZfTjROMmVoc1NuNnpnT3hhVlQwQnAxSVh1eEZCSHZaTm9fVG9rZW46WFBhc2JqVXdjb2xnWFV4TllQY2NQWDZsbmFlXzE3NjgwNDQ1NTg6MTc2ODA0ODE1OF9WNA)

**结论**：✅ 通过（趋境：93.3；官方：93.1）

---

### 2.3 超长上下文测试

**测试目的**：验证趋境方案 DeepSeek-V3.2 支持超长上下文（128K）。

**测试命令**：
```bash
evalscope perf --parallel 1 --number 1 \
  --model DeepSeek-V3.2 \
  --tokenizer-path /data/models/DeepSeek-V3.2 \
  --url http://127.0.0.1:8000/v1/completions \
  --api openai --dataset random \
  --max-tokens 1000 --min-tokens 1000 \
  --prefix-length 0 --min-prompt-length 128000 --max-prompt-length 128000 \
  --extra-args '{"ignore_eos": true}'
```

**预期结果**：支持 128K 超长上下文

**测试结果**：

![超长上下文测试结果](https://swcil84qspu.feishu.cn/space/api/box/stream/download/asynccode/?code=ZTYwOWQ2MTk4MWFiZTQzMDRjNGE1ZWM3MTUxOTU1OTNfbTFIeXc1Z2xGVUJVRmx2NzlPQVlEejBTUEV3QkdETzJfVG9rZW46RUVxRmJhcXhTb1F6S2x4QXBkcGNMT2VDbkZlXzE3NjgwNDQ1NTg6MTc2ODA0ODE1OF9WNA)

**结论**：✅ 通过

---

## 3. 测试结论

三台服务器的整体 TPM 为 **1,366,560**（22,776 × 60），TPOT、TTFT、精度均符合要求。

结合上述测试结果，**测试通过**。当前性能仍在持续优化中。
