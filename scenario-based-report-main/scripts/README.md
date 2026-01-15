# 脚本工具说明

## PDF 批注处理工具

用于处理 PDF 报告中的批注，将修改意见自动应用到 Markdown 源文件。

### 工具列表

| 工具 | 功能 |
|------|------|
| `extract-pdf-annotations.py` | 从 PDF 提取批注（高亮、评论等）|
| `apply-annotations-to-md.py` | 根据批注自动修改 Markdown 文件 |
| `generate-pdf.sh` | 将 Markdown 编译为 PDF |

### 工作流程

```
┌─────────────────┐
│  生成报告 PDF    │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ PDF 上添加批注   │  ← 评审人员在 PDF 阅读器中批注
└────────┬────────┘
         │
         v
┌─────────────────┐
│ extract-pdf     │  提取批注为 JSON
│ -annotations.py │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ apply-annota-   │  预览/应用修改到 MD
│ tions-to-md.py  │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ generate-pdf.sh │  重新生成 PDF
└─────────────────┘
```

### 使用示例

```bash
# 1. 提取批注
./scripts/extract-pdf-annotations.py report.pdf -o annotations.json

# 2. 预览将要进行的修改
./scripts/apply-annotations-to-md.py annotations.json report.md --dry-run

# 3. 应用修改
./scripts/apply-annotations-to-md.py annotations.json report.md --apply

# 4. 重新生成 PDF
./scripts/generate-pdf.sh report.md
```

### 批注指令格式

| 操作 | PDF 批注内容 | 效果 |
|------|-------------|------|
| 删除 | `删除` | 删除高亮的文本 |
| 替换 | `改为:新文本` | 将高亮文本替换为新文本 |
| 补充 | `补充:新文本` | 在高亮位置后补充文本 |
| 仅备注 | 任意内容 | 不修改文件，仅作为备注 |

### 安装依赖

```bash
pip install pymupdf
```
