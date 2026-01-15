# PDF 生成模板使用说明

## 快速开始

### 方式一：命令行直接生成（推荐）

```bash
# 生成单个文件
./scripts/generate-pdf.sh reports/xxx/external/投标技术方案.md

# 批量生成某个目录下的所有 md 文件
./scripts/generate-pdf.sh reports/xxx/external/

# 生成所有报告
./scripts/generate-pdf.sh
```

### 方式二：直接使用 npx

```bash
npx md-to-pdf your-file.md --stylesheet .templates/style.css
```

---

## 添加 Logo

### 方法 1：在 Markdown 文件开头添加 Logo

在 md 文件开头添加：

```markdown
<div style="text-align: center; margin-bottom: 30px;">
  <img src="../../../.templates/logo.png" alt="趋境科技" height="60">
</div>

# 文档标题
```

### 方法 2：使用 Base64 编码的 Logo

1. 将 logo 图片转换为 base64：

```bash
base64 -i logo.png | tr -d '\n' > logo-base64.txt
```

2. 在 md 文件中使用：

```markdown
<div style="text-align: center; margin-bottom: 30px;">
  <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..." height="60">
</div>
```

### 方法 3：页眉中使用图片 Logo

修改 `scripts/generate-pdf.sh` 中的 headerTemplate，将 Logo base64 编码后嵌入：

```javascript
headerTemplate: `
  <div style="display:flex;align-items:center;padding:0 20mm;">
    <img src="data:image/png;base64,YOUR_BASE64_HERE" height="20">
    <span style="margin-left:10px;">技术方案</span>
  </div>
`
```

---

## 自定义样式

编辑 `.templates/style.css` 可以自定义：

- 字体和颜色
- 表格样式
- 标题样式
- 代码块样式
- 页面边距

### 常用颜色配置

```css
/* 主色调 - 趋境科技蓝 */
--primary-color: #2b6cb0;
--primary-dark: #1a365d;
--primary-light: #bee3f8;

/* 背景色 */
--bg-light: #f7fafc;
--bg-quote: #ebf8ff;
```

---

## 高级配置

### 使用配置文件

```bash
npx md-to-pdf your-file.md --config-file .templates/pdf-config.js
```

### 可配置项

| 配置项 | 说明 |
|--------|------|
| `stylesheet` | 自定义 CSS 文件路径 |
| `pdf_options.format` | 纸张大小（A4, Letter 等） |
| `pdf_options.margin` | 页面边距 |
| `pdf_options.headerTemplate` | 页眉 HTML 模板 |
| `pdf_options.footerTemplate` | 页脚 HTML 模板 |
| `pdf_options.displayHeaderFooter` | 是否显示页眉页脚 |

---

## 其他工具推荐

如果需要更复杂的排版，可以考虑：

1. **Typst** - 现代排版工具，语法简洁
   ```bash
   brew install typst
   ```

2. **Pandoc + LaTeX** - 功能最强大
   ```bash
   brew install pandoc
   brew install --cask mactex
   ```

3. **WeasyPrint** - Python 工具，支持 CSS Paged Media
   ```bash
   pip install weasyprint
   ```

---

## 文件结构

```
.templates/
├── README.md          # 本说明文档
├── style.css          # PDF 样式文件
├── pdf-config.js      # md-to-pdf 配置
└── logo.png           # 公司 Logo（请自行添加）

scripts/
└── generate-pdf.sh    # 批量生成脚本
```
