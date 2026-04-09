#!/usr/bin/env python3
"""
网站结构分析工具
自动识别文档框架类型并推荐选择器配置
"""

import sys
import json
import re
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from typing import Dict, List, Tuple, Optional

# 框架识别模式
FRAMEWORK_PATTERNS = {
    "VitePress": {
        "indicators": [".VPDoc", ".vp-doc", ".VPContent", ".VPSidebar", "vitepress"],
        "content_selectors": [".vp-doc", ".VPContent", "main"],
        "sidebar_selectors": [".VPSidebar", ".sidebar", "nav"],
    },
    "Docusaurus": {
        "indicators": ["__docusaurus", ".theme-doc-markdown", ".theme-doc-sidebar", "docusaurus"],
        "content_selectors": [".theme-doc-markdown", ".markdown", "article"],
        "sidebar_selectors": [".theme-doc-sidebar-menu", ".menu", ".sidebar"],
    },
    "Astro/Starlight": {
        "indicators": [".sl-markdown-content", ".sl-container", "starlight", "data-astro"],
        "content_selectors": [".sl-markdown-content", ".sl-container", "article"],
        "sidebar_selectors": ["#starlight__sidebar", ".sidebar", "nav"],
    },
    "GitBook": {
        "indicators": [".book", ".markdown-section", "gitbook"],
        "content_selectors": [".markdown-section", ".book-body", "article"],
        "sidebar_selectors": [".summary", ".book-summary", ".sidebar"],
    },
    "Docsify": {
        "indicators": ["docsify", "#app", "data-docsify"],
        "content_selectors": [".markdown-section", "#main", "article"],
        "sidebar_selectors": [".sidebar", "nav", ".docsify-sidebar"],
    },
    "VuePress": {
        "indicators": [".theme-default-content", ".vuepress", "vuepress"],
        "content_selectors": [".theme-default-content", ".content", "article"],
        "sidebar_selectors": [".sidebar-links", ".sidebar", "nav"],
    },
    "ReadTheDocs": {
        "indicators": [".wy-nav-content", "readthedocs", ".rst-content"],
        "content_selectors": [".rst-content", "[role='main']", "article"],
        "sidebar_selectors": [".wy-nav-side", ".sidebar", "nav"],
    },
    "MDN": {
        "indicators": [".mdn", "mdn-docs", "mozilla"],
        "content_selectors": ["article", "main", ".content"],
        "sidebar_selectors": [".sidebar", "nav", ".toc"],
    },
    "Nuxt/Docus": {
        "indicators": [".docus-content", ".docus-sidebar", "nuxt"],
        "content_selectors": [".docus-content", ".prose", "article"],
        "sidebar_selectors": [".docus-sidebar", ".sidebar", "nav"],
    },
    "Mintlify": {
        "indicators": [".prose", "mintlify", "data-mintlify"],
        "content_selectors": [".prose", "article", "main"],
        "sidebar_selectors": [".sidebar", "nav", ".toc"],
    },
}

# 通用备选选择器
FALLBACK_SELECTORS = {
    "content": [
        "article",
        "main",
        ".content",
        ".main-content",
        "[role='main']",
        ".documentation",
        ".doc-content",
    ],
    "sidebar": [
        ".sidebar",
        ".side-bar",
        "nav",
        ".navigation",
        ".menu",
        ".toc",
        "[role='navigation']",
    ],
}


class SiteAnalyzer:
    """网站结构分析器"""

    def __init__(self, url: str):
        self.url = url
        self.base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        self.html = None
        self.soup = None
        self.framework = None
        self.confidence = 0

    def fetch_page(self) -> bool:
        """获取页面内容"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
            response = requests.get(self.url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # 确保UTF-8编码
            if response.encoding and response.encoding.lower() != "utf-8":
                response.encoding = "utf-8"
            
            self.html = response.text
            self.soup = BeautifulSoup(self.html, "lxml")
            return True
        except Exception as e:
            print(f"❌ 获取页面失败: {e}", file=sys.stderr)
            return False

    def detect_framework(self) -> Tuple[str, int]:
        """检测文档框架类型"""
        if not self.soup:
            return "Unknown", 0

        html_str = str(self.soup)
        scores = {}

        for framework, patterns in FRAMEWORK_PATTERNS.items():
            score = 0
            for indicator in patterns["indicators"]:
                # 检查class、id、属性等
                if indicator.startswith("."):
                    # class选择器
                    if self.soup.find_all(class_=indicator[1:]):
                        score += 2
                elif indicator.startswith("#"):
                    # id选择器
                    if self.soup.find(id=indicator[1:]):
                        score += 3
                elif indicator.startswith("["):
                    # 属性选择器
                    if indicator in html_str:
                        score += 2
                else:
                    # 通用字符串匹配
                    if indicator.lower() in html_str.lower():
                        score += 1

            scores[framework] = score

        # 找出得分最高的框架
        if scores:
            best_match = max(scores, key=scores.get)
            best_score = scores[best_match]
            
            # 计算置信度 (0-100)
            confidence = min(best_score * 20, 100)
            
            if best_score > 0:
                return best_match, confidence

        return "Unknown", 0

    def test_selectors(self, selectors: List[str], selector_type: str = "content") -> List[Tuple[str, int]]:
        """测试选择器是否有效，返回匹配结果列表"""
        if not self.soup:
            return []

        results = []
        for selector in selectors:
            try:
                elements = self.soup.select(selector)
                if elements:
                    # 计算内容长度作为评分依据
                    total_text = sum(len(el.get_text(strip=True)) for el in elements)
                    results.append((selector, total_text))
            except Exception:
                continue

        # 按内容长度排序（内容越多越可能是正文）
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def analyze_sidebar_links(self, sidebar_selector: str) -> Dict:
        """分析侧边栏链接结构"""
        if not self.soup:
            return {}

        result = {
            "selector": sidebar_selector,
            "found": False,
            "link_count": 0,
            "links": [],
            "url_pattern": "",
        }

        try:
            sidebar = self.soup.select_one(sidebar_selector)
            if sidebar:
                result["found"] = True
                links = sidebar.find_all("a", href=True)
                result["link_count"] = len(links)
                
                # 提取链接样本（最多10个）
                for link in links[:10]:
                    href = link.get("href", "")
                    text = link.get_text(strip=True)
                    if href and text:
                        result["links"].append({"text": text, "href": href})

                # 分析URL模式
                if links:
                    hrefs = [l.get("href", "") for l in links if l.get("href", "").startswith("/")]
                    if hrefs:
                        # 找出共同前缀
                        common_prefix = self._find_common_prefix(hrefs)
                        if common_prefix:
                            result["url_pattern"] = common_prefix

        except Exception as e:
            result["error"] = str(e)

        return result

    def _find_common_prefix(self, urls: List[str]) -> str:
        """找出URL列表的共同前缀"""
        if not urls:
            return ""

        # 分割路径
        paths = [url.strip("/").split("/") for url in urls]
        if not paths:
            return ""

        # 找出共同部分
        min_len = min(len(p) for p in paths)
        common = []

        for i in range(min_len):
            parts = [p[i] for p in paths]
            if len(set(parts)) == 1:
                common.append(parts[0])
            else:
                break

        return "/" + "/".join(common) if common else ""

    def analyze(self) -> Dict:
        """执行完整分析"""
        print(f"🔍 正在分析: {self.url}")
        
        if not self.fetch_page():
            return {"error": "Failed to fetch page"}

        # 1. 检测框架
        self.framework, self.confidence = self.detect_framework()
        print(f"📦 检测到框架: {self.framework} (置信度: {self.confidence}%)")

        # 2. 获取推荐选择器
        if self.framework in FRAMEWORK_PATTERNS:
            recommended = FRAMEWORK_PATTERNS[self.framework]
            content_selectors = recommended["content_selectors"] + FALLBACK_SELECTORS["content"]
            sidebar_selectors = recommended["sidebar_selectors"] + FALLBACK_SELECTORS["sidebar"]
        else:
            content_selectors = FALLBACK_SELECTORS["content"]
            sidebar_selectors = FALLBACK_SELECTORS["sidebar"]

        # 3. 测试内容选择器
        print("📝 测试内容选择器...")
        content_results = self.test_selectors(content_selectors, "content")
        best_content = content_results[0] if content_results else ("", 0)

        # 4. 测试侧边栏选择器
        print("📑 测试侧边栏选择器...")
        sidebar_results = self.test_selectors(sidebar_selectors, "sidebar")
        best_sidebar = sidebar_results[0] if sidebar_results else ("", 0)

        # 5. 分析侧边栏链接
        sidebar_analysis = self.analyze_sidebar_links(best_sidebar[0]) if best_sidebar[0] else {}

        # 6. 生成建议配置
        suggested_config = self._generate_config(best_content[0], best_sidebar[0], sidebar_analysis)

        return {
            "url": self.url,
            "base_url": self.base_url,
            "framework": self.framework,
            "confidence": self.confidence,
            "content_selector": {
                "recommended": best_content[0],
                "content_length": best_content[1],
                "alternatives": [s[0] for s in content_results[1:4]],
            },
            "sidebar_selector": {
                "recommended": best_sidebar[0],
                "link_count": sidebar_analysis.get("link_count", 0),
                "alternatives": [s[0] for s in sidebar_results[1:4]],
            },
            "sidebar_links": sidebar_analysis,
            "suggested_config": suggested_config,
        }

    def _generate_config(self, content_selector: str, sidebar_selector: str, sidebar_analysis: Dict) -> Dict:
        """生成建议配置"""
        site_id = self._generate_site_id()
        url_pattern = sidebar_analysis.get("url_pattern", "")

        config = {
            "name": f"{self.framework} Documentation" if self.framework != "Unknown" else "Documentation Site",
            "base_url": self.base_url,
            "doc_url": self.url,
            "selectors": {
                "content": content_selector or "article",
                "title": "h1",
            },
            "sidebar_selector": sidebar_selector or "nav",
            "url_pattern": url_pattern or "/",
            "prefix_to_remove": url_pattern,
            "output_dir": f"data/{site_id}",
        }

        return config

    def _generate_site_id(self) -> str:
        """生成站点ID"""
        domain = urlparse(self.url).netloc.replace("www.", "").replace(".", "_")
        path = urlparse(self.url).path.strip("/").replace("/", "_")
        if path:
            return f"{domain}_{path}"
        return domain


def print_analysis_report(analysis: Dict):
    """打印分析报告"""
    print("\n" + "=" * 60)
    print("📊 网站结构分析报告")
    print("=" * 60)

    print(f"\n🔗 URL: {analysis['url']}")
    print(f"🏠 Base URL: {analysis['base_url']}")
    print(f"📦 框架类型: {analysis['framework']} (置信度: {analysis['confidence']}%)")

    print("\n" + "-" * 40)
    print("📝 内容选择器")
    print("-" * 40)
    content = analysis["content_selector"]
    print(f"  推荐: {content['recommended']}")
    print(f"  内容长度: {content['content_length']} 字符")
    if content["alternatives"]:
        print(f"  备选: {', '.join(content['alternatives'])}")

    print("\n" + "-" * 40)
    print("📑 侧边栏选择器")
    print("-" * 40)
    sidebar = analysis["sidebar_selector"]
    print(f"  推荐: {sidebar['recommended']}")
    print(f"  链接数量: {sidebar['link_count']}")
    if sidebar["alternatives"]:
        print(f"  备选: {', '.join(sidebar['alternatives'])}")

    # 显示链接样本
    links = analysis.get("sidebar_links", {}).get("links", [])
    if links:
        print(f"\n  链接样本:")
        for link in links[:5]:
            print(f"    - {link['text'][:40]}: {link['href']}")

    print("\n" + "=" * 60)
    print("⚙️  建议配置 (sites.yaml)")
    print("=" * 60)
    config = analysis["suggested_config"]
    print(f"""
sites:
  {analysis['base_url'].replace('https://', '').replace('http://', '').replace('.', '_')}:
    name: "{config['name']}"
    base_url: "{config['base_url']}"
    doc_url: "{config['doc_url']}"
    selectors:
      content: "{config['selectors']['content']}"
      title: "{config['selectors']['title']}"
    sidebar_selector: "{config['sidebar_selector']}"
    url_pattern: "{config['url_pattern']}"
    prefix_to_remove: "{config['prefix_to_remove']}"
    output_dir: "{config['output_dir']}"
""")


def main():
    if len(sys.argv) < 2:
        print("用法: python analyze_site.py <url>")
        print("示例: python analyze_site.py https://vuejs.org/guide/introduction.html")
        sys.exit(1)

    url = sys.argv[1]
    
    # 确保URL有协议前缀
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    analyzer = SiteAnalyzer(url)
    analysis = analyzer.analyze()

    if "error" in analysis:
        print(f"❌ 分析失败: {analysis['error']}")
        sys.exit(1)

    print_analysis_report(analysis)

    # 输出JSON格式（供程序解析）
    print("\n📋 JSON输出:")
    print(json.dumps(analysis, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
