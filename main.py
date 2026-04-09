"""
通用文档爬虫 - 主入口
"""

import argparse
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from crawler import StaticCrawler, DynamicCrawler


def main():
    parser = argparse.ArgumentParser(
        description="通用文档爬虫 - 抓取项目文档喂给AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py opencode              # 爬取 opencode 文档
  python main.py vue --type dynamic    # 使用动态爬虫爬取 Vue 文档
  python main.py --list                # 列出所有配置的站点
  python main.py --config my.yaml site # 使用自定义配置文件
        """,
    )

    parser.add_argument(
        "site",
        nargs="?",
        type=str,
        help="要爬取的站点名称（在 config/sites.yaml 中配置）",
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config/sites.yaml",
        help="配置文件路径（默认: config/sites.yaml）",
    )

    parser.add_argument(
        "--type",
        type=str,
        choices=["static", "dynamic"],
        default="static",
        help="爬取类型：static（静态页面）或 dynamic（需要JS渲染）",
    )

    parser.add_argument("--list", action="store_true", help="列出所有配置的站点")

    parser.add_argument("--output", type=str, help="输出目录（覆盖配置文件中的设置）")

    args = parser.parse_args()

    # 列出所有站点
    if args.list:
        import yaml

        with open(args.config, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        sites = config.get("sites", {})
        if not sites:
            print("未配置任何站点")
            return

        print("已配置的站点:")
        print("-" * 50)
        for name, site_config in sites.items():
            print(f"  {name}: {site_config.get('name', name)}")
            print(f"    URL: {site_config.get('base_url', 'N/A')}")
            print(f"    输出: {site_config.get('output_dir', f'data/{name}')}")
            print()
        return

    # 需要指定站点名称
    if not args.site:
        parser.print_help()
        return

    # 选择爬虫类型
    if args.type == "static":
        crawler = StaticCrawler(args.config)
    else:
        crawler = DynamicCrawler(args.config)

    # 覆盖输出目录
    if args.output:
        site_config = crawler.get_site_config(args.site)
        if site_config:
            site_config["output_dir"] = args.output

    # 执行爬取
    crawler.crawl(args.site)


if __name__ == "__main__":
    main()
