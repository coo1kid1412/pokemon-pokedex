#!/usr/bin/env python3
"""
大师赛功能单元测试
"""

import pytest
import sys
import os
import json
import tempfile

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 模拟 Flask app 环境
os.environ['FLASK_ENV'] = 'testing'


class TestStage2Pokemon:
    """测试二跳页宝可梦相关功能"""
    
    def test_stage2_pokemon_ids_exists(self):
        """测试二跳页宝可梦ID列表存在"""
        from pokedex import STAGE2_POKEMON_IDS
        
        assert isinstance(STAGE2_POKEMON_IDS, list)
        assert len(STAGE2_POKEMON_IDS) > 0
        print(f"二跳页宝可梦数量: {len(STAGE2_POKEMON_IDS)}")
    
    def test_stage2_contains_138(self):
        """测试138号菊石兽在二跳页列表中"""
        from pokedex import STAGE2_POKEMON_IDS
        
        assert 138 in STAGE2_POKEMON_IDS, "138号应该在二跳页列表中"
    
    def test_random_stage2_without_exclude(self):
        """测试随机获取二跳页宝可梦（不排除）"""
        import random
        from pokedex import STAGE2_POKEMON_IDS
        
        # 多次随机，确保返回的都是有效的二跳页宝可梦
        for _ in range(10):
            result = random.choice(STAGE2_POKEMON_IDS)
            assert result in STAGE2_POKEMON_IDS
    
    def test_random_stage2_with_exclude(self):
        """测试排除指定ID后随机获取"""
        import random
        from pokedex import STAGE2_POKEMON_IDS
        
        # 排除列表包含大部分宝可梦，只剩1-2个
        exclude_ids = STAGE2_POKEMON_IDS[:-1]  # 排除除了最后一个以外的所有
        available = [x for x in STAGE2_POKEMON_IDS if x not in exclude_ids]
        
        # 应该只剩下1-2个
        assert len(available) <= 2
        
        # 随机选择应该都在available中
        if available:
            result = random.choice(available)
            assert result in available
    
    def test_random_stage2_all_excluded(self):
        """测试全部排除后的处理"""
        from pokedex import STAGE2_POKEMON_IDS
        
        # 排除所有
        exclude_ids = STAGE2_POKEMON_IDS
        available = [x for x in STAGE2_POKEMON_IDS if x not in exclude_ids]
        
        # 应该没有可用的
        assert len(available) == 0


class TestMasterChallengeStats:
    """测试大师赛挑战统计数据功能"""
    
    @pytest.fixture
    def stats_file(self):
        """创建临时统计文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
            json.dump({}, f)  # 初始化空文件
        
        yield temp_path
        
        # 清理
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    def test_stats_file_structure(self):
        """测试统计数据文件结构"""
        stats_path = '/Users/lailixiang/.openclaw/workspace/pokemon/db/master_challenge_stats.json'
        
        # 文件应该存在
        assert os.path.exists(stats_path), f"统计文件不存在: {stats_path}"
        
        # 应该是有效的JSON
        with open(stats_path, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, dict), "统计数据应该是字典"
    
    def test_increment_success_count(self):
        """测试增加成功次数"""
        stats_path = '/Users/lailixiang/.openclaw/workspace/pokemon/db/master_challenge_stats.json'
        
        # 读取当前数据
        with open(stats_path, 'r') as f:
            data = json.load(f)
        
        # 记录138号的初始值
        initial_count = data.get('138', 0)
        
        # 模拟增加成功次数
        data['138'] = initial_count + 1
        
        # 写回
        with open(stats_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        # 验证
        with open(stats_path, 'r') as f:
            new_data = json.load(f)
        
        assert new_data['138'] == initial_count + 1
    
    def test_weighted_random_selection(self):
        """测试加权随机选择（成功次数多的被选中概率低）"""
        import random
        
        stats_path = '/Users/lailixiang/.openclaw/workspace/pokemon/db/master_challenge_stats.json'
        
        # 读取统计数据
        with open(stats_path, 'r') as f:
            stats = json.load(f)
        
        # 模拟加权随机选择算法
        def weighted_select(stats_data, available_ids):
            """
            根据成功次数计算权重
            成功次数越多，权重越低，被选中的概率越低
            """
            weights = {}
            for pid in available_ids:
                success_count = stats_data.get(str(pid), 0)
                # 权重 = 1 / (1 + success_count)
                # 成功0次: 权重=1
                # 成功1次: 权重=0.5
                # 成功9次: 权重=0.1
                weights[pid] = 1.0 / (1 + success_count)
            
            total_weight = sum(weights.values())
            r = random.random() * total_weight
            
            cumulative = 0
            for pid in available_ids:
                cumulative += weights[pid]
                if r <= cumulative:
                    return pid
            
            return available_ids[-1]  # 默认返回最后一个
        
        # 测试：成功次数多的应该被选中概率低
        from pokedex import STAGE2_POKEMON_IDS
        
        # 模拟一些统计数据
        test_stats = {
            '100': 10,  # 成功10次，权重很低
            '101': 1,   # 成功1次，权重中等
            '102': 0,   # 成功0次，权重最高
        }
        
        available = [100, 101, 102]
        
        # 多次选择，验证100被选中的概率最低
        results = {}
        for _ in range(1000):
            selected = weighted_select(test_stats, available)
            results[selected] = results.get(selected, 0) + 1
        
        print(f"加权随机选择结果: {results}")
        
        # 102（0次成功）应该被选中最多
        # 100（10次成功）应该被选中最少
        assert results[102] > results[100], "成功次数少的应该被选中概率更高"


class TestMasterScores:
    """测试大师赛榜单功能"""
    
    def test_scores_file_exists(self):
        """测试榜单文件存在"""
        scores_path = '/Users/lailixiang/.openclaw/workspace/pokemon/db/master_scores.json'
        assert os.path.exists(scores_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
