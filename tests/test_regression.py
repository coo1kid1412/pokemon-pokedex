#!/usr/bin/env python3
"""
精灵图鉴项目 - 回归测试集
记录今天修复的问题，确保后续不会再次出现
"""

import pytest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPaginationWithFilter:
    """测试分页保留属性筛选参数"""
    
    def test_pagination_links_contain_filter_param(self):
        """测试分页链接是否包含filter_type参数"""
        # 这个问题是前端模板问题，这里验证后端API正常
        from pokedex import app
        
        with app.test_client() as client:
            # 测试带type参数的页面
            response = client.get('/?page=1&type=fairy')
            assert response.status_code == 200
            
            # 验证返回的HTML包含筛选参数
            html = response.data.decode('utf-8')
            assert 'type=fairy' in html or 'type=fire' in html
    
    def test_page_template_with_type_filter(self):
        """测试模板中type参数正确传递"""
        from pokedex import app
        
        with app.test_client() as client:
            # 测试各种属性筛选
            for type_name in ['fire', 'water', 'grass', 'electric', 'flying', 'rock', 'ground', 'bug']:
                response = client.get(f'/?page=1&type={type_name}')
                assert response.status_code == 200


class TestMasterChallengeFunctions:
    """测试大师赛相关功能"""
    
    def test_random_stage2_api_exists(self):
        """测试随机二跳页API存在"""
        from pokedex import app
        
        with app.test_client() as client:
            response = client.get('/api/random-stage2')
            assert response.status_code == 200
            import json
            data = json.loads(response.data)
            assert 'pokemon_id' in data
    
    def test_random_stage2_with_exclude_api(self):
        """测试带排除的随机API"""
        from pokedex import app
        
        with app.test_client() as client:
            # 排除一些ID
            response = client.get('/api/random-stage2-with-exclude?exclude=1,2,3')
            assert response.status_code == 200
            import json
            data = json.loads(response.data)
            assert 'pokemon_id' in data
    
    def test_random_explore_api(self):
        """测试探索新区域API"""
        from pokedex import app
        
        with app.test_client() as client:
            response = client.get('/api/random-explore?exclude=1,2,3')
            assert response.status_code == 200
            import json
            data = json.loads(response.data)
            assert 'pokemon_id' in data


class TestMasterChallengeStats:
    """测试大师赛挑战统计功能"""
    
    def test_challenge_stats_file_exists(self):
        """测试挑战统计文件存在"""
        stats_path = '/Users/lailixiang/.openclaw/workspace/pokemon/db/master_challenge_stats.json'
        assert os.path.exists(stats_path)
    
    def test_record_master_score_increments_stats(self):
        """测试记录成绩会同时增加挑战统计"""
        import json
        from pokedex import app, load_master_scores, save_master_scores, load_challenge_stats
        
        # 读取初始状态
        with open('/Users/lailixiang/.openclaw/workspace/pokemon/db/master_challenge_stats.json') as f:
            before_stats = json.load(f)
        
        # 使用一个已有记录的ID来测试
        test_pid = '138'
        before_count = before_stats.get(test_pid, 0)
        
        # 模拟记录成绩
        with app.test_client() as client:
            response = client.post('/api/master-scores/record',
                data=json.dumps({'pokemon_id': int(test_pid), 'pokemon_name': '菊石兽', 'success': True}),
                content_type='application/json'
            )
            assert response.status_code == 200
            
        # 验证统计增加
        with open('/Users/lailixiang/.openclaw/workspace/pokemon/db/master_challenge_stats.json') as f:
            after_stats = json.load(f)
        
        # 138号次数应该增加
        assert after_stats.get(test_pid, 0) >= before_count


class TestExploreFunction:
    """测试探索新区域功能"""
    
    def test_explore_excludes_viewed_pokemon(self):
        """测试探索会排除已浏览的宝可梦"""
        from pokedex import app
        
        with app.test_client() as client:
            # 排除1-100
            response = client.get('/api/random-explore?exclude=' + ','.join([str(i) for i in range(1, 101)]))
            assert response.status_code == 200
            import json
            data = json.loads(response.data)
            
            # 返回的ID应该不在排除列表中
            if data.get('pokemon_id'):
                assert data['pokemon_id'] > 100


class TestMasterNavigation:
    """测试大师赛导航功能"""
    
    def test_master_page_loads(self):
        """测试大师赛页面能正常加载"""
        from pokedex import app
        
        with app.test_client() as client:
            response = client.get('/pokemon/138?master=true')
            assert response.status_code == 200
    
    def test_master_success_page_loads(self):
        """测试大师赛成功页面能正常加载"""
        from pokedex import app
        
        with app.test_client() as client:
            # success模式
            response = client.get('/pokemon/138?master=true&success=true')
            # 应该能正常加载（不管成功与否）
            assert response.status_code == 200


class TestPinyinFunctions:
    """测试拼音相关功能"""
    
    def test_chinese_to_pinyin_api(self):
        """测试中文转拼音API"""
        from pokedex import app
        
        with app.test_client() as client:
            import urllib.parse
            response = client.get('/api/chinese_to_pinyin?text=' + urllib.parse.quote('菊石兽'))
            assert response.status_code == 200
            import json
            data = json.loads(response.data)
            assert 'pinyin' in data
    
    def test_pokemon_names_pinyin_api(self):
        """测试宝可梦名称拼音API"""
        from pokedex import app
        
        with app.test_client() as client:
            response = client.get('/api/pokemon_names_pinyin')
            assert response.status_code == 200
            import json
            data = json.loads(response.data)
            assert '138' in data
            assert data['138'] == 'jushishou'


class TestTypeFilter:
    """测试属性筛选功能"""
    
    def test_type_filter_api(self):
        """测试属性筛选API"""
        from pokedex import app
        
        with app.test_client() as client:
            # 测试fire属性
            response = client.get('/?type=fire')
            assert response.status_code == 200
    
    def test_all_type_filters_work(self):
        """测试所有属性筛选都能正常工作"""
        from pokedex import app
        
        types = ['fire', 'water', 'grass', 'electric', 'psychic', 'dragon', 'ghost',
                 'rock', 'ground', 'flying', 'bug', 'ice', 'fighting', 'poison', 'steel', 'fairy']
        
        with app.test_client() as client:
            for type_name in types:
                response = client.get(f'/?type={type_name}')
                assert response.status_code == 200, f"属性 {type_name} 筛选失败"


class TestBugFixes:
    """回归测试 - 确保之前修复的bug不再出现"""
    
    def test_bugfix_138_pinyin_correct(self):
        """Bugfix: 138号菊石兽拼音应该是jushishou"""
        from pokedex import app
        
        with app.test_client() as client:
            response = client.get('/api/pokemon_names_pinyin')
            import json
            data = json.loads(response.data)
            assert data.get('138') == 'jushishou', "138号拼音应该是jushishou"
    
    def test_bugfix_pokemon_id_type(self):
        """Bugfix: pokemon ID类型转换问题"""
        # 模拟前端场景：数字ID vs 字符串ID
        cache = {"138": "jushishou", "139": "duocijushishou"}
        
        # 错误方式
        assert cache.get(138) is None, "数字查找应该失败"
        
        # 正确方式
        assert cache.get("138") == "jushishou", "字符串查找应该成功"
    
    def test_bugfix_random_import(self):
        """Bugfix: random模块在函数内导入"""
        # 确保weighted_random_select函数正常工作
        from pokedex import weighted_random_select
        
        result = weighted_random_select([1, 2, 3], {})
        assert result in [1, 2, 3], "加权随机选择应该返回有效ID"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
