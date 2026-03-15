"""
pytest 配置文件
"""

import pytest
import sys
import os

# 确保项目根目录在路径中
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def pytest_configure(config):
    """pytest 配置"""
    config.addinivalue_line(
        "markers", "slow: 标记慢速测试(如需要启动服务的集成测试)"
    )
    config.addinivalue_line(
        "markers", "integration: 标记集成测试"
    )
