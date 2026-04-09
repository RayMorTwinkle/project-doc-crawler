#!/usr/bin/env python3
"""
智能文档爬取脚本
支持自适应调整、自动重试、错误恢复
"""

import sys
import json
import time
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

# 添加项目src目录到路径
script_dir = Path(__file__).parent.resolve()
skill_dir = script_dir.parent
project_root = skill_dir.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

try:
    from crawler import StaticCrawler, DynamicCrawler
except ImportError as e:
    # 尝试另一种路径
    import os
    cwd = Path(os.getcwd())
    sys.path.insert(0, str(cwd / "src"))
    try:
        from crawler import StaticCrawler, DynamicCrawler
    except ImportError:
        print(f"❌ 无法导入crawler模块: {e}")
        print(f"   请确保在项目根目录运行，或检查src/crawler.py是否存在")
        print(f"   当前工作目录: {os.getcwd()}")
        print(f"   尝试的路径: {project_root / 'src'}, {cwd / 'src'}")
        sys.exit(1)


# 备选选择器列表
FALLBACK_CONTENT_SELECTORS = [
    ".vp-doc",
    ".sl-markdown-content",
    ".theme-doc-markdown",
    ".markdown-section",
    ".theme-default-content",
    "article",
    "main",
    ".content",
    ".main-content",
    "[role='main']",
]

FALLBACK_SIDEBAR_SELECTORS = [
    ".VPSidebar",
    "#starlight__sidebar",
    ".theme-doc-sidebar-menu",
    ".sidebar",
    ".side-bar",
    "nav",
    ".navigation",
    ".menu",
    ".toc",
    "[role='navigation']",
]


class SmartCrawler:
    """智能爬虫，支持自适应调整"""

    def __init__(self, site_name: str, config_path: str = "config/sites.yaml"):
        self.site_name = site_name
        self.config_path = config_path
        self.config = self._load_config()
        self.site_config = self.config.get("sites", {}).get(site_name, {})
        self.crawler = None
        self.report = {
            "site": site_name,
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "pages_total": 0,
            "pages_success": 0,
            "pages_failed": 0,
            "pages_empty": 0,
            "errors": [],
            "adjustments": [],
            "output_files": [],
        }

    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"❌ 加载配置文件失败: {e}")
            return {}

    def _save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)
        except Exception as e:
            print(f"⚠️ 保存配置文件失败: {e}")

    def _log_adjustment(self, action: str, details: str):
        """记录调整操作"""
        adjustment = {
            "time": time.strftime("%H:%M:%S"),
            "action": action,
            "details": details,
        }
        self.report["adjustments"].append(adjustment)
        print(f"🔧 [{adjustment['time']}] {action}: {details}")

    def _log_error(self, error_type: str, message: str, url: str = ""):
        """记录错误"""
        error = {
            "time": time.strftime("%H:%M:%S"),
            "type": error_type,
            "message": message,
            "url": url,
        }
        self.report["errors"].append(error)
        print(f"❌ [{error['time']}] {error_type}: {message}")

    def _init_crawler(self, crawl_type: str = "static"):
        """初始化爬虫"""
        if crawl_type == "dynamic":
            self.crawler = DynamicCrawler(self.config_path)
        else:
            self.crawler = StaticCrawler(self.config_path)

    def _test_content_selector(self, url: str, selector: str) -> Tuple[bool, int]:
        """测试内容选择器是否有效"""
        try:
            html = self.crawler.fetch_page(url)
            if not html:
                return False, 0

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")
            elements = soup.select(selector)

            if elements:
                total_text = sum(len(el.get_text(strip=True)) for el in elements)
                return True, total_text
            return False, 0
        except Exception as e:
            return False, 0

    def _find_working_content_selector(self, url: str) -> Optional[str]:
        """找到可用的内容选择器"""
        print(f"🔍 测试内容选择器...")

        current_selector = self.site_config.get("selectors", {}).get("content", "")

        # 先测试当前配置
        if current_selector:
            success, length = self._test_content_selector(url, current_selector)
            if success and length > 100:
                print(f"  ✓ 当前选择器有效: {current_selector} ({length} 字符)")
                return current_selector

        # 尝试备选选择器
        for selector in FALLBACK_CONTENT_SELECTORS:
            if selector == current_selector:
                continue

            success, length = self._test_content_selector(url, selector)
            if success and length > 100:
                print(f"  ✓ 找到有效选择器: {selector} ({length} 字符)")
                self._log_adjustment("更新内容选择器", f"{current_selector} -> {selector}")

                # 更新配置
                self.site_config["selectors"]["content"] = selector
                self.config["sites"][self.site_name] = self.site_config
                self._save_config()

                return selector

        return None

    def _test_sidebar_selector(self, url: str, selector: str) -> Tuple[bool, int]:
        """测试侧边栏选择器是否有效"""
        try:
            html = self.crawler.fetch_page(url)
            if not html:
                return False, 0

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")
            sidebar = soup.select_one(selector)

            if sidebar:
                links = sidebar.find_all("a", href=True)
                return True, len(links)
            return False, 0
        except Exception as e:
            return False, 0

    def _find_working_sidebar_selector(self, url: str) -> Optional[str]:
        """找到可用的侧边栏选择器"""
        print(f"🔍 测试侧边栏选择器...")

        current_selector = self.site_config.get("sidebar_selector", "")

        # 先测试当前配置
        if current_selector:
            success, count = self._test_sidebar_selector(url, current_selector)
            if success and count > 0:
                print(f"  ✓ 当前选择器有效: {current_selector} ({count} 个链接)")
                return current_selector

        # 尝试备选选择器
        for selector in FALLBACK_SIDEBAR_SELECTORS:
            if selector == current_selector:
                continue

            success, count = self._test_sidebar_selector(url, selector)
            if success and count > 0:
                print(f"  ✓ 找到有效选择器: {selector} ({count} 个链接)")
                self._log_adjustment("更新侧边栏选择器", f"{current_selector} -> {selector}")

                # 更新配置
                self.site_config["sidebar_selector"] = selector
                self.config["sites"][self.site_name] = self.site_config
                self._save_config()

                return selector

        return None

    def _check_needs_dynamic(self, url: str) -> bool:
        """检查是否需要动态渲染"""
        try:
            html = self.crawler.fetch_page(url)
            if not html:
                return False

            # 检查是否有明显的JS框架特征
            js_indicators = [
                "vue",
                "react",
                "angular",
                "next.js",
                "nuxt",
                "window.__INITIAL_STATE__",
                "window.__DATA__",
                "hydrate",
                "data-server-rendered",
            ]

            html_lower = html.lower()
            for indicator in js_indicators:
                if indicator in html_lower:
                    print(f"  ⚠️ 检测到可能需要JS渲染: {indicator}")
                    return True

            return False
        except:
            return False

    def _switch_to_dynamic(self):
        """切换到动态爬取模式"""
        self._log_adjustment("切换模式", "static -> dynamic (需要JS渲染)")
        print("🔄 切换到动态爬取模式...")

        try:
            self.crawler = DynamicCrawler(self.config_path)
            return True
        except Exception as e:
            self._log_error("切换动态模式失败", str(e))
            print(f"❌ 无法切换到动态模式: {e}")
            print("   请确保已安装selenium和ChromeDriver")
            return False

    def crawl(self, crawl_type: str = "static") -> Dict:
        """执行智能爬取"""
        print(f"\n🚀 开始智能爬取: {self.site_name}")
        print("=" * 60)

        if not self.site_config:
            print(f"❌ 未找到站点配置: {self.site_name}")
            return {"error": "Site not found"}

        # 初始化爬虫
        self._init_crawler(crawl_type)

        base_url = self.site_config.get("base_url")
        doc_url = self.site_config.get("doc_url", base_url)

        print(f"📍 文档入口: {doc_url}")

        # Step 1: 检查并修复内容选择器
        content_selector = self._find_working_content_selector(doc_url)
        if not content_selector:
            # 尝试切换到动态模式
            if crawl_type == "static" and self._check_needs_dynamic(doc_url):
                if self._switch_to_dynamic():
                    return self.crawl("dynamic")

            self._log_error("选择器错误", "无法找到有效的内容选择器")
            return {"error": "No working content selector found"}

        # Step 2: 检查并修复侧边栏选择器
        sidebar_selector = self._find_working_sidebar_selector(doc_url)
        if not sidebar_selector:
            print("⚠️ 未找到有效的侧边栏选择器，将尝试从全页面提取链接")
            self._log_adjustment("侧边栏策略", "使用全页面链接提取")

        # Step 3: 执行爬取
        print("\n📥 开始爬取文档...")
        print("-" * 60)

        try:
            # 使用基础爬虫的crawl方法
            self.crawler.crawl(self.site_name)

            # 统计结果
            output_dir = Path(self.site_config.get("output_dir", f"data/{self.site_name}"))
            if output_dir.exists():
                md_files = list(output_dir.glob("*.md"))
                self.report["pages_success"] = len(md_files)
                self.report["output_files"] = [str(f) for f in md_files]

        except Exception as e:
            self._log_error("爬取异常", str(e))

        # 生成报告
        self.report["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self._generate_report()

        return self.report

    def _generate_report(self):
        """生成爬取报告"""
        output_dir = Path(self.site_config.get("output_dir", f"data/{self.site_name}"))
        report_path = output_dir / "_crawl_report.json"

        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(self.report, f, indent=2, ensure_ascii=False)
            print(f"\n📊 报告已保存: {report_path}")
        except Exception as e:
            print(f"⚠️ 保存报告失败: {e}")

        # 打印摘要
        print("\n" + "=" * 60)
        print("📋 爬取摘要")
        print("=" * 60)
        print(f"  成功: {self.report['pages_success']} 页")
        print(f"  失败: {self.report['pages_failed']} 页")
        print(f"  空内容: {self.report['pages_empty']} 页")
        print(f"  调整次数: {len(self.report['adjustments'])}")
        print(f"  错误次数: {len(self.report['errors'])}")

        if self.report["adjustments"]:
            print("\n🔧 自适应调整:")
            for adj in self.report["adjustments"]:
                print(f"  - {adj['action']}: {adj['details']}")

        if self.report["errors"]:
            print("\n❌ 错误记录:")
            for err in self.report["errors"][:5]:  # 只显示前5个
                print(f"  - {err['type']}: {err['message']}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="智能文档爬虫")
    parser.add_argument("site", help="站点名称")
    parser.add_argument("--config", default="config/sites.yaml", help="配置文件路径")
    parser.add_argument("--type", choices=["static", "dynamic"], default="static", help="爬取类型")

    args = parser.parse_args()

    crawler = SmartCrawler(args.site, args.config)
    report = crawler.crawl(args.type)

    if "error" in report:
        print(f"\n❌ 爬取失败: {report['error']}")
        sys.exit(1)

    print("\n✅ 爬取完成!")


if __name__ == "__main__":
    main()
