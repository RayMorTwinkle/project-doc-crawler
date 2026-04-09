#!/usr/bin/env python3
"""
配置验证工具
验证sites.yaml配置是否正确，检查必填字段
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, List, Tuple


class ConfigValidator:
    """配置验证器"""

    # 必填字段
    REQUIRED_FIELDS = ["name", "base_url", "selectors"]
    REQUIRED_SELECTORS = ["content", "title"]

    # 可选但有默认值的字段
    OPTIONAL_FIELDS = ["doc_url", "sidebar_selector", "url_pattern", "prefix_to_remove", "output_dir"]

    def __init__(self, config_path: str = "config/sites.yaml"):
        self.config_path = config_path
        self.config = None
        self.errors = []
        self.warnings = []

    def load_config(self) -> bool:
        """加载配置文件"""
        try:
            path = Path(self.config_path)
            if not path.exists():
                self.errors.append(f"配置文件不存在: {self.config_path}")
                return False

            with open(path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)

            if not self.config:
                self.errors.append("配置文件为空或格式错误")
                return False

            return True
        except yaml.YAMLError as e:
            self.errors.append(f"YAML解析错误: {e}")
            return False
        except Exception as e:
            self.errors.append(f"加载配置文件失败: {e}")
            return False

    def validate_site(self, site_name: str, site_config: Dict) -> Tuple[bool, List[str], List[str]]:
        """验证单个站点配置"""
        errors = []
        warnings = []

        # 检查必填字段
        for field in self.REQUIRED_FIELDS:
            if field not in site_config:
                errors.append(f"[{site_name}] 缺少必填字段: {field}")

        # 检查selectors
        if "selectors" in site_config:
            selectors = site_config["selectors"]
            if not isinstance(selectors, dict):
                errors.append(f"[{site_name}] selectors必须是字典类型")
            else:
                for selector_field in self.REQUIRED_SELECTORS:
                    if selector_field not in selectors:
                        errors.append(f"[{site_name}] selectors缺少: {selector_field}")
        else:
            errors.append(f"[{site_name}] 缺少selectors配置")

        # 检查URL格式
        if "base_url" in site_config:
            base_url = site_config["base_url"]
            if not base_url.startswith(("http://", "https://")):
                errors.append(f"[{site_name}] base_url格式错误，必须以http://或https://开头")

        # 检查doc_url（如果有）
        if "doc_url" in site_config:
            doc_url = site_config["doc_url"]
            if not doc_url.startswith(("http://", "https://")):
                errors.append(f"[{site_name}] doc_url格式错误")

        # 警告：建议配置sidebar_selector
        if "sidebar_selector" not in site_config:
            warnings.append(f"[{site_name}] 未配置sidebar_selector，将从全页面提取链接")

        # 警告：建议配置url_pattern
        if "url_pattern" not in site_config:
            warnings.append(f"[{site_name}] 未配置url_pattern，可能爬取无关页面")

        # 警告：检查output_dir
        if "output_dir" in site_config:
            output_dir = site_config["output_dir"]
            if output_dir.startswith("/"):
                warnings.append(f"[{site_name}] output_dir建议使用相对路径")

        return len(errors) == 0, errors, warnings

    def validate_all(self) -> bool:
        """验证所有配置"""
        if not self.load_config():
            return False

        sites = self.config.get("sites", {})

        if not sites:
            self.warnings.append("没有配置任何站点")
            return True

        all_valid = True

        for site_name, site_config in sites.items():
            if not isinstance(site_config, dict):
                self.errors.append(f"[{site_name}] 站点配置必须是字典类型")
                all_valid = False
                continue

            valid, errors, warnings = self.validate_site(site_name, site_config)
            if not valid:
                all_valid = False
            self.errors.extend(errors)
            self.warnings.extend(warnings)

        # 验证settings（如果有）
        settings = self.config.get("settings", {})
        if settings:
            self._validate_settings(settings)

        return all_valid

    def _validate_settings(self, settings: Dict):
        """验证全局设置"""
        # 检查delay
        if "delay" in settings:
            delay = settings["delay"]
            if not isinstance(delay, (int, float)):
                self.errors.append("[settings] delay必须是数字")
            elif delay < 0:
                self.errors.append("[settings] delay不能为负数")
            elif delay < 0.5:
                self.warnings.append("[settings] delay小于0.5秒，可能对服务器造成压力")

        # 检查timeout
        if "timeout" in settings:
            timeout = settings["timeout"]
            if not isinstance(timeout, int):
                self.errors.append("[settings] timeout必须是整数")
            elif timeout < 1:
                self.errors.append("[settings] timeout必须大于0")

        # 检查user_agent
        if "user_agent" in settings:
            user_agent = settings["user_agent"]
            if not isinstance(user_agent, str):
                self.errors.append("[settings] user_agent必须是字符串")

    def print_report(self):
        """打印验证报告"""
        print("\n" + "=" * 60)
        print("📋 配置验证报告")
        print("=" * 60)

        sites = self.config.get("sites", {}) if self.config else {}
        print(f"\n已配置站点数: {len(sites)}")

        if sites:
            print("\n站点列表:")
            for name in sites.keys():
                print(f"  - {name}")

        if self.errors:
            print("\n" + "-" * 40)
            print(f"❌ 错误 ({len(self.errors)}):")
            print("-" * 40)
            for error in self.errors:
                print(f"  • {error}")

        if self.warnings:
            print("\n" + "-" * 40)
            print(f"⚠️  警告 ({len(self.warnings)}):")
            print("-" * 40)
            for warning in self.warnings:
                print(f"  • {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ 配置验证通过！")

        print("\n" + "=" * 60)

    def fix_config(self) -> bool:
        """尝试自动修复配置"""
        if not self.config:
            return False

        fixed = False
        sites = self.config.get("sites", {})

        for site_name, site_config in sites.items():
            # 如果没有doc_url，使用base_url
            if "doc_url" not in site_config and "base_url" in site_config:
                site_config["doc_url"] = site_config["base_url"]
                fixed = True
                print(f"🔧 [{site_name}] 自动添加doc_url = base_url")

            # 如果没有output_dir，使用默认值
            if "output_dir" not in site_config:
                site_config["output_dir"] = f"data/{site_name}"
                fixed = True
                print(f"🔧 [{site_name}] 自动添加output_dir = data/{site_name}")

            # 如果没有selectors.title，添加默认值
            if "selectors" in site_config and "title" not in site_config["selectors"]:
                site_config["selectors"]["title"] = "h1"
                fixed = True
                print(f"🔧 [{site_name}] 自动添加selectors.title = h1")

        if fixed:
            try:
                with open(self.config_path, "w", encoding="utf-8") as f:
                    yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)
                print(f"\n✅ 配置已自动修复并保存")
                return True
            except Exception as e:
                print(f"\n❌ 保存修复后的配置失败: {e}")
                return False

        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description="配置验证工具")
    parser.add_argument("--config", default="config/sites.yaml", help="配置文件路径")
    parser.add_argument("--fix", action="store_true", help="自动修复配置")

    args = parser.parse_args()

    validator = ConfigValidator(args.config)
    is_valid = validator.validate_all()
    validator.print_report()

    if not is_valid and args.fix:
        print("\n🔧 尝试自动修复...")
        validator.fix_config()
        # 重新验证
        print("\n重新验证...")
        validator = ConfigValidator(args.config)
        is_valid = validator.validate_all()
        validator.print_report()

    if not is_valid:
        sys.exit(1)

    print("\n✅ 验证通过！")


if __name__ == "__main__":
    main()
