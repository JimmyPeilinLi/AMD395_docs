#!/usr/bin/env python3
"""
根据 PDF 批注自动修改 Markdown 文件

支持的批注指令：
- "删除" / "delete" / "remove": 删除高亮标注的内容
- "改为:xxx" / "修改为:xxx" / "replace:xxx": 将高亮内容替换为 xxx
- "补充:xxx" / "add:xxx": 在高亮位置后补充 xxx
- "移动到第X节" / "move to": 移动内容（需要手动处理）
- 其他文本: 作为高亮内容的注释，不修改文件
"""

import argparse
import json
import re
from pathlib import Path
from typing import Literal


def load_markdown(md_path: str | Path) -> list[str]:
    """加载 Markdown 文件并按行分割。"""
    return Path(md_path).read_text(encoding="utf-8").splitlines()


def normalize_text(text: str) -> str:
    """标准化文本用于匹配。"""
    # 移除多余空格和换行
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def find_annotation_location(
    lines: list[str],
    search_text: str,
    page_num: int = None
) -> tuple[int, int] | None:
    """
    在 Markdown 行中查找标注文本的位置。

    Returns:
        (start_line, end_line) 或 None
    """
    search_normalized = normalize_text(search_text)
    best_match = None
    best_score = 0

    # 拆分为关键词进行模糊匹配
    search_words = set(search_normalized.split())
    if not search_words:
        return None

    for line_num, line in enumerate(lines):
        line_normalized = normalize_text(line)

        # 精确匹配
        if search_normalized in line_normalized:
            return (line_num, line_num)

        # 关键词匹配
        line_words = set(line_normalized.split())
        overlap = len(search_words & line_words)
        if overlap > best_score and overlap >= len(search_words) * 0.5:
            best_score = overlap
            best_match = (line_num, line_num)

    return best_match


def parse_annotation_command(content: str) -> tuple[Literal["delete", "replace", "add", "comment"], str] | None:
    """
    解析批注命令。

    Returns:
        (命令类型, 参数) 或 None
    """
    if not content:
        return None

    content_lower = content.strip().lower()

    # 删除命令
    if content_lower in ["删除", "delete", "remove", "del"]:
        return ("delete", "")

    # 替换命令: "改为:xxx", "修改为:xxx", "replace:xxx"
    for prefix in ["改为:", "修改为:", "replace:", "change to:", "修改:" ]:
        if content_lower.startswith(prefix):
            new_text = content[len(prefix):].strip()
            return ("replace", new_text)

    # 补充命令: "补充:xxx", "add:xxx", "+ xxx"
    for prefix in ["补充:", "add:", "+ "]:
        if content_lower.startswith(prefix):
            new_text = content[len(prefix):].strip()
            return ("add", new_text)

    # 检查是否包含指令关键词
    if any(kw in content_lower for kw in ["删除", "delete", "remove"]):
        return ("delete", "")

    return ("comment", content)


def apply_annotation(
    lines: list[str],
    annotation: dict,
    dry_run: bool = False
) -> tuple[list[str], str]:
    """
    应用单条批注到 Markdown。

    Returns:
        (修改后的行列表, 修改描述)
    """
    # 获取被标注的文本
    annotated_text = annotation.get("text", "")
    if not annotated_text:
        return lines, f"跳过（无标注文本）: {annotation.get('content', '')[:50]}"

    # 解析批注命令
    content = annotation.get("content", "")
    command_info = parse_annotation_command(content)

    if not command_info:
        return lines, f"跳过（无法解析命令）: {content[:50]}"

    command, param = command_info

    # 查找位置
    location = find_annotation_location(lines, annotated_text, annotation.get("page"))

    if location is None:
        return lines, f"跳过（未找到位置）: {annotated_text[:50]}"

    start_line, end_line = location

    # 应用修改
    result_lines = lines.copy()
    description = ""

    if command == "delete":
        # 删除标注的行
        for i in range(start_line, end_line + 1):
            result_lines[start_line] = ""  # 标记为空，稍后清理
        description = f"第 {start_line + 1} 行: 删除内容"

    elif command == "replace":
        # 替换标注的行
        original = result_lines[start_line]
        # 尝试精确替换
        if annotated_text.lower() in original.lower():
            # 找到原始大小写匹配
            pattern = re.compile(re.escape(annotated_text), re.IGNORECASE)
            match = pattern.search(original)
            if match:
                new_line = original[:match.start()] + param + original[match.end():]
                result_lines[start_line] = new_line
                description = f"第 {start_line + 1} 行: 替换为 '{param}'"
            else:
                result_lines[start_line] = param
                description = f"第 {start_line + 1} 行: 整行替换为 '{param}'"
        else:
            result_lines[start_line] = param
            description = f"第 {start_line + 1} 行: 替换为 '{param}'"

    elif command == "add":
        # 在标注位置后补充内容
        original = result_lines[start_line]
        result_lines[start_line] = original + " " + param
        description = f"第 {start_line + 1} 行: 补充 '{param}'"

    elif command == "comment":
        # 仅添加注释，不修改内容
        return lines, f"注释（第 {start_line + 1} 行）: {content[:50]}"

    # 清理空行
    result_lines = [l for l in result_lines if l != ""]

    return result_lines, description


def apply_all_annotations(
    md_path: str | Path,
    annotations: list[dict],
    dry_run: bool = False,
    output_path: str | Path = None
) -> tuple[bool, list[str]]:
    """
    应用所有批注到 Markdown 文件。

    Returns:
        (是否有修改, 修改描述列表)
    """
    lines = load_markdown(md_path)
    current_lines = lines
    changes = []
    has_changes = False

    for i, annot in enumerate(annotations, 1):
        annot_type = annot.get("type", "")
        content = annot.get("content", "")

        # 跳过高亮（如果没有批注内容）
        if annot_type == "Highlight" and not content:
            changes.append(f"[{i}] 跳过（无批注内容）")
            continue

        # 应用批注
        new_lines, description = apply_annotation(current_lines, annot, dry_run)

        if new_lines != current_lines:
            has_changes = True
            current_lines = new_lines

        changes.append(f"[{i}] 第 {annot.get('page', '?')} 页 - {annot_type}: {description}")

    # 保存修改
    if has_changes and not dry_run and output_path:
        output = Path(output_path)
        output.write_text("\n".join(current_lines) + "\n", encoding="utf-8")
        changes.append(f"\n✓ 文件已保存: {output_path}")
    elif dry_run and has_changes:
        changes.append("\n[预览模式] 未实际修改文件")

    return has_changes, changes


def main():
    parser = argparse.ArgumentParser(
        description="根据 PDF 批注自动修改 Markdown 文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
批注指令格式:
  删除: "删除" / "delete" / "remove"
  替换: "改为:新内容" / "replace:新内容"
  补充: "补充:新内容" / "add:新内容"
  其他: 作为注释，不修改

示例:
  # 预览修改（不实际修改文件）
  %(prog)s annotations.json report.md --dry-run

  # 应用修改并覆盖原文件
  %(prog)s annotations.json report.md --apply

  # 应用修改并保存到新文件
  %(prog)s annotations.json report.md --apply -o report-new.md
        """,
    )

    parser.add_argument("annotations", help="批注 JSON 文件")
    parser.add_argument("markdown", help="Markdown 源文件")
    parser.add_argument(
        "--apply", "-a",
        action="store_true",
        help="应用修改到文件"
    )
    parser.add_argument(
        "--output", "-o",
        help="输出文件路径（默认覆盖原文件）"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="预览模式，显示将要进行的修改但不实际修改"
    )

    args = parser.parse_args()

    if not args.apply and not args.dry_run:
        print("错误: 请指定 --apply 应用修改，或使用 --dry-run 预览")
        return 1

    # 加载批注
    annot_path = Path(args.annotations)
    if not annot_path.exists():
        print(f"错误: 批注文件不存在: {args.annotations}")
        return 1

    annotations = json.loads(annot_path.read_text(encoding="utf-8"))

    # 加载 Markdown
    md_path = Path(args.markdown)
    if not md_path.exists():
        print(f"错误: Markdown 文件不存在: {args.markdown}")
        return 1

    output_path = args.output or md_path

    # 应用批注
    has_changes, changes = apply_all_annotations(
        md_path,
        annotations,
        dry_run=args.dry_run,
        output_path=None if args.dry_run else output_path
    )

    # 输出结果
    print("\n" + "=" * 60)
    print("批注处理结果:\n")
    for change in changes:
        print(change)

    if not has_changes:
        print("\n没有需要应用的修改")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
