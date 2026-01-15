#!/bin/bash
#
# 趋境科技 - 批量生成 PDF 脚本
# 用法: ./scripts/generate-pdf.sh [选项] [目录或文件]
#
# 选项:
#   --name, -n <name>  指定输出文件名（不含扩展名），支持 {date} 变量自动替换
#   --list, -l        列出常用的命名格式
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$PROJECT_ROOT/.templates/pdf-config.js"

# 颜色输出
GREEN='\033[0;32m'
PURPLE='\033[0;35m'
YELLOW='\033[1;33m'
NC='\033[0m'

OUTPUT_NAME=""
CURRENT_DATE="$(date +%Y%m%d)"  # 自动获取当前日期

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --name|-n)
            OUTPUT_NAME="$2"
            shift 2
            ;;
        --list|-l)
            echo "常用命名格式示例:"
            echo ""
            echo "  功能报告:"
            echo "    --name 'KTransformers-CLI功能报告-{date}'"
            echo ""
            echo "  技术方案（内部版）:"
            echo "    --name '昇腾910B-DeepSeek-R1-671B-技术方案-内部版-{date}'"
            echo ""
            echo "  技术方案（外部版）:"
            echo "    --name '昇腾910B-DeepSeek-R1-671B-技术方案-{date}'"
            echo ""
            echo "  说明: {date} 会自动替换为当前日期 (YYYYMMDD)"
            echo ""
            exit 0
            ;;
        *)
            break
            ;;
    esac
done

echo -e "${PURPLE}========================================${NC}"
echo -e "${PURPLE}    趋境科技 - PDF 生成工具${NC}"
echo -e "${PURPLE}========================================${NC}"
echo ""

# 检查依赖
if ! command -v npx &> /dev/null; then
    echo "错误: 未找到 npx，请安装 Node.js"
    exit 1
fi

# 生成单个 PDF 的函数
generate_pdf() {
    local md_file="$1"
    local pdf_file="${md_file%.md}.pdf"
    local dir="$(dirname "$md_file")"

    echo -e "${YELLOW}正在生成:${NC} $(basename "$md_file")"

    # 切换到文件所在目录执行（保证相对路径正确）
    (cd "$dir" && npx md-to-pdf "$(basename "$md_file")" --config-file "$CONFIG_FILE" 2>/dev/null)

    if [ -f "$pdf_file" ]; then
        echo -e "${GREEN}  ✓ 生成成功:${NC} $(basename "$pdf_file")"

        # 如果指定了输出名称，重命名文件
        if [ -n "$OUTPUT_NAME" ]; then
            # 替换 {date} 为实际日期
            local final_name="${OUTPUT_NAME//\{date\}/$CURRENT_DATE}.pdf"
            local final_path="$(dirname "$pdf_file")/$final_name"

            mv "$pdf_file" "$final_path"
            echo -e "${GREEN}  → 已重命名为:${NC} $final_name"
        fi

        return 0
    else
        echo -e "\033[0;31m  ✗ 生成失败${NC}"
        return 1
    fi
}

# 主逻辑
if [ $# -eq 0 ]; then
    echo "未指定文件，将处理 reports 目录下的所有 .md 文件..."
    echo ""
    find "$PROJECT_ROOT/reports" -name "*.md" -type f | while read -r file; do
        generate_pdf "$file"
        echo ""
    done
else
    for target in "$@"; do
        if [ -f "$target" ]; then
            generate_pdf "$target"
        elif [ -d "$target" ]; then
            echo "处理目录: $target"
            find "$target" -name "*.md" -type f | while read -r file; do
                generate_pdf "$file"
                echo ""
            done
        else
            echo "警告: $target 不存在"
        fi
    done
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}    生成完成！${NC}"
echo -e "${GREEN}========================================${NC}"
