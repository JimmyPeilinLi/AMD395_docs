#!/bin/bash
#
# 趋境科技 - HTML 预览工具（用于调试样式）
# 用法: ./scripts/preview-html.sh <markdown文件>
#
# 生成 HTML 后可以在浏览器中打开，修改 CSS 后刷新即可看到效果
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
STYLE_FILE="$PROJECT_ROOT/.templates/style.css"

if [ $# -eq 0 ]; then
    echo "用法: $0 <markdown文件>"
    echo "示例: $0 reports/xxx/文档.md"
    exit 1
fi

MD_FILE="$1"
HTML_FILE="${MD_FILE%.md}.html"

echo "生成 HTML 预览: $MD_FILE"

# 使用 npx marked 生成 HTML（如果没有安装会自动安装）
CONTENT=$(npx marked "$MD_FILE" 2>/dev/null)

# 生成完整的 HTML 文件
cat > "$HTML_FILE" << EOF
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>预览 - $(basename "$MD_FILE")</title>
  <link rel="stylesheet" href="$STYLE_FILE">
  <style>
    /* 预览模式额外样式 */
    body {
      max-width: 210mm;
      margin: 20px auto;
      padding: 20mm;
      box-shadow: 0 0 20px rgba(0,0,0,0.1);
      background: white;
    }
    html {
      background: #f0f0f0;
    }
    /* 调试辅助：显示页面边界 */
    .page-guide {
      position: fixed;
      top: 10px;
      right: 10px;
      background: #7c3aed;
      color: white;
      padding: 10px 15px;
      border-radius: 5px;
      font-size: 12px;
      z-index: 1000;
    }
  </style>
</head>
<body>
  <div class="page-guide">
    预览模式 | <a href="#" onclick="location.reload()" style="color:white">刷新</a>
  </div>
  $CONTENT
</body>
</html>
EOF

echo "✓ HTML 已生成: $HTML_FILE"
echo ""
echo "调试方法:"
echo "  1. 在浏览器中打开 HTML 文件"
echo "  2. 编辑 .templates/style.css"
echo "  3. 刷新浏览器查看效果"
echo "  4. 满意后运行 generate-pdf.sh 生成 PDF"
echo ""

# 尝试自动打开（macOS）
if command -v open &> /dev/null; then
    echo "正在打开浏览器..."
    open "$HTML_FILE"
fi
