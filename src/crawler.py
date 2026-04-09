"""
通用文档爬虫核心
支持多种网站的文档爬取
"""

from typing import List, Dict, Optional, Callable
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import time
import yaml
import requests
from pathlib import Path


class BaseCrawler:
    """爬虫基类"""

    def __init__(self, config_path: str = "config/sites.yaml"):
        self.config = self._load_config(config_path)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.config.get("settings", {}).get(
                    "user_agent",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                )
            }
        )
        self.visited_urls = set()

    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def get_site_config(self, site_name: str) -> Dict:
        """获取站点配置"""
        return self.config.get("sites", {}).get(site_name, {})

    def fetch_page(self, url: str, delay: float = None) -> Optional[str]:
        """获取页面内容"""
        if delay is None:
            delay = self.config.get("settings", {}).get("delay", 1.0)

        try:
            time.sleep(delay)
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # 确保正确处理编码
            if response.encoding and response.encoding.lower() != "utf-8":
                response.encoding = "utf-8"

            return response.text
        except Exception as e:
            print(f"获取页面失败 {url}: {e}")
            return None

    def extract_links_from_selector(
        self, html: str, base_url: str, selector: str = "a"
    ) -> List[str]:
        """从指定选择器提取链接"""
        soup = BeautifulSoup(html, "lxml")
        links = []

        container = soup.select_one(selector) if selector != "a" else soup
        if container:
            for a_tag in container.find_all("a", href=True):
                href = a_tag["href"]
                full_url = urljoin(base_url, href)

                # 只处理同域名链接
                if urlparse(full_url).netloc == urlparse(base_url).netloc:
                    links.append(full_url)

        return list(set(links))

    def extract_links_from_sidebar(
        self,
        html: str,
        base_url: str,
        sidebar_selector: str = "#starlight__sidebar",
        url_pattern: str = None,
    ) -> List[str]:
        """从侧边栏提取文档链接"""
        soup = BeautifulSoup(html, "lxml")
        links = []

        sidebar = soup.select_one(sidebar_selector)
        if sidebar:
            for a_tag in sidebar.find_all("a", href=True):
                href = a_tag["href"]
                full_url = urljoin(base_url, href)

                if urlparse(full_url).netloc == urlparse(base_url).netloc:
                    if url_pattern is None or re.search(url_pattern, full_url):
                        links.append(full_url)
        else:
            # 如果没有找到侧边栏，从整个页面提取
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                full_url = urljoin(base_url, href)
                if urlparse(full_url).netloc == urlparse(base_url).netloc:
                    if url_pattern is None or re.search(url_pattern, full_url):
                        links.append(full_url)

        return list(set(links))

    def extract_content(self, html: str, selectors: Dict) -> Dict:
        """提取页面内容"""
        soup = BeautifulSoup(html, "lxml")
        content = {"title": "", "body": ""}

        # 提取标题
        title_elem = soup.select_one(selectors.get("title", "h1"))
        if title_elem:
            content["title"] = title_elem.get_text(strip=True)

        # 提取正文
        content_elem = soup.select_one(selectors.get("content", "article"))
        if content_elem:
            content["body"] = str(content_elem)

        return content

    def html_to_markdown(self, html: str) -> str:
        """HTML转Markdown"""
        from markdownify import markdownify

        return markdownify(html, heading_style="ATX")

    def get_filename_from_url(self, url: str, prefix_to_remove: str = None) -> str:
        """从URL生成文件名"""
        path = urlparse(url).path.rstrip("/")

        if prefix_to_remove:
            if path.startswith(prefix_to_remove):
                path = path[len(prefix_to_remove) :]

        # 获取最后一部分作为文件名
        filename = path.strip("/").split("/")[-1] if path.strip("/") else "index"
        return filename

    def save_content(self, content: str, filepath: str) -> None:
        """保存内容到文件"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    def crawl(self, site_name: str) -> None:
        """爬取文档（可被子类覆盖）"""
        site_config = self.get_site_config(site_name)
        if not site_config:
            print(f"未找到站点配置: {site_name}")
            return

        base_url = site_config.get("base_url")
        doc_url = site_config.get("doc_url", base_url)
        selectors = site_config.get("selectors", {})
        output_dir = site_config.get("output_dir", f"data/{site_name}")
        url_pattern = site_config.get("url_pattern")
        sidebar_selector = site_config.get("sidebar_selector", "nav")
        prefix_to_remove = site_config.get("prefix_to_remove")

        print(f"开始爬取: {site_name}")
        print(f"起始URL: {doc_url}")

        # 获取首页
        html = self.fetch_page(doc_url)
        if not html:
            print("无法获取首页，请检查网络连接")
            return

        # 提取文档链接
        links = self.extract_links_from_sidebar(
            html, base_url, sidebar_selector, url_pattern
        )
        print(f"找到 {len(links)} 个文档页面")

        if not links:
            print("未找到任何文档链接")
            return

        # 爬取每个页面
        for i, url in enumerate(sorted(links)):
            if url in self.visited_urls:
                continue

            self.visited_urls.add(url)
            print(f"[{i + 1}/{len(links)}] 正在爬取: {url}")

            page_html = self.fetch_page(url)
            if not page_html:
                print(f"  - 获取失败，跳过")
                continue

            # 提取内容
            content = self.extract_content(page_html, selectors)

            if not content["body"]:
                print(f"  - 未找到内容，跳过")
                continue

            # 转换为Markdown
            md_content = self.html_to_markdown(content["body"])
            md_content = f"# {content['title']}\n\n{md_content}"

            # 生成文件名
            filename = self.get_filename_from_url(url, prefix_to_remove)
            filepath = f"{output_dir}/{filename}.md"

            # 保存
            self.save_content(md_content, filepath)
            print(f"  - 已保存: {filepath}")

        print(f"\n爬取完成: {site_name}")
        print(f"共爬取 {len(self.visited_urls)} 个页面")
        print(f"保存位置: {output_dir}")


class StaticCrawler(BaseCrawler):
    """静态页面爬虫"""

    pass


class DynamicCrawler(BaseCrawler):
    """动态页面爬虫（需要JavaScript渲染）"""

    def __init__(self, config_path: str = "config/sites.yaml"):
        super().__init__(config_path)
        self.driver = None

    def init_driver(self):
        """初始化浏览器驱动"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options

            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            self.driver = webdriver.Chrome(options=options)
        except ImportError:
            print("需要安装 selenium 和 chromedriver")
            raise

    def fetch_page(self, url: str, delay: float = None) -> Optional[str]:
        """使用浏览器获取页面内容"""
        if self.driver is None:
            self.init_driver()

        if delay is None:
            delay = self.config.get("settings", {}).get("delay", 1.0)

        try:
            time.sleep(delay)
            self.driver.get(url)
            time.sleep(2)  # 等待页面加载
            return self.driver.page_source
        except Exception as e:
            print(f"获取页面失败 {url}: {e}")
            return None

    def __del__(self):
        """清理资源"""
        if self.driver:
            self.driver.quit()
