#!/usr/bin/env python3
"""
大师赛加权随机选择功能单元测试
"""

import pytest
import sys
import os
import json
import tempfile
import random

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestWeightedRandomSelect:
    """测试加权随机选择功能"""
    
    def test_weighted_random_select_function(self):
        """测试加权随机选择函数存在且正确"""
        from pokedex import weighted_random_select, load_challenge_stats
        
        # 测试用例：3个宝可梦，不同成功次数
        available_ids = [100, 101, 102]
        stats = {
            '100': 10,  # 成功10次，权重很低
            '101': 1,   # 成功1次，权重中等
            '102': 0,   # 成功0次，权重最高
        }
        
        # 多次选择，验证概率分布
        results = {}
        for _ in range(1000):
            selected = weighted_random_select(available_ids, stats)
            results[selected] = results.get(selected, 0) + 1
        
        print(f"加权随机选择结果: {results}")
        
        # 102（0次成功）应该被选中最多
        # 100（10次成功）应该被选中最少
        assert results[102] > results[100], "成功次数少的应该被选中概率更高"
        assert results[102] > results[101], "成功0次 > 成功1次"
    
    def test_weighted_select_empty_list(self):
        """测试空列表处理"""
        from pokedex import weighted_random_select
        
        result = weighted_random_select([], {})
        assert result is None
    
    def test_weighted_select_no_stats(self):
        """测试无统计数据时（全部权重为1）"""
        from pokedex import weighted_random_select
        
        available_ids = [100, 101, 102]
        stats = {}
        
        # 无统计时权重都是1，应该随机
        results = {}
        for _ in range(100):
            selected = weighted_random_select(available_ids, stats)
            results[selected] = results.get(selected, 0) + 1
        
        # 3个都应该被选中
        assert len(results) == 3
    
    def test_load_save_challenge_stats(self):
        """测试统计数据的加载和保存"""
        from pokedex import load_challenge_stats, save_challenge_stats, increment_success_count, MASTER_CHALLENGE_STATS_FILE
        
        # 创建临时测试文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
            json.dump({}, f)
        
        # 临时修改路径
        import pokedex
        original_path = pokedex.MASTER_CHALLENGE_STATS_FILE
        pokedex.MASTER_CHALLENGE_STATS_FILE = temp_path
        
        try:
            # 测试增加成功次数
            count = increment_success_count(999)
            assert count == 1
            
            # 再次增加
            count = increment_success_count(999)
            assert count == 2
            
            # 验证
            stats = load_challenge_stats()
            assert stats.get('999') == 2
            
        finally:
            # 恢复原路径
            pokedex.MASTER_CHALLENGE_STATS_FILE = original_path
            # 清理
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def test_integration_with_api(self):
        """测试加权随机选择与API集成"""
        from pokedex import weighted_random_select, load_challenge_stats, STAGE2_POKEMON_IDS
        
        # 模拟已存在的挑战记录
        available_ids = STAGE2_POKEMON_IDS[:10]  # 取前10个
        
        # 模拟：第一个成功9次，其他成功0次
        stats = {str(available_ids[0]): 9}
        for pid in available_ids[1:]:
            stats[str(pid)] = 0
        
        # 多次选择
        results = {}
        for _ in range(500):
            selected = weighted_random_select(available_ids, stats)
            results[selected] = results.get(selected, 0) + 1
        
        # 第一个（成功9次）应该被选中最少
        first_count = results.get(available_ids[0], 0)
        second_count = results.get(available_ids[1], 0)
        
        print(f"成功9次被选中: {first_count}, 成功0次被选中: {second_count}")
        
        # 加权后的概率：成功0次的权重是1，成功9次的权重是0.1
        # 所以成功0次被选中的概率应该明显更高
        assert second_count > first_count, "成功0次应该比成功9次被选中概率高"


class TestMasterChallengeFlow:
    """测试大师赛挑战完整流程"""
    
    def test_challenge_stats_file_exists(self):
        """测试挑战统计文件存在"""
        stats_path = '/Users/lailixiang/.openclaw/workspace/pokemon/db/master_challenge_stats.json'
        assert os.path.exists(stats_path), f"统计文件不存在: {stats_path}"
        
        # 验证是有效JSON
        with open(stats_path, 'r') as f:
            data = json.load(f)
        assert isinstance(data, dict)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
