---
name: tech-report
description: 生成基于场景的技术方案报告。当用户需要整理技术方案、撰写技术报告、对比方案优劣势、准备售前材料时使用。支持推理框架性能评估（TTFT、TPOT、并发、吞吐量）。
---

# 基于场景的技术方案报告生成器

## 概述

帮助技术 leader 高效生成技术方案报告，支持内部版（完整技术细节）和外部版（价值导向，脱敏）两种输出。

## 触发场景

- 用户说"整理技术方案"、"写技术报告"
- 用户说"对比方案"、"分析优劣势"
- 用户说"准备售前材料"、"给客户的方案"
- 用户提到推理框架性能测试、TTFT、TPOT 等指标

## 工作流程

### Step 1: 收集场景信息

询问并确认以下信息：

| 要素 | 问题 |
|------|------|
| 目标场景 | 这个方案解决什么问题？|
| 核心价值 | 方案的核心价值是什么？|
| 目标用户 | 方案面向谁？|
| 竞品方案 | 要对比的竞品是什么？|
| 输出类型 | 内部版/外部版/两者都要？|

### Step 2: 定义评估维度

根据场景选择评估维度，推理框架通用指标见 [INFERENCE-METRICS.md](INFERENCE-METRICS.md)

常用维度：
- 模型效果（准确率、质量）
- 推理性能（TTFT、TPOT、QPS、吞吐量）
- 资源效率（GPU利用率、显存占用）
- 成本效益（单位成本、ROI）

### Step 3: 整理测试数据

使用标准测试矩阵，见 [INFERENCE-METRICS.md](INFERENCE-METRICS.md) 中的测试矩阵模板

### Step 4: 生成报告

根据 [REPORT-TEMPLATE.md](REPORT-TEMPLATE.md) 生成报告：
- 内部版：完整技术细节
- 外部版：价值导向，脱敏处理

### Step 5: 输出分层处理

内外版本转化原则：

| 内部版 | 外部版 |
|--------|--------|
| 具体参数配置 | 隐藏 |
| 优化技巧细节 | 概述为"优化技术" |
| 完整测试数据 | 选择性展示 |
| 劣势分析 | 淡化或不提 |
| 技术语言 | 转为业务语言 |

### Step 6: 生成 PDF

使用 `./scripts/generate-pdf.sh` 生成 PDF 文件。

#### 命名规则

PDF 文件命名格式：`[硬件平台]-[模型名称]-技术方案-[版本标识]-[日期].pdf`

| 组成部分 | 说明 | 示例 |
|----------|------|------|
| 硬件平台 | 芯片型号或服务器类型 | `昇腾910B`、`H100`、`A100` |
| 模型名称 | 模型名称和规模 | `DeepSeek-R1-671B`、`Qwen2-72B` |
| 版本标识 | 内部版/外部版（外部版省略） | `内部版`、留空 |
| 日期 | YYYYMMDD 格式 | `20251231` |

#### 示例

```
# 内部版
昇腾910B-DeepSeek-R1-671B-技术方案-内部版-20251231.pdf

# 外部版
昇腾910B-DeepSeek-R1-671B-技术方案-20251231.pdf
```

#### 生成命令

```bash
# 查看命名格式示例
./scripts/generate-pdf.sh --list

# 生成并自动命名（{date} 会自动替换为当前日期）
./scripts/generate-pdf.sh --name "昇腾910B-DeepSeek-R1-671B-技术方案-内部版-{date}" \
    reports/项目目录/internal/README.md

# 功能报告命名示例
./scripts/generate-pdf.sh --name "KTransformers-CLI功能报告-{date}" \
    reports/ktransformers-cli/README.md

# 不指定名称（默认使用文件名）
./scripts/generate-pdf.sh reports/项目目录/README.md
```

## 价值主张模板

```
通过 [技术手段]，实现 [技术指标提升]，
使 [目标用户] 能够 [获得的收益]。
```

### Step 7: 处理 PDF 批注（可选）

当报告生成后，评审人员可以在 PDF 上添加批注，然后自动反馈到 Markdown 源文件。

#### 批注指令格式

在 PDF 中对文本添加高亮或批注时，使用以下格式：

| 操作 | 批注内容 | 示例 |
|------|----------|------|
| 删除 | `删除` / `delete` | 高亮文本后批注写"删除" |
| 替换 | `改为:新内容` / `replace:新内容` | 高亮文本后批注写"改为:正确内容" |
| 补充 | `补充:新内容` / `add:新内容` | 高亮位置后批注���"补充:说明文字" |
| 仅注释 | 任意文本 | 作为备注，不修改文件 |

#### 处理流程

```bash
# 1. 提取 PDF 批注为 JSON
./scripts/extract-pdf-annotations.py report.pdf --format json -o annotations.json

# 2. 预览将要进行的修改（不实际修改）
./scripts/apply-annotations-to-md.py annotations.json report.md --dry-run

# 3. 确认后应用修改
./scripts/apply-annotations-to-md.py annotations.json report.md --apply

# 4. 重新生成 PDF
./scripts/generate-pdf.sh reports/项目目录/README.md
```

#### 完整示例

```bash
# 一键处理批注并重新生成 PDF
PDF_FILE="report.pdf"
MD_FILE="reports/project/README.md"

# 提取批注
./scripts/extract-pdf-annotations.py "$PDF_FILE" -o /tmp/annotations.json

# 预览修改
./scripts/apply-annotations-to-md.py /tmp/annotations.json "$MD_FILE" -n

# 应用修改
./scripts/apply-annotations-to-md.py /tmp/annotations.json "$MD_FILE" --apply

# 重新生成 PDF
./scripts/generate-pdf.sh "$MD_FILE"
```

## 价值主张模板

```
通过 [技术手段]，实现 [技术指标提升]，
使 [目标用户] 能够 [获得的收益]。
```

## 快速开始

告诉我：
1. 你要整理什么方案？
2. 要对比的竞品是什么？
3. 需要内部版还是外部版？

我会引导你完成整个报告生成流程。
