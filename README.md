# 通用文档爬虫 (Doc Crawler)

一个简单易用的文档爬虫工具，用于抓取各种项目文档并转换为 Markdown 格式，方便喂给 AI 进行分析和学习。

## ✨ 功能特性

- ✅ **静态页面爬取** - 基于 requests + BeautifulSoup
- ✅ **自动转换 Markdown** - HTML 自动转为干净的 Markdown 格式
- ✅ **配置化管理** - 通过 YAML 文件配置站点，无需修改代码
- ✅ **智能链接提取** - 支持从侧边栏、导航栏提取文档链接
- ✅ **编码自动处理** - 自动识别和处理 UTF-8 编码
- ✅ **请求频率控制** - 内置延时，避免对服务器造成压力
- 🔄 **动态页面支持** - Selenium 驱动（可选）

## 📁 项目结构

```
project-doc-crawler/
├── src/
│   └── crawler.py         # 爬虫核心代码
├── config/
│   └── sites.yaml         # 站点配置文件
├── data/                  # 爬取的数据存放目录
├── venv/                  # Python 虚拟环境
├── main.py                # 主入口脚本
├── requirements.txt       # Python 依赖
├── .gitignore             # Git 忽略文件
└── README.md              # 项目说明
```

## 🚀 快速开始

### 1. 激活虚拟环境

```bash
cd project-doc-crawler
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows
```

### 2. 安装依赖（如未安装）

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. 配置站点

编辑 `config/sites.yaml`，添加要爬取的站点。详见下方「配置说明」。

### 4. 运行爬虫

```bash
# 爬取指定站点
python main.py opencode

# 列出所有已配置站点
python main.py --list

# 使用自定义配置文件
python main.py --config my_config.yaml opencode

# 指定输出目录
python main.py --output my_docs opencode
```

## ⚙️ 配置说明

### 站点配置格式

```yaml
sites:
  站点ID:
    name: "站点显示名称"
    base_url: "https://example.com"
    doc_url: "https://example.com/docs"
    selectors:
      content: ".content"           # 正文内容选择器
      title: "h1"                   # 标题选择器
    sidebar_selector: ".sidebar"    # 侧边栏选择器
    url_pattern: "/docs"            # URL 匹配模式（正则）
    prefix_to_remove: "/docs"       # 文件名中移除的前缀
    output_dir: "data/example"      # 输出目录
```

### 配置字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | ✅ | 站点显示名称 |
| `base_url` | ✅ | 站点根 URL |
| `doc_url` | ❌ | 文档入口 URL（默认使用 base_url） |
| `selectors.content` | ✅ | 正文内容的 CSS 选择器 |
| `selectors.title` | ✅ | 页面标题的 CSS 选择器 |
| `sidebar_selector` | ❌ | 侧边栏的 CSS 选择器 |
| `url_pattern` | ❌ | URL 匹配的正则表达式 |
| `prefix_to_remove` | ❌ | 文件名中需要移除的 URL 前缀 |
| `output_dir` | ❌ | 输出目录（默认: data/站点ID） |

### 全局设置

```yaml
settings:
  delay: 1.0          # 请求间隔（秒）
  timeout: 30         # 请求超时（秒）
  user_agent: "..."   # User-Agent 字符串
  max_depth: 3        # 爬取深度限制
```

## 📝 配置示例

### OpenCode 文档（Astro/Starlight 框架）

```yaml
opencode:
  name: "OpenCode 中文文档"
  base_url: "https://opencode.ai"
  doc_url: "https://opencode.ai/docs/zh-cn/"
  selectors:
    content: ".sl-markdown-content"
    title: "h1"
  sidebar_selector: "#starlight__sidebar"
  url_pattern: "/docs/zh-cn"
  prefix_to_remove: "/docs/zh-cn"
  output_dir: "data/opencode"
```

### Vue.js 文档（VitePress 框架）

```yaml
vue:
  name: "Vue.js 中文文档"
  base_url: "https://cn.vuejs.org"
  doc_url: "https://cn.vuejs.org/guide/introduction.html"
  selectors:
    content: ".vp-doc"
    title: "h1"
  sidebar_selector: ".VPSidebar"
  url_pattern: "/(guide|api|examples|style-guide|about)"
  prefix_to_remove: ""
  output_dir: "data/vue"
```

### React 文档

```yaml
react:
  name: "React 中文文档"
  base_url: "https://zh-hans.react.dev"
  doc_url: "https://zh-hans.react.dev/learn"
  selectors:
    content: "article"
    title: "h1"
  sidebar_selector: "nav"
  url_pattern: "/(learn|reference)"
  prefix_to_remove: ""
  output_dir: "data/react"
```

## 🔍 如何找到正确的选择器

1. **打开目标网站**，进入文档页面
2. **打开开发者工具**（F12 或右键 → 检查）
3. **查找正文内容**：
   - 点击左上角的「选择元素」工具
   - 点击文档正文区域
   - 查看元素的 class 或 id
4. **查找侧边栏**：
   - 点击侧边栏区域
   - 查看导航元素的选择器
5. **测试选择器**：
   - 在 Console 中输入 `document.querySelector('.your-selector')`

### 常见文档框架的选择器

| 框架 | 正文选择器 | 侧边栏选择器 |
|------|-----------|-------------|
| VitePress | `.vp-doc` | `.VPSidebar` |
| Astro/Starlight | `.sl-markdown-content` | `#starlight__sidebar` |
| Docusaurus | `.markdown` | `.menu` |
| GitBook | `.markdown-section` | `.summary` |
| Docsify | `.markdown-section` | `.sidebar` |
| VuePress | `.theme-default-content` | `.sidebar-links` |

## 🛠️ 命令行参数

```bash
python main.py [站点名称] [选项]
```

| 参数 | 说明 |
|------|------|
| `site` | 要爬取的站点名称 |
| `--config FILE` | 指定配置文件（默认: config/sites.yaml） |
| `--type TYPE` | 爬取类型: static/dynamic（默认: static） |
| `--list` | 列出所有已配置的站点 |
| `--output DIR` | 指定输出目录 |

### 示例

```bash
# 列出所有配置的站点
python main.py --list

# 爬取 opencode 文档
python main.py opencode

# 使用动态爬虫
python main.py vue --type dynamic

# 指定输出目录
python main.py --output my_docs opencode
```

## 📦 输出格式

爬取的文档保存为 Markdown 文件，格式如下：

```
data/
└── opencode/
    ├── index.md          # 首页/简介
    ├── config.md         # 配置文档
    ├── agents.md         # 代理文档
    ├── cli.md            # CLI 文档
    └── ...
```

每个文件包含：
- 标题（从页面 h1 提取）
- 正文内容（转换为 Markdown）

## ⚠️ 注意事项

1. **遵守 robots.txt** - 请尊重网站的爬虫规则
2. **控制请求频率** - 默认延时 1 秒，可根据需要调整
3. **个人学习使用** - 仅用于个人学习和研究目的
4. **版权问题** - 爬取的内容请遵守原网站的版权协议

## 🔧 常见问题

### Q: 中文显示乱码怎么办？

A: 爬虫已自动处理 UTF-8 编码。如果仍有问题，检查终端是否支持 UTF-8。

### Q: 如何爬取需要登录的网站？

A: 目前不支持。可以考虑添加 Cookie 支持或使用 Selenium。

### Q: 爬取速度太慢怎么办？

A: 修改 `config/sites.yaml` 中的 `delay` 值（不建议设为 0）。

### Q: 如何爬取 JavaScript 渲染的页面？

A: 使用 `--type dynamic` 参数，需要安装 Selenium 和 ChromeDriver。

## 📄 License

MIT

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
