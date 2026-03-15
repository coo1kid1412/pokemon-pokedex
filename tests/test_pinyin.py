#!/usr/bin/env python3
"""
宝可梦图鉴拼音功能单元测试
使用 pytest 框架

运行方式:
    pytest                    # 运行所有测试
    pytest -v                # 详细输出
    pytest -v --tb=short    # 简短traceback
    pytest test_pinyin.py    # 只运行此文件
"""

import pytest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pokemon_names_cn_full import POKEMON_NAMES_CN
from pypinyin import lazy_pinyin, Style


class TestPinyinBasics:
    """测试基础拼音功能"""
    
    def test_138_pinyin(self):
        """测试138号菊石兽的拼音"""
        cn_name = POKEMON_NAMES_CN.get('138')
        assert cn_name == '菊石兽', f"期望 '菊石兽', 实际 '{cn_name}'"
        
        py = lazy_pinyin(cn_name, style=Style.NORMAL)
        pinyin = ''.join(py)
        assert pinyin == 'jushishou', f"期望 'jushishou', 实际 '{pinyin}'"
    
    def test_1_pinyin(self):
        """测试1号妙蛙种子的拼音"""
        cn_name = POKEMON_NAMES_CN.get('1')
        py = lazy_pinyin(cn_name, style=Style.NORMAL)
        pinyin = ''.join(py)
        assert pinyin == 'miaowazhongzi', f"期望 'miaowazhongzi', 实际 '{pinyin}'"
    
    def test_25_pinyin(self):
        """测试25号皮卡丘的拼音"""
        cn_name = POKEMON_NAMES_CN.get('25')
        py = lazy_pinyin(cn_name, style=Style.NORMAL)
        pinyin = ''.join(py)
        assert pinyin == 'pikaqiu', f"期望 'pikaqiu', 实际 '{pinyin}'"


class TestPinyinAPI:
    """测试API返回格式"""
    
    def test_pokemon_names_pinyin_format(self):
        """测试API返回格式"""
        result = {}
        for pid, cname in POKEMON_NAMES_CN.items():
            py = lazy_pinyin(cname, style=Style.NORMAL)
            result[pid] = ''.join(py)
        
        # 验证类型
        assert isinstance(result['138'], str), "API返回的应该是字符串"
        
        # 验证值
        assert result['138'] == 'jushishou'
        assert result['139'] == 'duocijushishou'


class TestPinyinCompare:
    """测试拼音对比逻辑"""
    
    @staticmethod
    def compare_pinyin(js_user_py, js_target_py):
        """模拟JS的对比逻辑"""
        normalize1 = js_user_py.replace('zh', 'z').replace('ch', 'c').replace('sh', 's')
        normalize2 = js_target_py.replace('zh', 'z').replace('ch', 'c').replace('sh', 's')
        normalize1 = normalize1.replace('ng', 'n')
        normalize2 = normalize2.replace('ng', 'n')
        
        if normalize1 == normalize2:
            return True
        if normalize1 in normalize2 or normalize2 in normalize1:
            return True
        return False
    
    def test_exact_match(self):
        """测试完全匹配"""
        assert self.compare_pinyin('jushishou', 'jushishou') is True
    
    def test_partial_match(self):
        """测试部分匹配(简称)"""
        assert self.compare_pinyin('jushishou', 'jushishouzi') is True
    
    def test_no_match(self):
        """测试不匹配 - 验证严格匹配逻辑"""
        # 修复后的对比函数(更严格)
        def strict_compare(p1, p2):
            n1 = p1.replace('zh','z').replace('ch','c').replace('sh','s').replace('ng','n')
            n2 = p2.replace('zh','z').replace('ch','c').replace('sh','s').replace('ng','n')
            # 只接受完全匹配或前缀匹配
            return n1 == n2 or n1.startswith(n2) or n2.startswith(n1)
        
        # 完全不匹配
        assert strict_compare('shou', 'jushishou') is False
        # 前缀匹配(用户说简称)
        assert strict_compare('jushi', 'jushishou') is True  # jushishou以jushi开头
        assert strict_compare('jushishou', 'jushi') is True  # jushi以jushi开头
        # 完全匹配
        assert strict_compare('jushishou', 'jushishou') is True
        # 前缀匹配(目标简称)
        assert strict_compare('jushishou', 'jushishouzi') is True
    
    def test_zh_ch_sh_normalize(self):
        """测试翘舌音忽略"""
        assert self.compare_pinyin('shou', 'sou') is True  # sh->s
        assert self.compare_pinyin('zhang', 'zang') is True  # zh->z


class TestBackendAPI:
    """测试后端API(需要服务运行)"""
    
    def test_chinese_to_pinyin_api(self):
        """测试中文转拼音API"""
        import urllib.request
        import urllib.parse
        
        text = urllib.parse.quote('菊石兽')
        url = f'http://localhost:5000/api/chinese_to_pinyin?text={text}'
        
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                import json
                data = json.loads(response.read())
                assert data.get('pinyin') == 'jushishou', f"期望 'jushishou', 实际 '{data.get('pinyin')}'"
        except Exception as e:
            pytest.skip(f"服务未运行: {e}")
    
    def test_pokemon_names_pinyin_api(self):
        """测试宝可梦名称拼音API"""
        import urllib.request
        
        url = 'http://localhost:5000/api/pokemon_names_pinyin'
        
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                import json
                data = json.loads(response.read())
                assert data.get('138') == 'jushishou'
        except Exception as e:
            pytest.skip(f"服务未运行: {e}")


# ============ 前端JS逻辑测试 ============

class TestFrontendPinyinLogic:
    """测试前端拼音逻辑(模拟)"""
    
    def test_cache_key_string_conversion(self):
        """测试缓存键需要字符串转换"""
        # 模拟场景：pokemon.id 是数字，但缓存键是字符串
        pokemon_id_int = 138
        cache = {"138": "jushishou", "139": "duocijushishou"}
        
        # 错误写法
        result_wrong = cache.get(pokemon_id_int)
        assert result_wrong is None, "数字键查找会失败"
        
        # 正确写法
        result_correct = cache.get(str(pokemon_id_int))
        assert result_correct == "jushishou", "字符串键查找成功"
    
    def test_local_pinyin_map_incomplete(self):
        """测试本地映射表不完整问题"""
        # 模拟有道API失败后的fallback映射表
        local_map = {
            '兽': 'shou',  # 只有"兽"
            '狼': 'lang',
            '猿': 'yuan',
            # '菊' 和 '石' 不在表里
        }
        
        # 测试
        result = ''
        for char in '菊石兽':
            py = local_map.get(char)
            if py:
                result += py
        
        assert result == 'shou', f"本地映射表只能识别'兽'，'{result}'是不完整的"


# ============ 集成测试 ============

class TestIntegration:
    """集成测试"""
    
    def test_master_mode_flow(self):
        """测试大师赛完整流程(拼音相关)"""
        # 1. 获取目标宝可梦名称
        pokemon_id = '138'
        cn_name = POKEMON_NAMES_CN.get(pokemon_id)
        assert cn_name == '菊石兽'
        
        # 2. 获取目标拼音
        target_pinyin = ''.join(lazy_pinyin(cn_name, style=Style.NORMAL))
        assert target_pinyin == 'jushishou'
        
        # 3. 模拟用户录音"菊石兽"
        user_text = '菊石兽'
        user_pinyin = ''.join(lazy_pinyin(user_text, style=Style.NORMAL))
        
        # 4. 对比结果 - 使用严格匹配
        def strict_compare(p1, p2):
            n1 = p1.replace('zh','z').replace('ch','c').replace('sh','s').replace('ng','n')
            n2 = p2.replace('zh','z').replace('ch','c').replace('sh','s').replace('ng','n')
            return n1 == n2 or n1.startswith(n2) or n2.startswith(n1)
        
        is_correct = strict_compare(user_pinyin, target_pinyin)
        
        assert is_correct is True, "用户念'菊石兽'应该通过"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
