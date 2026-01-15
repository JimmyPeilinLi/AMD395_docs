const fs = require('fs');
const path = require('path');

// 读取 logo base64
const logoPath = path.join(__dirname, '..', 'scripts', 'logo', 'logo-base64.txt');
let logoBase64 = '';
try {
  logoBase64 = fs.readFileSync(logoPath, 'utf8').trim();
} catch (e) {
  console.warn('Logo not found, using text fallback');
}

// 无衬线字体（适合屏幕阅读，包含中文字体）
const sansSerifFont = "'Noto Sans CJK SC', 'PingFang SC', 'Microsoft YaHei', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif";

// 构建页眉模板
const headerTemplate = logoBase64
  ? `<div style="width:100%;font-size:9px;padding:0 20mm;display:flex;justify-content:space-between;align-items:center;color:#6b7280;border-bottom:1px solid #ede9fe;padding-bottom:5px;font-family:${sansSerifFont};">
      <img src="data:image/png;base64,${logoBase64}" height="18" style="opacity:0.9;"/>
      <span style="color:#9ca3af;">技术方案</span>
    </div>`
  : `<div style="width:100%;font-size:9px;padding:0 20mm;display:flex;justify-content:space-between;color:#6b7280;border-bottom:1px solid #ede9fe;padding-bottom:5px;font-family:${sansSerifFont};">
      <span style="font-weight:bold;color:#6c20ef;">趋境科技</span>
      <span>技术方案</span>
    </div>`;

const footerTemplate = `<div style="width:100%;font-size:9px;padding:0 20mm;display:flex;justify-content:center;color:#9ca3af;font-family:${sansSerifFont};">
  <span>第 <span class="pageNumber"></span> 页 / 共 <span class="totalPages"></span> 页</span>
</div>`;

module.exports = {
  stylesheet: path.join(__dirname, 'style.css'),

  // CSS 选项 - 代码块样式
  css: `
    pre, pre code {
      font-family: "SF Mono", "Monaco", "Consolas", "Courier New", monospace !important;
    }
  `,

  pdf_options: {
    format: 'A4',
    margin: {
      top: '30mm',
      bottom: '20mm',
      left: '20mm',
      right: '20mm'
    },
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: headerTemplate,
    footerTemplate: footerTemplate
  },

  launch_options: {
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  }
};
