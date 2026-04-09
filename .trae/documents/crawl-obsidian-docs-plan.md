# Obsidian 插件文档爬取计划

## 目标
爬取 https://docs.obsidian.md/Plugins/ 下的所有文档，转换为 Markdown 格式。

## 网站分析

### 网站结构
- **基础 URL**: https://docs.obsidian.md
- **文档入口**: https://docs.obsidian.md/Plugins/Getting+started/Build+a+plugin
- **框架**: Obsidian Publish（静态生成）

### 页面结构分析
根据获取的页面内容，Obsidian 文档使用 Obsidian Publish 发布，页面结构如下：
- 内容区域：需要分析具体的选择器
- 标题：页面主标题
- 侧边栏：包含导航链接

### URL 模式
- 插件文档 URL 模式: `/Plugins/...`
- URL 使用 `+` 代替空格，如 `Getting+started`

## 实施步骤

### 步骤 1: 分析页面选择器
需要先用浏览器开发者工具分析页面结构，确定：
1. **正文内容选择器** - 文档主要内容区域
2. **标题选择器** - 页面标题
3. **侧边栏选择器** - 导航链接容器

### 步骤 2: 添加站点配置
在 `config/sites.yaml` 中添加 Obsidian 文档配置：

```yaml
obsidian:
  name: "Obsidian Developer Documentation"
  base_url: "https://docs.obsidian.md"
  doc_url: "https://docs.obsidian.md/Plugins/Getting+started/Build+a+plugin"
  selectors:
    content: "[待确定]"
    title: "h1"
  sidebar_selector: "[待确定]"
  url_pattern: "/Plugins"
  prefix_to_remove: ""
  output_dir: "data/obsidian"
```

### 步骤 3: 测试爬取
运行爬虫测试配置是否正确：
```bash
python main.py obsidian
```

### 步骤 4: 调试和修复
根据测试结果调整选择器配置，确保：
- 能正确提取所有文档链接
- 能正确提取页面内容
- 生成的 Markdown 格式正确

### 步骤 5: 完整爬取
确认配置无误后，完整爬取所有文档。

## 注意事项

1. **请求频率**: 保持默认 1 秒延迟，尊重服务器
2. **编码处理**: 项目已自动处理 UTF-8 编码
3. **URL 特殊字符**: URL 中包含 `+` 号需要正确处理
4. **内容完整性**: 检查是否所有 Plugins 下的文档都被爬取

## 预期输出

```
data/
└── obsidian/
    ├── Build+a+plugin.md
    ├── Getting+started/
    │   └── ...
    └── ...
```

## 风险评估

1. **选择器可能不准确** - 需要通过浏览器开发者工具确认
2. **Obsidian Publish 可能有反爬机制** - 如遇问题可调整请求频率
3. **动态加载内容** - 如果页面使用 JS 渲染，可能需要使用 dynamic 模式

## 下一步行动

1. 使用浏览器访问 https://docs.obsidian.md/Plugins/Getting+started/Build+a+plugin
2. 打开开发者工具（F12）分析页面结构
3. 确定正确的选择器
4. 更新配置文件
5. 执行爬取
