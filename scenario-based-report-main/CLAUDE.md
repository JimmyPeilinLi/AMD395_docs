# 项目说明

这是趋境科技的技术方案报告项目，用于生成基于场景的技术方案文档。

## 目录结构

```
reports/           # 报告目录，每个项目一个子目录
  ├── internal/    # 内部版（完整技术细节）
  └── external/    # 外部版（脱敏，面向客户）
scripts/           # 工具脚本
.templates/        # PDF 模板和样式
```

## 常用工具

### 1. PDF 批注提取

当用户提供带批注的 PDF 文件时，使用此工具提取批注内容：

```bash
# 提取 PDF 中的所有批注（高亮、评论等）
python scripts/extract-pdf-annotations.py <PDF文件路径>

# 输出为 JSON 格式
python scripts/extract-pdf-annotations.py <PDF文件路径> --format json
```

### 2. 批注应用到 Markdown

将提取的批注指令应用到 Markdown 源文件：

```bash
# 预览修改（不实际修改文件）
python scripts/apply-annotations-to-md.py annotations.json report.md --dry-run

# 应用修改
python scripts/apply-annotations-to-md.py annotations.json report.md --apply
```

**批注指令格式：**
| 操作 | PDF 批注内容 | 效果 |
|------|-------------|------|
| 删除 | `删除` 或 `delete` | 删除高亮的文本/章节 |
| 替换 | `改为:新文本` 或 `replace:新文本` | 替换高亮文本 |
| 补充 | `补充:新文本` 或 `add:新文本` | 在高亮位置后补充 |
| 仅备注 | 任意其他内容 | 不修改文件，仅作为备注供参考 |

### 3. 生成 PDF

```bash
# 生成 PDF（自动命名）
./scripts/generate-pdf.sh <Markdown文件路径>

# 指定输出文件名（{date} 自动替换为当前日期 YYYYMMDD）
./scripts/generate-pdf.sh --name '昇腾910B-多机多卡-工作计划-{date}' report.md

# 查看命名格式示例
./scripts/generate-pdf.sh --list
```

**PDF 命名规则：** `[硬件平台]-[模型/项目名称]-[文档类型]-[版本标识]-[日期].pdf`

示例：
- 内部版：`昇腾910B-DeepSeek-R1-671B-技术方案-内部版-20260109.pdf`
- 外部版：`昇腾910B-DeepSeek-R1-671B-技术方案-20260109.pdf`

## 常见工作流程

### 处理 PDF 批注并更新报告

当用户说"PDF 有批注"或"查看批注并修改"时：

1. **提取批注**：`python scripts/extract-pdf-annotations.py <PDF路径>`
2. **根据批注修改 Markdown**：编辑对应的 .md 文件
3. **更新章节编号**：如果删除了章节，需要重新编号
4. **重新生成 PDF**：`./scripts/generate-pdf.sh --name '<命名>' <MD路径>`

### 生成技术方案报告

使用 `/tech-report` 命令启动报告生成向导，会引导完成：
1. 场景信息收集
2. 评估维度定义
3. 测试数据整理
4. 报告生成（内部版/外部版）

## 注意事项

- **日期年份**：当前是 2026 年，创建或修改文档时注意使用正确的年份（2026），不要写成 2025
- 报告分内部版和外部版，外部版需要脱敏处理
- 修改 Markdown 后记得重新生成 PDF
