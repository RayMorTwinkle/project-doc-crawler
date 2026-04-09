---
name: "doc-crawler"
description: "自动分析文档网站结构并爬取内容转换为Markdown。Invoke when user wants to crawl documentation from a website, extract docs to Markdown, or needs to analyze a documentation site's structure."
---

# Doc Crawler - 智能文档爬虫

自动分析文档网站结构，智能推荐选择器配置，爬取文档并转换为Markdown格式。

## 核心能力

1. **网站结构分析** - 自动识别文档框架类型（VitePress/Docusaurus/Astro等）
2. **智能选择器推荐** - 根据框架类型推荐最优CSS选择器
3. **自动配置管理** - 读取/修改 `sites.yaml` 配置文件
4. **执行爬取任务** - 调用Python脚本执行爬取
5. **自适应调整** - 根据爬取结果自动调整配置和脚本

## 执行流程

```
用户请求爬取文档
    ↓
1. 分析网站结构（调用 analyze_site.py）
    ↓
2. 识别文档框架，推荐选择器
    ↓
3. 创建/修改 sites.yaml 配置
    ↓
4. 执行爬取（调用 smart_crawl.py）
    ↓
5. 检查结果，如有问题自适应调整
    ↓
6. 输出最终结果
```

## 常见文档框架识别特征

| 框架 | HTML特征 | 推荐选择器 |
|------|---------|-----------|
| **VitePress** | `.VPDoc`, `.vp-doc`, `.VPContent` | content: `.vp-doc`, sidebar: `.VPSidebar` |
| **Docusaurus** | `__docusaurus` id, `.theme-doc-markdown` | content: `.theme-doc-markdown`, sidebar: `.theme-doc-sidebar-menu` |
| **Astro/Starlight** | `.sl-markdown-content`, `.sl-container` | content: `.sl-markdown-content`, sidebar: `#starlight__sidebar` |
| **GitBook** | `.book`, `.markdown-section` | content: `.markdown-section`, sidebar: `.summary` |
| **Docsify** | `#app`, `.markdown-section` | content: `.markdown-section`, sidebar: `.sidebar` |
| **VuePress** | `.theme-default-content`, `.sidebar` | content: `.theme-default-content`, sidebar: `.sidebar-links` |
| **ReadTheDocs** | `.wy-nav-content`, `readthedocs` | content: `[role="main"]`, sidebar: `.wy-nav-side` |
| **MDN** | `mdn` class, `article` | content: `article`, sidebar: `.sidebar` |
| **Nuxt/Docus** | `.docus-content`, `.docus-sidebar` | content: `.docus-content`, sidebar: `.docus-sidebar` |
| **Mintlify** | `.prose`, `.sidebar` | content: `.prose`, sidebar: `.sidebar` |

## 文件结构

```
.trae/skills/doc-crawler/
├── SKILL.md                    # 本文件 - Skill核心说明
├── examples/                   # 示例输入输出
│   ├── input_01.md            # 示例：爬取VitePress站点
│   ├── output_01.md           # 示例：爬取结果
│   └── edge_case.md           # 边界情况处理
├── scripts/                    # 辅助脚本
│   ├── analyze_site.py        # 网站结构分析
│   ├── smart_crawl.py         # 智能爬取（带自适应）
│   └── validate_config.py     # 配置验证
└── resources/                  # 资源文件
    └── framework_patterns.json # 框架识别模式库
```

## 使用方式

### 方式1：用户直接请求

用户说：
- "帮我爬取 https://vuejs.org 的文档"
- "把 https://docs.example.com 转成Markdown"
- "分析这个文档网站的结构"

### 方式2：带特定需求

用户说：
- "爬取 https://docs.astro.build，输出到 astro_docs 目录"
- "用动态模式爬取这个JS渲染的文档站"

## 执行步骤详解

### Step 1: 分析网站结构

使用 `scripts/analyze_site.py` 分析目标网站：

```bash
python .trae/skills/doc-crawler/scripts/analyze_site.py <url>
```

输出信息包括：
- 检测到的文档框架类型
- 推荐的内容选择器
- 推荐的侧边栏选择器
- URL匹配模式建议
- 页面编码信息

### Step 2: 创建配置

根据分析结果，在 `config/sites.yaml` 中添加配置：

```yaml
sites:
  <site_id>:
    name: "站点名称"
    base_url: "https://example.com"
    doc_url: "https://example.com/docs"
    selectors:
      content: "<推荐的内容选择器>"
      title: "h1"
    sidebar_selector: "<推荐的侧边栏选择器>"
    url_pattern: "<URL匹配模式>"
    prefix_to_remove: "<需要移除的前缀>"
    output_dir: "data/<site_id>"
```

### Step 3: 执行爬取

使用 `scripts/smart_crawl.py` 执行智能爬取：

```bash
python .trae/skills/doc-crawler/scripts/smart_crawl.py <site_id>
```

该脚本会：
- 自动重试失败的请求
- 检测内容是否为空，尝试备用选择器
- 记录爬取日志
- 生成爬取报告

### Step 4: 自适应调整

如果爬取失败或结果不理想：

1. **检查错误类型**
   - 选择器未找到 → 尝试其他常见选择器
   - 内容为空 → 检查页面是否需要JS渲染
   - 链接未找到 → 尝试从全页面提取链接

2. **自动修复策略**
   - 尝试备选选择器列表
   - 切换到动态爬取模式（如果需要JS）
   - 调整请求延迟和超时设置

3. **修改配置重试**
   - 更新 `sites.yaml` 中的选择器
   - 重新执行爬取

## 错误处理清单

| 错误 | 症状 | 解决方案 |
|------|------|---------|
| **ImportError** | 模块未找到 | 激活虚拟环境: `source venv/bin/activate` |
| **Timeout** | 请求超时 | 增加delay到2-3秒，检查网络连接 |
| **SelectorNotFound** | 选择器匹配不到元素 | 尝试备选选择器，检查页面结构 |
| **EmptyContent** | 提取的内容为空 | 页面可能需要JS渲染，切换到dynamic模式 |
| **NoLinksFound** | 未找到文档链接 | 尝试从全页面提取，或调整sidebar选择器 |
| **EncodingError** | 中文乱码 | 强制设置response.encoding = 'utf-8' |
| **PermissionError** | 无法写入文件 | 检查data目录权限，创建目录 |
| **SeleniumError** | ChromeDriver错误 | 安装ChromeDriver或使用static模式 |
| **TooManyRedirects** | 重定向过多 | 检查URL是否正确，添加headers |
| **SSLCertificateError** | SSL证书错误 | 添加verify=False（不推荐长期使用） |

## 自适应调整策略

### 场景1：内容选择器不匹配

```python
# 备选选择器列表（按优先级）
CONTENT_SELECTORS = [
    ".vp-doc",                    # VitePress
    ".sl-markdown-content",      # Astro/Starlight
    ".theme-doc-markdown",       # Docusaurus
    ".markdown-section",         # GitBook/Docsify
    ".theme-default-content",    # VuePress
    "article",                    # 通用
    "main",                       # 通用
    ".content",                   # 通用
    "[role='main']",             # ARIA
]
```

### 场景2：侧边栏选择器不匹配

```python
# 备选侧边栏选择器
SIDEBAR_SELECTORS = [
    ".VPSidebar",                 # VitePress
    "#starlight__sidebar",       # Astro/Starlight
    ".theme-doc-sidebar-menu",   # Docusaurus
    ".sidebar",                   # 通用
    ".menu",                      # 通用
    "nav",                        # 通用
    ".toc",                       # 目录
]
```

### 场景3：需要JS渲染

如果static模式获取不到内容：
1. 检查页面是否有 `window.__INITIAL_STATE__` 或类似JS数据
2. 检查内容是否在 `<script>` 标签中
3. 切换到 `dynamic` 模式使用Selenium

## 输出规范

爬取完成后，输出目录结构：

```
data/<site_id>/
├── index.md              # 首页
├── getting-started.md    # 入门文档
├── api/
│   ├── index.md
│   └── reference.md
└── _crawl_report.json    # 爬取报告（包含成功/失败统计）
```

每个Markdown文件格式：

```markdown
# 页面标题

[原始URL: https://example.com/docs/page]

正文内容...
```

## 最佳实践

1. **先分析后爬取** - 总是先运行analyze_site了解网站结构
2. **从小范围开始** - 先爬取几个页面测试配置是否正确
3. **尊重robots.txt** - 检查目标网站的爬虫规则
4. **控制请求频率** - 默认delay 1秒，避免对服务器造成压力
5. **处理编码问题** - 确保输出文件为UTF-8编码
6. **记录爬取日志** - 方便排查问题和重试

## 扩展能力

AI可以根据实际情况：

1. **修改现有脚本** - 根据特定网站调整爬取逻辑
2. **编写新脚本** - 针对特殊需求创建自定义爬取器
3. **优化配置** - 根据爬取结果迭代优化选择器
4. **批量处理** - 同时配置和爬取多个站点
5. **数据清洗** - 爬取后对Markdown进行清理和格式化
