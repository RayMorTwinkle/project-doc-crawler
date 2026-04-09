# 示例 01: 爬取 VitePress 文档站点

## 用户输入

```
帮我爬取 https://vitejs.dev/guide/ 的文档
```

## AI 执行流程

### Step 1: 分析网站结构

```bash
python .trae/skills/doc-crawler/scripts/analyze_site.py https://vitejs.dev/guide/
```

**分析结果:**
```json
{
  "url": "https://vitejs.dev/guide/",
  "base_url": "https://vitejs.dev",
  "framework": "VitePress",
  "confidence": 85,
  "content_selector": {
    "recommended": ".vp-doc",
    "content_length": 15420,
    "alternatives": ["main", "article"]
  },
  "sidebar_selector": {
    "recommended": ".VPSidebar",
    "link_count": 24,
    "alternatives": [".sidebar", "nav"]
  },
  "sidebar_links": {
    "found": true,
    "link_count": 24,
    "url_pattern": "/guide"
  }
}
```

### Step 2: 创建配置

在 `config/sites.yaml` 中添加:

```yaml
sites:
  vite:
    name: "Vite 官方文档"
    base_url: "https://vitejs.dev"
    doc_url: "https://vitejs.dev/guide/"
    selectors:
      content: ".vp-doc"
      title: "h1"
    sidebar_selector: ".VPSidebar"
    url_pattern: "/guide"
    prefix_to_remove: "/guide"
    output_dir: "data/vite"
```

### Step 3: 验证配置

```bash
python .trae/skills/doc-crawler/scripts/validate_config.py
```

**输出:**
```
📋 配置验证报告
============================================

已配置站点数: 2

站点列表:
  - opencode
  - vite

✅ 配置验证通过！
```

### Step 4: 执行爬取

```bash
python .trae/skills/doc-crawler/scripts/smart_crawl.py vite
```

**执行输出:**
```
🚀 开始智能爬取: vite
============================================================

📍 文档入口: https://vitejs.dev/guide/
🔍 测试内容选择器...
  ✓ 当前选择器有效: .vp-doc (15420 字符)
🔍 测试侧边栏选择器...
  ✓ 当前选择器有效: .VPSidebar (24 个链接)

📥 开始爬取文档...
------------------------------------------------------------
开始爬取: vite
起始URL: https://vitejs.dev/guide/
找到 24 个文档页面
[1/24] 正在爬取: https://vitejs.dev/guide/
  - 已保存: data/vite/index.md
[2/24] 正在爬取: https://vitejs.dev/guide/features.html
  - 已保存: data/vite/features.md
...
[24/24] 正在爬取: https://vitejs.dev/guide/migration.html
  - 已保存: data/vite/migration.md

爬取完成: vite
共爬取 24 个页面
保存位置: data/vite

📊 报告已保存: data/vite/_crawl_report.json

============================================================
📋 爬取摘要
============================================================
  成功: 24 页
  失败: 0 页
  空内容: 0 页
  调整次数: 0
  错误次数: 0

✅ 爬取完成!
```

### Step 5: 输出结果

```
data/vite/
├── _crawl_report.json
├── index.md
├── features.md
├── build.md
├── config.md
├── assets.md
├── env-and-mode.md
├── ssr.md
├── backend-integration.md
├── comparison.md
├── migration.md
└── ...
```

## 最终回复给用户

```
✅ 成功爬取 Vite 官方文档！

📊 统计信息:
   • 爬取页面: 24 个
   • 框架类型: VitePress
   • 保存位置: data/vite/

📁 输出文件:
   • index.md - 入门指南
   • features.md - 功能特性
   • config.md - 配置指南
   • ... 共 24 个文件

📝 使用方式:
   所有文档已转换为 Markdown 格式，可以直接用于:
   - AI 学习分析
   - 离线阅读
   - 文档搜索
```
