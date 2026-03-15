#!/usr/bin/env python3
"""拼音识别单元测试 - 验证138号菊石兽的拼音逻辑"""

import sys
sys.path.insert(0, '/Users/lailixiang/.openclaw/workspace/pokemon')

from pokemon_names_cn_full import POKEMON_NAMES_CN
from pypinyin import lazy_pinyin, Style

def test_pinyin_basics():
    """测试基础拼音功能"""
    print("=" * 50)
    print("测试1: 基础拼音库")
    print("=" * 50)
    
    # 138号应该是菊石兽
    cn_name = POKEMON_NAMES_CN.get('138')
    print(f"138号中文名: {cn_name}")
    
    # 用pypinyin转换
    py = lazy_pinyin(cn_name, style=Style.NORMAL)
    pinyin = ''.join(py)
    print(f"pypinyin结果: {pinyin}")
    
    assert pinyin == 'jushishou', f"期望 jushishou，实际 {pinyin}"
    print("✅ 测试通过!\n")

def test_pinyin_api():
    """测试API返回格式"""
    print("=" * 50)
    print("测试2: API返回格式模拟")
    print("=" * 50)
    
    # 模拟API返回格式
    result = {}
    for pid, cname in POKEMON_NAMES_CN.items():
        py = lazy_pinyin(cname, style=Style.NORMAL)
        result[pid] = ''.join(py)
    
    print(f"API返回 138: {result['138']}")
    print(f"类型: {type(result['138'])}")
    
    # 模拟前端读取
    target_pinyin = result.get('138', '')
    print(f"前端读取: {target_pinyin}")
    
    assert target_pinyin == 'jushishou', f"期望 jushishou，实际 {target_pinyin}"
    print("✅ 测试通过!\n")

def test_compare_logic():
    """测试拼音对比逻辑"""
    print("=" * 50)
    print("测试3: 拼音对比逻辑(JS模拟)")
    print("=" * 50)
    
    # 模拟JS的comparePinyinIgnoreDiff函数
    def compare_pinyin(js_user_py, js_target_py):
        """模拟JS的对比逻辑"""
        normalize1 = js_user_py.replace('zh', 'z').replace('ch', 'c').replace('sh', 's')
        normalize2 = js_target_py.replace('zh', 'z').replace('ch', 'c').replace('sh', 's')
        
        # 完全匹配
        if normalize1 == normalize2:
            return True
        # 包含匹配
        if normalize1 in normalize2 or normalize2 in normalize1:
            return True
        return False
    
    # 测试用例
    test_cases = [
        ('jushishou', 'jushishou', True),
        ('jushishou', 'jushishouzi', True),  # 完整名 vs 简称
        ('shou', 'jushishou', False),  # 错误：只有"兽"
        ('jushi', 'jushishou', False),  # 错误：只有"石"
    ]
    
    for user_py, target_py, expected in test_cases:
        result = compare_pinyin(user_py, target_py)
        status = "✅" if result == expected else "❌"
        print(f"{status} 用户:{user_py} vs 目标:{target_py} -> {result} (期望:{expected})")
        
    print()

def test_user_speech_to_pinyin():
    """测试用户录音转拼音(本地库)"""
    print("=" * 50)
    print("测试4: 用户录音转拼音(本地pypinyin)")
    print("=" * 50)
    
    # 模拟用户说"菊石兽"
    user_texts = ['菊石兽', 'jushishou', '石兽', '兽']
    
    for text in user_texts:
        py = lazy_pinyin(text, style=Style.NORMAL)
        pinyin = ''.join(py)
        print(f"用户说'{text}' -> 拼音: {pinyin}")
    
    print()

def test_all_variants():
    """测试所有可能的正确拼音变体"""
    print("=" * 50)
    print("测试5: 菊石兽的所有正确拼音变体")
    print("=" * 50)
    
    cn_name = '菊石兽'
    
    # 使用不同风格获取拼音
    styles = [
        ('NORMAL', Style.NORMAL),
        ('TONE2', Style.TONE2),
        ('FINALS', Style.FINALS),
        ('INITIALS', Style.INITIALS),
    ]
    
    for name, style in styles:
        py = lazy_pinyin(cn_name, style=style)
        print(f"{name}: {py}")
    
    print()
    print("结论: 标准拼音是 jushishou")
    print("用户可能说: 菊石兽/jushishou/jushi shou 等")
    print()

def test_backend_api():
    """测试后端API返回"""
    import urllib.request
    import json
    
    print("=" * 50)
    print("测试6: 后端API验证")
    print("=" * 50)
    
    # 测试宝可梦名称拼音API
    url = 'http://localhost:5000/api/pokemon_names_pinyin'
    with urllib.request.urlopen(url, timeout=5) as response:
        data = json.loads(response.read())
        print(f"138号: {data.get('138')}")
        assert data.get('138') == 'jushishou', f"期望 jushishou，实际 {data.get('138')}"
    
    # 测试中文转拼音API
    import urllib.parse
    text = urllib.parse.quote('菊石兽')
    url = f'http://localhost:5000/api/chinese_to_pinyin?text={text}'
    with urllib.request.urlopen(url, timeout=5) as response:
        data = json.loads(response.read())
        print(f"中文转拼音 '菊石兽': {data.get('pinyin')}")
        # pypinyin返回 jushishou
    
    print("✅ 测试通过!\n")

if __name__ == '__main__':
    test_pinyin_basics()
    test_pinyin_api()
    test_compare_logic()
    test_user_speech_to_pinyin()
    test_all_variants()
    test_backend_api()  # 新增
    print("=" * 50)
    print("所有单元测试完成!")
    print("=" * 50)
