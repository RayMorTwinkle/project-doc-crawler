# 边界情况处理指南

## 情况 1: 选择器不匹配，AI 自动调整

### 场景
用户请求爬取一个自定义文档站点，初始选择器无法匹配。

### 用户输入
```
帮我爬取 https://example.com/docs 的文档
```

### AI 处理流程

#### Step 1: 初始分析
```bash
python .trae/skills/doc-crawler/scripts/analyze_site.py https://example.com/docs
```

**分析结果:**
```json
{
  "framework": "Unknown",
  "confidence": 0,
  "content_selector": {
    "recommended": "article",
    "content_length": 0
  },
  "sidebar_selector": {
    "recommended": ".sidebar",
    "link_count": 0
  }
}
```

#### Step 2: 创建初始配置

```yaml
sites:
  example:
    name: "Example Docs"
    base_url: "https://example.com"
    doc_url: "https://example.com/docs"
    selectors:
      content: "article"
      title: "h1"
    sidebar_selector: ".sidebar"
    url_pattern: "/docs"
    output_dir: "data/example"
```

#### Step 3: 执行爬取（遇到问题）

```bash
python .trae/skills/doc-crawler/scripts/smart_crawl.py example
```

**输出:**
```
🚀 开始智能爬取: example
============================================================

📍 文档入口: https://example.com/docs
🔍 测试内容选择器...
  ✗ 当前选择器无效: article (0 字符)
  ✗ 备选选择器 .vp-doc 无效
  ✗ 备选选择器 .sl-markdown-content 无效
  ✓ 找到有效选择器: .doc-content (12543 字符)
🔧 [10:23:45] 更新内容选择器: article -> .doc-content

🔍 测试侧边栏选择器...
  ✗ 当前选择器无效: .sidebar (0 个链接)
  ✗ 备选选择器 .VPSidebar 无效
  ✓ 找到有效选择器: nav (18 个链接)
🔧 [10:23:47] 更新侧边栏选择器: .sidebar -> nav

✅ 配置已自动调整，继续爬取...
```

#### Step 4: 自动更新配置

```yaml
sites:
  example:
    name: "Example Docs"
    base_url: "https://example.com"
    doc_url: "https://example.com/docs"
    selectors:
      content: ".doc-content"  # 已自动更新
      title: "h1"
    sidebar_selector: "nav"    # 已自动更新
    url_pattern: "/docs"
    output_dir: "data/example"
```

#### Step 5: 成功爬取

```
📥 开始爬取文档...
------------------------------------------------------------
找到 18 个文档页面
[1/18] 正在爬取: https://example.com/docs
  - 已保存: data/example/index.md
...
[18/18] 正在爬取: https://example.com/docs/api
  - 已保存: data/example/api.md

✅ 爬取完成!
```

---

## 情况 2: 需要 JavaScript 渲染

### 场景
文档站点使用 React/Vue 等前端框架渲染，静态爬取无法获取内容。

### 用户输入
```
爬取 https://some-react-docs.com 的文档
```

### AI 处理流程

#### Step 1: 分析网站
```bash
python .trae/skills/doc-crawler/scripts/analyze_site.py https://some-react-docs.com
```

**分析结果:**
```json
{
  "framework": "Unknown",
  "confidence": 0,
  "content_selector": {
    "recommended": "#root",
    "content_length": 0
  }
}
```

#### Step 2: 尝试静态爬取（失败）

```bash
python .trae/skills/doc-crawler/scripts/smart_crawl.py react-docs --type static
```

**输出:**
```
🚀 开始智能爬取: react-docs
============================================================

📍 文档入口: https://some-react-docs.com
🔍 测试内容选择器...
  ✗ 当前选择器无效: #root (0 字符)
  ⚠️ 检测到可能需要JS渲染: react
  ⚠️ 检测到可能需要JS渲染: window.__INITIAL_STATE__

🔄 切换到动态爬取模式...
```

#### Step 3: 自动切换到动态模式

```
🔧 [10:30:15] 切换模式: static -> dynamic (需要JS渲染)
🔄 切换到动态爬取模式...

🔍 测试内容选择器...
  ✓ 当前选择器有效: #root (23456 字符)

✅ 动态模式工作正常，继续爬取...
```

#### Step 4: 成功爬取

```bash
python .trae/skills/doc-crawler/scripts/smart_crawl.py react-docs --type dynamic
```

---

## 情况 3: 侧边栏链接提取失败

### 场景
侧边栏选择器无法匹配，需要尝试从全页面提取链接。

### AI 处理

```
🔍 测试侧边栏选择器...
  ✗ 当前选择器无效: .VPSidebar (0 个链接)
  ✗ 备选选择器 #starlight__sidebar 无效
  ✗ 备选选择器 .theme-doc-sidebar-menu 无效
  ✗ 备选选择器 .sidebar 无效
  ✗ 备选选择器 nav 无效

⚠️ 未找到有效的侧边栏选择器，将尝试从全页面提取链接
🔧 [10:35:22] 侧边栏策略: 使用全页面链接提取

📥 从全页面提取链接...
  ✓ 找到 32 个链接
  ✓ 过滤后剩余 15 个文档链接

✅ 链接提取成功，继续爬取...
```

---

## 情况 4: 编码问题（中文乱码）

### 场景
爬取中文文档时出现乱码。

### AI 处理

```python
# 在 crawler.py 中自动处理编码
def fetch_page(self, url: str, delay: float = None) -> Optional[str]:
    try:
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        
        # 强制 UTF-8 编码
        if response.encoding and response.encoding.lower() != "utf-8":
            response.encoding = "utf-8"
        
        return response.text
    except Exception as e:
        print(f"获取页面失败 {url}: {e}")
        return None
```

---

## 情况 5: 网络超时和重试

### 场景
网络不稳定导致请求失败。

### AI 处理

```python
# 自动重试机制
MAX_RETRIES = 3
RETRY_DELAY = 2  # 秒

def fetch_with_retry(self, url: str) -> Optional[str]:
    for attempt in range(MAX_RETRIES):
        try:
            result = self.fetch_page(url)
            if result:
                return result
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                print(f"  请求失败，{RETRY_DELAY}秒后重试... ({attempt + 1}/{MAX_RETRIES})")
                time.sleep(RETRY_DELAY)
            else:
                print(f"  请求失败，已达最大重试次数")
                raise
    return None
```

---

## 情况 6: URL 重定向处理

### 场景
文档链接发生重定向。

### AI 处理

```python
# 自动跟随重定向
response = self.session.get(url, timeout=30, allow_redirects=True)
final_url = response.url  # 获取最终URL

# 记录重定向
if final_url != url:
    print(f"  重定向: {url} -> {final_url}")
```

---

## 情况 7: 配置文件验证失败

### 场景
用户手动修改配置后出现错误。

### AI 处理

```bash
python .trae/skills/doc-crawler/scripts/validate_config.py --fix
```

**输出:**
```
📋 配置验证报告
============================================================

已配置站点数: 3

❌ 错误 (2):
  • [mysite] 缺少必填字段: selectors
  • [mysite] base_url格式错误，必须以http://或https://开头

⚠️  警告 (1):
  • [mysite] 未配置sidebar_selector

🔧 尝试自动修复...
🔧 [mysite] 自动添加selectors.title = h1
🔧 [mysite] 自动添加output_dir = data/mysite

重新验证...
✅ 配置验证通过！
```

---

## 情况 8: 爬取过程中被反爬

### 场景
服务器返回 403 或要求验证码。

### AI 处理策略

1. **增加请求延迟**
```yaml
settings:
  delay: 3.0  # 增加到3秒
```

2. **更换 User-Agent**
```yaml
settings:
  user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
```

3. **使用代理（如果需要）**
```python
proxies = {
    'http': 'http://proxy.example.com:8080',
    'https': 'https://proxy.example.com:8080',
}
response = self.session.get(url, proxies=proxies)
```

4. **提示用户**
```
⚠️ 检测到可能的反爬机制
建议:
  1. 增加请求延迟: settings.delay = 3.0
  2. 更换 User-Agent
  3. 使用代理服务器
  4. 稍后再试
```

---

## 情况 9: 输出目录权限问题

### 场景
无法写入输出目录。

### AI 处理

```python
from pathlib import Path

output_dir = Path(self.site_config.get("output_dir", f"data/{site_name}"))

try:
    output_dir.mkdir(parents=True, exist_ok=True)
except PermissionError:
    # 尝试使用临时目录
    import tempfile
    output_dir = Path(tempfile.gettempdir()) / "doc-crawler" / site_name
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"⚠️ 原目录无写入权限，使用临时目录: {output_dir}")
```

---

## 情况 10: 部分页面爬取失败

### 场景
大部分页面成功，少数页面失败。

### AI 处理

```
📥 开始爬取文档...
------------------------------------------------------------
找到 50 个文档页面
[1/50] 正在爬取: https://example.com/docs/page1
  - 已保存: data/example/page1.md
[2/50] 正在爬取: https://example.com/docs/page2
  - 获取失败，跳过
[3/50] 正在爬取: https://example.com/docs/page3
  - 未找到内容，跳过
...

============================================================
📋 爬取摘要
============================================================
  成功: 47 页
  失败: 2 页
  空内容: 1 页

❌ 错误记录:
  - Timeout: 请求超时 https://example.com/docs/page2
  - EmptyContent: 未找到内容 https://example.com/docs/page3

✅ 大部分页面已爬取完成！
```

---

## 总结

AI 在处理边界情况时的核心策略:

1. **自动检测** - 识别问题类型
2. **备选方案** - 尝试多种选择器
3. **模式切换** - static <-> dynamic
4. **自动修复** - 更新配置重试
5. **优雅降级** - 部分成功也接受
6. **清晰报告** - 告知用户发生了什么
