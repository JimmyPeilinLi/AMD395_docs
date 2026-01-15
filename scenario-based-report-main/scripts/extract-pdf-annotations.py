#!/usr/bin/env python3
"""
PDF 批注提取工具

从 PDF 文件中提取高亮、批注等内容，支持：
- 高亮文本 (Highlight)
- 下划线 (Underline)
- 删除线 (Strike-through)
- 文本批注 (Text comments/notes)

使用 PyMuPDF (fitz) 库
"""

import argparse
import json
from pathlib import Path
from typing import Any

try:
    import fitz  # PyMuPDF
except ImportError:
    print("错误: 需要安装 PyMuPDF 库")
    print("安装命令: pip install pymupdf")
    raise SystemExit(1)


# PDF 批注类型映射
ANNOTATION_TYPES = {
    0: "Text",
    1: "Link",
    2: "FreeText",
    3: "Line",
    4: "Square",
    5: "Circle",
    6: "Polygon",
    7: "PolyLine",
    8: "Highlight",
    9: "Underline",
    10: "Squiggly",
    11: "StrikeOut",
    12: "Stamp",
    13: "Caret",
    14: "Ink",
    15: "Popup",
    16: "FileAttachment",
    17: "Sound",
}


def get_highlighted_words(page: fitz.Page, annot: fitz.Annot) -> list[str]:
    """
    获取高亮标注所覆盖的单词。

    PyMuPDF 的高亮注释使用 vertices 定义多边形区域，
    需要找到这些区域内的所有单词。
    """
    words = page.get_text("words")  # 返回 [(x0, y0, x1, y1, word, block_no, line_no, word_no), ...]
    highlighted_words = []

    if annot.vertices:
        # 高亮可能由多个区域组成（多行）
        vertices = annot.vertices
        quads = len(vertices) // 4  # 每个 quad 由 4 个点组成

        for i in range(quads):
            # 获取当前 quad 的 4 个顶点
            quad = vertices[i * 4 : (i + 1) * 4]

            # 计算 quad 的边界矩形
            x_coords = [p[0] for p in quad]
            y_coords = [p[1] for p in quad]
            x0 = min(x_coords)
            y0 = min(y_coords)
            x1 = max(x_coords)
            y1 = max(y_coords)

            # 查找在这个矩形内的单词
            for w in words:
                # w: (x0, y0, x1, y1, word, block_no, line_no, word_no)
                word_rect = fitz.Rect(w[0], w[1], w[2], w[3])
                annot_rect = fitz.Rect(x0, y0, x1, y1)

                # 检查单词是否在高亮区域内（有交集）
                if word_rect.intersects(annot_rect):
                    highlighted_words.append(w[4])
    else:
        # 如果没有 vertices，使用 rect（适用于简单的矩形注释）
        rect = annot.rect
        for w in words:
            word_rect = fitz.Rect(w[0], w[1], w[2], w[3])
            if rect.contains(word_rect):
                highlighted_words.append(w[4])

    return highlighted_words


def extract_annotation_text(page: fitz.Page, annot: fitz.Annot) -> str:
    """从注释中提取相关文本内容。"""
    annot_type = annot.type[0]

    # 文本注释类型
    if annot_type == 0:  # Text / Comment
        content = annot.info.get("content", "")
        return content if content else "[空文本注释]"

    # 高亮、下划线、删除线等文本标记类型
    if annot_type in [8, 9, 10, 11]:  # Highlight, Underline, Squiggly, StrikeOut
        words = get_highlighted_words(page, annot)
        return " ".join(words) if words else "[无法提取文本]"

    # 其他类型，尝试提取内容
    content = annot.info.get("content", "")
    if content:
        return content

    return f"[{ANNOTATION_TYPES.get(annot_type, 'Unknown')} 标注]"


def extract_annotations(pdf_path: str | Path) -> list[dict[str, Any]]:
    """
    从 PDF 文件中提取所有批注。

    Args:
        pdf_path: PDF 文件路径

    Returns:
        批注列表，每个批注是一个字典，包含:
        - page: 页码（从 0 开始）
        - type: 批注类型
        - content: 批注内容（对于文本注释）
        - text: 被标注的文本（对于高亮等）
        - author: 作者（如果有的话）
        - created: 创建时间
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"文件不存在: {pdf_path}")

    doc = fitz.open(str(pdf_path))
    annotations = []

    for page_num, page in enumerate(doc):
        for annot in page.annots():
            annot_type = annot.type[0]
            type_name = ANNOTATION_TYPES.get(annot_type, f"Unknown({annot_type})")

            # 获取注释信息
            info = annot.info

            annotation = {
                "page": page_num + 1,  # 页码从 1 开始显示
                "page_zero_indexed": page_num,
                "type": type_name,
                "type_code": annot_type,
            }

            # 文本注释的内容
            if info.get("content"):
                annotation["content"] = info["content"]

            # 提取被标注的文本（对于高亮等）
            extracted_text = extract_annotation_text(page, annot)
            if extracted_text:
                annotation["text"] = extracted_text

            # 作者信息
            if info.get("title"):
                annotation["author"] = info["title"]

            # 创建时间
            if info.get("creationDate"):
                annotation["created"] = info["creationDate"]

            # 修改时间
            if info.get("modDate"):
                annotation["modified"] = info["modDate"]

            # 颜色信息（对于高亮）
            if hasattr(annot, "colors") and annot.colors:
                annotation["color"] = annot.colors

            annotations.append(annotation)

    doc.close()
    return annotations


def format_annotations(annotations: list[dict[str, Any]], output_format: str = "text") -> str:
    """格式化批注输出。"""
    if output_format == "json":
        return json.dumps(annotations, ensure_ascii=False, indent=2)

    # 文本格式输出
    lines = []
    lines.append(f"共找到 {len(annotations)} 条批注\n")
    lines.append("=" * 60)

    for i, annot in enumerate(annotations, 1):
        lines.append(f"\n[批注 {i}] 第 {annot['page']} 页")
        lines.append(f"类型: {annot['type']}")

        if "text" in annot:
            lines.append(f"标注文本: {annot['text']}")

        if "content" in annot:
            lines.append(f"批注内容: {annot['content']}")

        if "author" in annot:
            lines.append(f"作者: {annot['author']}")

        if "created" in annot:
            lines.append(f"创建时间: {annot['created']}")

        lines.append("-" * 40)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="从 PDF 文件中提取高亮、批注等内容",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 提取批注并以文本格式显示
  %(prog)s document.pdf

  # 提取批注并保存为 JSON
  %(prog)s document.pdf --format json --output annotations.json

  # 只提取高亮
  %(prog)s document.pdf --type Highlight

  # 提取第 5-10 页的批注
  %(prog)s document.pdf --pages 5-10
        """,
    )

    parser.add_argument("pdf_file", help="PDF 文件路径")
    parser.add_argument(
        "--format", "-f",
        choices=["text", "json"],
        default="text",
        help="输出格式 (默认: text)"
    )
    parser.add_argument("--output", "-o", help="输出文件路径（默认输出到 stdout）")
    parser.add_argument(
        "--type", "-t",
        help="只提取指定类型的批注 (如: Highlight, Underline, Text)"
    )
    parser.add_argument(
        "--pages", "-p",
        help="指定页码范围 (如: 1-5, 10, 15-20)"
    )

    args = parser.parse_args()

    # 解析页码范围
    page_filter = None
    if args.pages:
        page_filter = set()
        for part in args.pages.split(","):
            part = part.strip()
            if "-" in part:
                start, end = part.split("-")
                page_filter.update(range(int(start), int(end) + 1))
            else:
                page_filter.add(int(part))

    # 提取批注
    try:
        annotations = extract_annotations(args.pdf_file)
    except Exception as e:
        print(f"错误: {e}")
        return 1

    # 过滤类型
    if args.type:
        annotations = [a for a in annotations if a["type"] == args.type]

    # 过滤页码
    if page_filter:
        annotations = [a for a in annotations if a["page"] in page_filter]

    # 格式化输出
    output = format_annotations(annotations, args.format)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"批注已保存到: {args.output}")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
