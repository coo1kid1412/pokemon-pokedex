#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
宝可梦图鉴 Web 应用 - 性能优化版 v2
针对详情页加载速度优化

优化点：
1. 并发API请求 - 使用线程池并发获取
2. 减少技能API调用 - 从20个减少到8个，不获取中文名
3. 预加载热门宝可梦详情 - 首页加载时后台预获取
4. 本地缓存优化 - 更激进的缓存策略
"""

import json
import os
import urllib.request
import ssl
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, render_template, request, send_from_directory, abort, make_response, jsonify

# 导入中文名称 - 使用完整的1008个中文名称
import sys
sys.path.insert(0, '/Users/lailixiang/.openclaw/workspace/pokemon')
try:
    from pokemon_names_cn_full import POKEMON_NAMES_CN
except ImportError:
    from pokemon_cn import POKEMON_NAMES_CN

app = Flask(__name__)

# 配置
POKEMON_DB_PATH = '/Users/lailixiang/.openclaw/workspace/pokemon/db/pokemons.json'
POKEMONS_PER_PAGE = 30
SPRITE_DIR = '/Users/lailixiang/.openclaw/workspace/scripts/static/sprites'
SPRITE_URL_BASE = '/static/sprites'

# 名称语音 TTS 配置
TTS_DIR = '/Users/lailixiang/.openclaw/workspace/scripts/static/tts'
TTS_URL_BASE = '/static/tts'

# 线程池用于并发API请求
EXECUTOR = ThreadPoolExecutor(max_workers=10)

# 确保精灵图目录存在
os.makedirs(SPRITE_DIR, exist_ok=True)
os.makedirs(TTS_DIR, exist_ok=True)

# SSL 上下文
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

# 类型颜色配置
TYPE_COLORS = {
    'normal': '#A8A878', 'fire': '#F08030', 'water': '#6890F0', 'electric': '#F8D030',
    'grass': '#78C850', 'ice': '#98D8D8', 'fighting': '#C03028', 'poison': '#A040A0',
    'ground': '#E0C068', 'flying': '#A890F0', 'psychic': '#F85888', 'bug': '#A8B820',
    'rock': '#B8A038', 'ghost': '#705898', 'dragon': '#7038F8', 'dark': '#705848',
    'steel': '#B8B8D0', 'fairy': '#EE99AC',
}

TYPE_NAMES_CN = {
    'normal': '普通', 'fire': '火', 'water': '水', 'electric': '电', 'grass': '草',
    'ice': '冰', 'fighting': '格斗', 'poison': '毒', 'ground': '地面', 'flying': '飞行',
    'psychic': '超能', 'bug': '虫', 'rock': '岩石', 'ghost': '幽灵', 'dragon': '龙',
    'dark': '恶', 'steel': '钢', 'fairy': '妖精',
}

# ============ 本地化中文名称（减少API调用）===========
# 常用特性中文名映射 - 预置常见特性
ABILITY_NAMES_CN = {
    # 完整特性中文映射（280个）
    'adaptability': '适应力', 'aftermath': '后效', 'air-lock': '气闸', 'analytic': '分析',
    'anger-point': '愤怒穴位', 'anger-shell': '愤怒外壳', 'anticipation': '预知', 'arena-trap': 'arena陷阱',
    'armor-tail': '装甲尾巴', 'aroma-veil': '芳香幕', 'aura-break': '气场破坏', 'bad-dreams': '噩梦',
    'ball-fetch': '捡球', 'battery': '电池', 'battle-armor': '战斗装甲', 'beads-of-ruin': '破坏之珠',
    'beast-boost': '野兽boost', 'berserk': 'Berserk', 'big-pecks': '大喙', 'blaze': '猛火',
    'bulletproof': '防弹', 'cheek-pouch': '颊袋', 'chilling-neigh': '寒冷嘶鸣', 'chlorophyll': '叶绿素',
    'clear-body': '透明身体', 'cloud-nine': '无关天气', 'color-change': '变色', 'comatose': '睡眠',
    'commander': '指挥官', 'competitive': '斗争心', 'compound-eyes': '复眼', 'contrary': '相反',
    'corrosion': '腐蚀', 'costar': '搭档', 'cotton-down': '棉絮', 'cursed-body': '诅咒身体',
    'cute-charm': '迷人之躯', 'damp': '潮湿', 'dancer': '舞者', 'dark-aura': '恶气场',
    'dauntless-shield': '无畏护盾', 'dazzling': '闪光', 'defeatist': '失败者', 'defiant': '愤怒穴位',
    'disguise': '伪装', 'download': '下载', 'dragons-maw': '龙之颚', 'drizzle': '降雨',
    'drought': '干旱', 'dry-skin': '干燥皮肤', 'early-bird': '早起', 'earth-eater': '食土者',
    'effect-spore': '孢子', 'electric-surge': '电气场地', 'electromorphosis': '电形态', 'emergency-exit': '紧急退出',
    'fairy-aura': '妖精气场', 'filter': '过滤器', 'flame-body': '火焰之躯', 'flare-boost': '火焰boost',
    'flash-fire': '引火', 'flower-gift': '花之礼', 'flower-veil': '花幕', 'fluffy': '绒毛',
    'forecast': '预报', 'forewarn': '警告', 'friend-guard': '友爱', 'frisk': '察觉',
    'full-metal-body': '全金属身体', 'fur-coat': '毛皮大衣', 'gale-wings': '风之翼', 'gluttony': '贪吃鬼',
    'good-as-gold': '如金', 'gooey': '黏滑', 'grass-pelt': '草皮', 'grassy-surge': '青草场地',
    'grim-neigh': '恐怖嘶鸣', 'guard-dog': '看门狗', 'gulp-missile': '吞食导弹', 'guts': '根性',
    'hadron-engine': '强子引擎', 'harvest': '收获', 'healer': '治愈之心', 'heatproof': '耐热',
    'heavy-metal': '重金属', 'honey-gather': '采蜜', 'huge-power': '巨大力量', 'hunger-switch': '饥饿转换',
    'hustle': '活力', 'hydration': '水合作用', 'hyper-cutter': '怪力钳', 'ice-body': '冰冻之躯',
    'ice-face': '冰面孔', 'ice-scales': '冰鳞片', 'illuminate': '发光', 'illusion': '幻觉',
    'immunity': '免疫', 'imposter': '模仿', 'infiltrator': '穿透', 'innards-out': '内脏外露',
    'inner-focus': '精神力', 'insomnia': '失眠', 'intimidate': '威吓', 'intrepid-sword': '无畏之剑',
    'iron-barbs': '铁刺', 'iron-fist': '铁拳', 'justified': '正义之心', 'keen-eye': '锐利目光',
    'klutz': '笨拙', 'leaf-guard': '叶子防守', 'levitate': '漂浮', 'libero': '自由者',
    'light-metal': '轻金属', 'lightning-rod': '引电', 'limber': '柔软', 'lingering-aroma': ' lingering aroma',
    'liquid-ooze': '液体ooze', 'liquid-voice': '湿润声', 'long-reach': '长臂', 'magic-bounce': '魔法反弹',
    'magic-guard': '魔法守护', 'magician': '魔术师', 'magma-armor': '熔岩装甲', 'magnet-pull': '磁力吸引',
    'marvel-scale': '奇异鳞片', 'mega-launcher': 'mega launcher', 'merciless': '无情', 'minus': '负',
    'mirror-armor': '镜甲', 'misty-surge': '薄雾场地', 'mold-breaker': '变形蛋', 'moody': '情绪化',
    'motor-drive': '马达驱动', 'moxie': '自信', 'multiscale': '多重鳞片', 'multitype': '多种形态',
    'mummy': '木乃伊', 'mycelium-might': '菌丝之力', 'natural-cure': '自然回复', 'neutralizing-gas': '中和气体',
    'no-guard': '无防守', 'normalize': '正规化', 'oblivious': '迟钝', 'opportunist': '机会主义者',
    'orichalcum-pulse': '俄瑞克脉冲', 'overcoat': '外套', 'overgrow': '茂盛', 'own-tempo': '我行我素',
    'perish-body': '灭亡身体', 'pickpocket': '偷盗', 'pickup': '拾取', 'pixilate': '像素化',
    'plus': '正', 'poison-heal': '毒疗', 'poison-point': '毒针', 'poison-touch': '毒手',
    'power-construct': '力量构造', 'power-spot': '力量点', 'prankster': '恶作剧', 'pressure': '压迫感',
    'prism-armor': '棱镜装甲', 'propeller-tail': '螺旋尾巴', 'protean': '百变', 'protosynthesis': '原合成',
    'psychic-surge': '超能场地', 'punk-rock': '庞克摇滚', 'pure-power': '纯力量', 'purifying-salt': '净化盐',
    'quark-drive': '夸克驱动', 'queenly-majesty': '女王威严', 'quick-feet': '快脚', 'rain-dish': '雨盘',
    'rattled': '胆怯', 'receiver': '接收者', 'reckless': '舍身', 'refrigerate': '冷藏',
    'regenerator': '再生力', 'ripen': '成熟', 'rivalry': '斗争心', 'rks-system': 'rks系统',
    'rock-head': '石头脑袋', 'rocky-payload': '岩石载荷', 'rough-skin': '粗糙皮肤', 'run-away': '逃跑',
    'sand-force': '沙力量', 'sand-rush': '沙速', 'sand-spit': '沙喷', 'sand-stream': '沙暴',
    'sand-veil': '沙帘', 'sap-sipper': '吸盘', 'schooling': '鱼群', 'scrappy': '不屈之心',
    'screen-cleaner': '屏幕清洁', 'seed-sower': '种子播种', 'serene-grace': '优雅', 'shadow-shield': '影子盾牌',
    'shadow-tag': '阴影追踪', 'sharpness': '锋利', 'shed-skin': '蜕皮', 'sheer-force': '强行',
    'shell-armor': '硬壳甲', 'shield-dust': '鳞粉', 'shields-down': '盾牌下降', 'simple': '单纯',
    'skill-link': '技能连接', 'slow-start': '慢启动', 'slush-rush': '雪速', 'sniper': '狙击手',
    'snow-cloak': '雪伪装', 'snow-warning': '降雪', 'solar-power': '太阳能', 'solid-rock': '坚硬岩石',
    'soul-heart': '精神之心', 'soundproof': '隔音', 'speed-boost': '加速', 'stakeout': '监视',
    'stall': '懒散', 'stalwart': '坚定', 'stamina': '耐力', 'stance-change': '姿态改变',
    'static': '静电', 'steadfast': '不屈', 'steam-engine': '蒸汽引擎', 'steelworker': '钢能力者',
    'steely-spirit': '钢之精神', 'stench': '恶臭', 'sticky-hold': '黏着', 'storm-drain': '排水',
    'strong-jaw': '强颚', 'sturdy': '结实', 'suction-cups': '吸盘', 'super-luck': '超幸运',
    'supreme-overlord': '至高霸王', 'swarm': '虫之预感', 'sweet-veil': '甜蜜幕', 'swift-swim': '悠游自如',
    'sword-of-ruin': '破坏之剑', 'symbiosis': '共生', 'synchronize': '同步率', 'tablets-of-ruin': '破坏之板',
    'tangled-feet': '蹩脚', 'technician': '技术员', 'telepathy': '心电感应', 'teravolt': 'Teravolt',
    'thermal-exchange': '热交换', 'thick-fat': '厚脂肪', 'tinted-lens': '有色镜片', 'torrent': '激流',
    'tough-claws': '硬爪子', 'toxic-boost': '毒boost', 'toxic-debris': '毒碎片', 'trace': '追踪',
    'transistor': '晶体管', 'triage': '治疗', 'truant': '逃学', 'turboblaze': 'Turboblaze',
    'unaware': '无意识', 'unburden': '负担减轻', 'unnerve': '紧张感', 'unseen-fist': '无形拳',
    'vessel-of-ruin': '破坏之器', 'victory-star': '胜利之星', 'vital-spirit': '活力', 'volt-absorb': '储电',
    'wandering-spirit': '流浪精神', 'water-absorb': '储水', 'water-bubble': '水泡', 'water-compaction': '水压实',
    'water-veil': '水幕', 'weak-armor': '脆弱装甲', 'well-baked-body': '烘焙身体', 'white-smoke': '白烟',
    'wimp-out': '懦弱', 'wind-power': '风能', 'wind-rider': '风骑士', 'wonder-guard': '奇迹守护',
    'wonder-skin': '奇迹皮肤', 'zen-mode': '禅模式', 'zero-to-hero': '从零到英雄',
}

# 常用技能中文名映射 - 预置常见技能
MOVE_NAMES_CN = {
    # 第一代技能 - 完整修正版
    'tackle': '撞击', 'vine-whip': '藤鞭', 'razor-leaf': '飞叶快刀', 'growl': '叫声',
    'scratch': '抓', 'ember': '火花', 'flamethrower': '烈焰喷射', 'water-gun': '水枪',
    'hydro-pump': '水炮', 'thunder-shock': '电击', 'thunderbolt': '十万伏特', 'quick-attack': '电光一闪',
    'tail-whip': '摇尾巴', 'bite': '咬', 'dragon-breath': '龙息', 'submission': '地狱',
    'mega-kick': '百万吨飞腿', 'hyper-beam': '破坏光线', 'earthquake': '地震', 'rock-slide': '岩崩',
    'shadow-ball': '暗影球', 'sludge-bomb': '污泥炸弹', 'fire-spin': '火焰旋涡', 'confuse-ray': '困惑之光',
    'hypnosis': '催眠术', 'dream-eater': '食梦', 'psychic': '精神干扰', 'psyshock': '精神冲击',
    'rest': '睡觉', 'recover': '回复', 'substitute': '替身', 'protect': '保护',
    'swords-dance': '剑舞', 'dragon-dance': '龙舞', 'calm-mind': '冥想', 'toxic': '剧毒',
    'will-o-wisp': '鬼火', 'double-team': '影分身', 'minimize': '变小', 'swagger': '虚张声势',
    'attract': '诱惑', 'facade': '看穿', 'brick-break': '臂锤', 'aerial-ace': '燕返',
    'iron-tail': '铁尾', 'steel-wing': '钢翼', 'roost': '栖息', 'brave-bird': '猛攻',
    'flare-blitz': '闪焰冲锋', 'close-combat': '近身战', 'extremespeed': '神速', 'outrage': '逆鳞',
    'dragon-claw': '龙爪', 'crunch': '咬碎', 'play-rough': '嬉闹', 'drain-punch': '吸取拳',
    'focus-blast': '真气弹', 'flash-cannon': '加农光炮', 'ice-beam': '冰冻光束', 'blizzard': '暴风雪',
    'surf': '冲浪', 'scald': '热水', 'ice-fang': '冰牙', 'fire-fang': '火牙',
    'thunder-fang': '雷牙', 'poison-jab': '毒击', 'cross-poison': '毒十字', 'sludge-wave': '污泥波',
    'giga-impact': '终极冲击', 'hyper-voice': '巨声', 'bolt-strike': '电光冲击', 'blue-flare': '蓝焰',
    'fusion-flare': '融合flare', 'fusion-bolt': '融合bolt', 'v-create': 'V热焰', 'bolt-beak': '电喙',
    'fishious-rend': '啃咬', 'clanging-scales': '鳞片作响', 'scale-shot': '鳞片射击', 'meteor-assault': '流星坠落',
    'eternabeam': '无尽光束', 'dynamax-cannon': '极光炮', 'snipe-shot': '狙击', 'jet-punch': '喷射拳',
    'collision-course': '冲撞', 'expand-force': '势力', 'spin-out': '旋转', 'wicked-blow': '恶意追击',
    'soul-crisis': '灵魂冲击', 'crisis-power': '危机力量', 'shell-side-arm': '贝壳刃', 'magnet-rise': '磁悬浮',
    'electro-shot': '电光石火', 'particle-ion': '粒子炮', 'galactic-order': '银河秩序', 'prismatic-laser': '棱镜激光',
    'spectral-thief': '暗影偷盗', 'sunny-day': '大晴天', 'rain-dance': '求雨', 'hail': '冰雹',
    'sandstorm': '沙暴', 'stealth-rock': '隐形岩', 'spikes': '毒菱', 'toxic-spikes': '毒菱',
    'defog': '清雾', 'court-change': '场地交换', 'trick-room': '戏法空间', 'wonder-room': '奇妙空间',
    'magic-room': '魔法空间', 'grassy-terrain': '青草场地', 'electric-terrain': '电气场地', 'misty-terrain': '薄雾场地',
    'reflect': '光墙', 'light-screen': '反射壁', 'safeguard': '神秘守护', 'mist': '白雾',
    'aurora-veil': '极光幕', 'aqua-ring': '水环', 'aqua-boost': '水之加速', 'curse': '诅咒',
    'stockpile': '蓄力', 'spit-up': '吐出', 'swallow': '吞咽', 'belly-drum': '腹鼓',
    'fling': '投掷', 'endure': '忍耐', 'endeavor': '搏命', 'reversal': '反打',
    'flail': '挣扎', 'false-swipe': '蜻蜓点水', 'charge': '充电', 'terrain-pulse': '地形脉冲',
    # 第二代及以后常见技能
    'razor-wind': '旋风', 'cut': '剪切', 'bind': '绑紧', 'headbutt': '头锤', 'body-slam': '重压',
    'take-down': '猛撞', 'thrash': '乱打', 'double-edge': '舍身撞击', 'peck': '啄',
    'fury-attack': '连斩', 'drill-peck': '钻孔', 'poison-sting': '毒针', 'twineedle': '双针',
    'pin-missile': '飞弹针', 'leech-life': '吸血', 'spore': '孢子', 'sleep-powder': '睡眠粉',
    'stun-spore': '麻痹粉', 'petal-dance': '花瓣舞', 'mega-drain': '超级吸取', 'absorb': '吸取',
    'mega-punch': '百万吨重拳', 'pay-day': '聚宝盆', 'fire-punch': '火焰拳', 'ice-punch': '冰冻拳',
    'thunder-punch': '雷电拳', 'slam': '摔打', 'wrap': '缠绕', 'stomp': '踩踏',
    'double-kick': '二连踢', 'jump-kick': '跳踢', 'rolling-kick': '回旋踢', 'kick': '踢',
    'head-smash': '碎岩', 'feint-attack': '佯攻', 'flame-wheel': '火焰轮', 'inferno': '喷火',
    'fire-blast': '火焰爆发', 'water-sport': '玩水', 'clamp': '贝壳夹', 'whirlpool': '漩涡',
    'bubble-beam': '泡沫光线', 'octazooka': '章鱼桶', 'spider-web': '蛛网', 'bug-buzz': '虫鸣',
    'signal-beam': '信号光', 'x-scissor': '十字剪', 'night-slash': '暗袭要害', 'shadow-claw': '暗影爪',
    'shadow-sneak': '影子偷窃', 'ominous-wind': '邪风', 'air-slash': '空气斩', 'acrobatics': '杂技',
    'pluck': '衔取', 'u-turn': 'UTurn', 'assurance': '必定命中', 'avalanche': '雪崩',
    'gyro-ball': '陀螺球', 'metal-burst': '金属爆炸', 'revenge': '复仇', 'rock-tomb': '岩石封闭',
    'rock-blast': '岩石爆破', 'power-gem': '力量宝石', 'mach-punch': '音速拳', 'vacuum-wave': '真空波',
    'force-palm': '掌打', 'storm-throw': '碎击', 'circle-throw': '过肩摔', 'low-sweep': '下踢',
    'foul-play': '欺诈', 'dark-pulse': '恶波动', 'night-burst': '暗夜爆裂', 'cruel-wind': '残酷风',
    'phantom-force': '幻影', 'power-shift': '力量转换', 'lava-plume': '喷烟', 'fire-lash': '火焰鞭',
    'inferno-overdrive': '过热', 'hydro-cannon': '水加农', 'return': '返回', 'frustration': '挫败',
    'pain-split': '分担痛楚', 'wish': '祈愿', 'heal-bell': '治愈铃', 'refresh': '焕新',
    'grudge': '怨恨', 'mimic': '模仿', 'cosmic-power': '宇宙力量', 'amnesia': '记忆',
    'kinesis': '折返', 'telekinesis': '念力', 'guard-split': '防御分割', 'power-split': '力量分割',
    'role-play': '扮演', 'gravity': '重力', 'healing-wish': '治愈愿望', 'heal-order': '治愈指令',
    'recoil': '后座力', 'struggle': '挣扎', 'sketch': '写生', 'destiny-bond': '同命',
    'perish-song': '灭亡之歌', 'sticky-web': '黏黏网', 'covet': '渴望', 'crabhammer': '蟹钳锤',
    'cross-chop': '十字劈', 'detect': '见切', 'bone-club': '骨棒', 'bone-rush': '骨击',
    'bonemerang': '骨回飞', 'drill-run': '钻刺', 'fury-swipes': '乱抓', 'horn-attack': '角攻击',
    'horn-drill': '角钻', 'tri-attack': '三角攻击', 'super-fang': '超级牙', 'slash': '切',
    'clamp': '夹', 'constrict': '压缩', 'conversion': '变换', 'conversion2': '变换2',
    'counter': '反击', 'dig': '挖洞', 'disable': '禁止', 'dizzy-punch': '眩晕拳',
    'double-slap': '连环腿', 'dragon-rage': '龙之愤怒', 'dragon-rush': '龙卷风', 'dynamic-punch': '爆裂拳',
    'egg-bomb': '炸弹', 'explosion': '大爆炸', 'extrasensory': '神通力', 'faint-attack': '暗算',
    'feather-dance': '羽毛舞', 'fly': '飞翔', 'flying-press': '飞翔', 'focus-punch': '聚气',
    'follow-me': '帮我', 'foresight': '看破', 'glare': '刺耳声', 'growth': '生长',
    'guilt-trip': '内疚', 'gust': '起风', 'harden': '变硬', 'haze': '黑雾',
    'heal-block': '回复封锁', 'heal-pulse': '治愈波动', 'heat-crash': '热压', 'heavy-slam': '重击',
    'imprison': '封印', 'iron-defense': '铁壁', 'iron-head': '铁头', 'judgment': '审判',
    'karate-chop': '手刀', 'knock-off': '拍落', 'last-resort': '搏命', 'leaf-blade': '叶刃',
    'leaf-storm': '叶绿风暴', 'leech-seed': '种子', 'lick': '舌舔', 'lock-on': '锁定',
    'lovely-kiss': '艳红', 'low-kick': '过肩摔', 'mach-claw': '音速', 'meditate': '冥想',
    'megaphone': '巨声', 'metal-claw': '金属爪', 'metronome': '促进', 'milk-drink': '喝奶',
    'mirror-coat': '镜光', 'mirror-move': '鹦鹉学舌', 'moonblast': '月球冲击', 'moonlight': '月光',
    'morning-sun': '晨光', 'mud-slap': '泥巴', 'muddy-water': '浊流', 'nasty-plot': '阴谋',
    'nature-power': '自然力量', 'needle-arm': '尖刺臂', 'nightmare': '噩梦', 'night-shade': '黑夜',
    'odor-sleuth': '气味', 'paleo-wave': '古代波', 'parabolic-charge': '抛物线充电', 'payback': ' payback',
    'petal-blizzard': '花瓣', 'pin-missile': '飞针', 'plasma-fist': '等离子', 'play-nice': '友好',
    'poison-fang': '毒牙', 'poison-tail': '毒尾', 'pollen-puff': '花粉', 'population-crush': '群体',
    'powder': '粉末', 'power-trip': '力量', 'power-whip': '强力鞭打', 'present': '礼物',
    'psybeam': '精神光线', 'psycho-cut': '精神之刃', 'psycho-boost': '精神提升', 'punishment': '惩罚',
    'rage': '愤怒', 'rage-powder': '愤怒粉末', 'rapid-spin': '高速旋转', 'recycle': '回收',
    'roar': '吼叫', 'rock-climb': '攀岩', 'rock-smash': '碎岩', 'rock-throw': '投石',
    'rollout': '滚动', 'sacred-fire': '圣火', 'sand-attack': '泼沙', 'scary-face': '恐怖脸',
    'screech': '刺耳', 'seismic-toss': '过肩摔', 'self-destruct': '自爆', 'shadow-force': '暗影',
    'sharpen': '磨砺', 'sheer-cold': '绝对零度', 'shock-wave': '电击波', 'silver-wind': '银风',
    'sing': '唱歌', 'skull-bash': '火箭头锤', 'sky-attack': '飞翔', 'slack-off': '偷懒',
    'smack-down': '敲打', 'smell': '气味', 'smog': '烟雾', 'smoke-screen': '烟幕',
    'snore': '打鼾', 'soak': '浸水', 'soft-boiled': '温泉', 'solar-beam': '日光束',
    'sonic-boom': '音爆', 'spacial-rend': '空间', 'spark': '电光', 'spike-cannon': '尖刺',
    'spite': '怨恨', 'splash': '跃起', 'steam-roller': '压路机', 'stockpile': '储藏',
    'stone-edge': '石刃', 'stored-power': '聚气', 'strength': '怪力', 'string-shot': '吐丝',
    'stun-spore': '粉末', 'substitute': '替身', 'sucker-punch': '偷袭', 'superpower': '怪力',
    'supersonic': '超声波', 'sweet-kiss': '甜吻', 'sweet-scent': '甜甜', 'swift': '电光',
    'switcheroo': '交换', 'synthesis': '光合作用', 'tail-glow': '萤光', 'taunt': '挑衅',
    'tearful-look': '泪眼', 'techno-blast': '科技', 'teleport': '瞬间移动', 'thief': '小偷',
    'thrash': '暴动', 'thunder-wave': '电磁波', 'thunder': '雷电', 'tickle': '挠痒',
    'topsy-turvy': '颠覆', 'torment': '折磨', 'transform': '变身', 'triple-kick': '三连踢',
    'trump-card': '王牌', 'twister': '龙卷', 'uproar': '喧哗', 'vacuum-wave': '真空波',
    'venoshock': '毒液', 'vice-grip': '夹', 'vital-throw': '背摔', 'volt-tackle': '电光石火',
    'water-fall': '瀑布', 'water-pulse': '水波动', 'water-spout': '水喷', 'weather-ball': '气象球',
    'wide-guard': '广域防守', 'wild-charge': '疯狂伏特', 'wind-attack': '风力', 'wing-attack': '翅膀',
    'wonder-launcher': '神秘', 'work-up': '自我激励', 'worry-seed': '寄生种子', 'yawn': '哈欠',
    'zap-cannon': '电磁炮', 'zen-headbutt': '意念头锤',
    # 更多第八九代技能
    'aura-wheel': '气场轮', 'beak-blast': '鸟嘴爆', 'blood-moon': '血月', 'break-glass': '碎玻璃',
    'burning-jealousy': '嫉妒之火', 'clangorous-soul': '灵魂共鸣', 'court-change': '场地交换',
    'dragon-darts': '龙之镖', 'draco-meteor': '龙星群', 'dynamax-cannon': '极光炮',
    'eclipse': '日食', 'energy-ball': '能源球', 'everlasting': '永恒', 'false-surrender': '虚假投降',
    'fiery-wrath': '怒火', 'fishious-rend': '咬碎', 'freezing-glare': '冰冻目光', 'glacial-lance': '冰枪',
    'glaive-rush': '长刀冲击', 'grav-ball': '重力球', 'head-long': '头锤', 'hollywood-jaw': '好莱坞',
    'infinite-rotation': '无限旋转', 'jungle-healing': '丛林治疗', 'lunar-blessing': '月之祝福',
    'make-it-rain': '倾盆雨', 'meteor-beam': '流星光束', 'mirror-coat': '镜光', 'mountain-gale': '山崩',
    'oceanic-operetta': '海洋协奏曲', 'overdrive': '超音速', 'photon-geyser': '光子溅射',
    'playrough': '嬉闹', 'powder-snow': '粉末雪', 'power-gem': '力量宝石', 'prismatic-laser': '棱镜激光',
    'psychic-fangs': '精神之牙', 'psystrike': '精神冲击', 'pyro-ball': '火球', 'quash': '粉碎',
    'razor-shell': '贝壳刃', 'recover': '回复', 'rising-voltage': '上升电压', 'roost': '栖息',
    'salt-cure': '盐疗', 'scaleshot': '鳞片射击', 'shell-trap': '贝壳陷阱', 'shelter': '避难',
    'shitestorm': '粪便风暴', 'sizzle-strike': '热烤', 'stone-axe': '石斧', 'storm-throw': '碎击',
    'sun-strike': '烈日冲击', 'tar-shot': '焦油射击', 'tearful-look': '泪眼', 'tera-blast': '太晶爆发',
    'thunder-clap': '雷电掌声', 'thunder-cage': '雷电囚笼', 'thunderous-kick': '雷鸣脚', 'trailblaze': '开拓',
    'twin-beam': '双子光束', 'upper-hand': '抢先', 'wicked-leap': '邪恶跳跃', 'wildbolt-storm': '疾风骤雨',
    'zeffect': 'Z效果', 'shadow-rush': '暗影冲', 'shadow-break': '暗影裂', 'shadow-end': '暗影终结',
}
print(f"Total moves: {len(MOVE_NAMES_CN)}")


# ============ 数据缓存 ============
class PokemonDataCache:
    _instance = None
    _data = None
    _sorted_ids = None
    
    @classmethod
    def get_data(cls):
        if cls._data is None:
            cls.load()
        return cls._data
    
    @classmethod
    def load(cls):
        print("📦 加载宝可梦数据...")
        start = time.time()
        with open(POKEMON_DB_PATH, 'r', encoding='utf-8') as f:
            cls._data = json.load(f)
        cls._sorted_ids = sorted(cls._data.keys(), key=lambda x: int(x))
        print(f"✅ 数据加载完成! 耗时: {time.time()-start:.2f}秒, 共 {len(cls._data)} 只宝可梦")
    
    @classmethod
    def get_sorted_ids(cls):
        if cls._sorted_ids is None:
            cls.get_data()
        return cls._sorted_ids

# ============ API响应缓存 ============
class APICache:
    _cache = {}
    _cache_time = {}
    CACHE_TTL = 7200  # 2小时缓存
    
    @classmethod
    def get(cls, key):
        if key in cls._cache:
            if time.time() - cls._cache_time[key] < cls.CACHE_TTL:
                return cls._cache[key]
        return None
    
    @classmethod
    def set(cls, key, value):
        cls._cache[key] = value
        cls._cache_time[key] = time.time()

def fetch_json(url):
    """JSON获取"""
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, context=SSL_CONTEXT, timeout=8) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"获取 {url} 失败: {e}")
        return None

def fetch_json_with_cache(url, cache_key):
    """带缓存的JSON获取"""
    cached = APICache.get(cache_key)
    if cached is not None:
        return cached
    
    data = fetch_json(url)
    if data:
        APICache.set(cache_key, data)
    return data

# ============ 精灵图下载 ============
def download_sprite(pokemon_id):
    sprite_path = os.path.join(SPRITE_DIR, f"{pokemon_id}.png")
    if os.path.exists(sprite_path):
        return True
    
    try:
        url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{pokemon_id}.png"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, context=SSL_CONTEXT, timeout=8) as response:
            with open(sprite_path, 'wb') as f:
                f.write(response.read())
        return True
    except Exception as e:
        return False

def prefetch_sprites(start_id=1, end_id=151):
    """后台预加载精灵图"""
    print("🔄 开始预加载精灵图...")
    for pid in range(start_id, min(end_id, 30) + 1):
        download_sprite(pid)
    
    def background_download():
        for pid in range(31, end_id + 1):
            download_sprite(pid)
        print("✅ 精灵图预加载完成!")
    
    threading.Thread(target=background_download, daemon=True).start()

def get_sprite_url(pokemon_id):
    sprite_path = os.path.join(SPRITE_DIR, f"{pokemon_id}.png")
    if os.path.exists(sprite_path):
        return f"/sprite/{pokemon_id}.png"
    else:
        threading.Thread(target=download_sprite, args=(pokemon_id,), daemon=True).start()
        return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{pokemon_id}.png"

# ============ 工具函数 ============
def get_cn_name(pokemon_id):
    return POKEMON_NAMES_CN.get(str(pokemon_id), None)

def get_cn_types(types):
    return [TYPE_NAMES_CN.get(t, t) for t in types]

def format_height(height):
    return f"{height:.1f} m"

def format_weight(weight):
    return f"{weight:.1f} kg"

def get_cry_url(pokemon_id):
    """获取宝可梦叫声 URL - 使用新的PokeAPI cries"""
    return f"https://raw.githubusercontent.com/PokeAPI/cries/main/cries/pokemon/latest/{pokemon_id}.ogg"

def get_name_audio_url(pokemon_id):
    """获取宝可梦名称语音 URL - 使用本地生成的TTS音频"""
    tts_path = os.path.join(TTS_DIR, f"{pokemon_id}.mp3")
    if os.path.exists(tts_path):
        return f"/tts/{pokemon_id}.mp3"
    return None

# ============ 优化后的API函数 ============
def get_pokemon_detail(pokemon_id):
    """获取宝可梦详情 - 带缓存"""
    cache_key = f"detail_{pokemon_id}"
    cached = APICache.get(cache_key)
    if cached is not None:
        return cached
    
    data = fetch_json(f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}")
    if data:
        APICache.set(cache_key, data)
    return data

def get_evolution_chain(pokemon_id):
    """获取进化链 - 优化：并发请求"""
    cache_key = f"evo_{pokemon_id}"
    cached = APICache.get(cache_key)
    if cached is not None:
        return cached
    
    # 并发获取species和evolution_chain
    species_url = f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_id}"
    
    # 使用预加载的detail数据获取species信息
    detail_data = get_pokemon_detail(pokemon_id)
    if not detail_data:
        return []
    
    # 从species URL获取evolution chain URL
    species_url = f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_id}"
    species_data = fetch_json_with_cache(species_url, f"species_{pokemon_id}")
    
    if not species_data or 'evolution_chain' not in species_data:
        return []
    
    evo_data = fetch_json(species_data['evolution_chain']['url'])
    if not evo_data:
        return []
    
    evolutions = []
    def parse_chain(chain, stage=0):
        species_url = chain['species']['url']
        species_id = int(species_url.rstrip('/').split('/')[-1])
        evolutions.append({
            'id': species_id,
            'name': chain['species']['name'],
            'cn_name': get_cn_name(species_id),
            'stage': stage,
            'sprite_url': get_sprite_url(species_id)
        })
        for evo in chain.get('evolves_to', []):
            parse_chain(evo, stage + 1)
    
    parse_chain(evo_data['chain'])
    evolutions.sort(key=lambda x: x['id'])
    APICache.set(cache_key, evolutions)
    return evolutions

def get_pokemon_description(pokemon_id):
    """获取宝可梦描述（中文）"""
    cache_key = f"desc_{pokemon_id}"
    cached = APICache.get(cache_key)
    if cached is not None:
        return cached
    
    species_data = fetch_json_with_cache(
        f"https://pokeapi.co/api/v2/pokemon-species/{pokemon_id}",
        f"species_{pokemon_id}"
    )
    
    if not species_data:
        return None
    
    # 获取中文描述
    descriptions = []
    for entry in species_data.get('flavor_text_entries', []):
        if entry['language']['name'] == 'zh-hans':
            desc = entry['flavor_text'].replace('\n', ' ').replace('\f', ' ').strip()
            if desc:
                descriptions.append(desc)
    
    # 获取栖息地
    habitat = None
    if species_data.get('habitat'):
        habitat_data = fetch_json(species_data['habitat']['url'])
        if habitat_data:
            for name in habitat_data.get('names', []):
                if name['language']['name'] == 'zh-hans':
                    habitat = name['name']
                    break
    
    # 获取特性描述（中文）
    genus = None
    for gen in species_data.get('genera', []):
        if gen['language']['name'] == 'zh-hans':
            genus = gen['genus']
            break
    
    result = {
        'descriptions': descriptions[:3],  # 最多3条
        'habitat': habitat,
        'genus': genus
    }
    
    APICache.set(cache_key, result)
    return result

def get_pokemon_moves(pokemon_id):
    """获取技能列表 - 优化：减少调用，不获取中文名"""
    cache_key = f"moves_{pokemon_id}"
    cached = APICache.get(cache_key)
    if cached is not None:
        return cached
    
    detail_data = get_pokemon_detail(pokemon_id)
    if not detail_data:
        return []
    
    moves = []
    # 只获取前8个技能，不获取中文名（使用本地映射）
    for move_info in detail_data.get('moves', [])[:20]:
        move_name = move_info['move']['name']
        # 优先使用本地中文映射
        cn_name = MOVE_NAMES_CN.get(move_name, move_name)
        moves.append({'name': move_name, 'cn_name': cn_name})
    
    APICache.set(cache_key, moves)
    return moves

def get_abilities_with_cn(detail_data, local_abilities):
    """获取特性列表 - 优化：使用本地映射"""
    abilities = []
    
    if detail_data and 'abilities' in detail_data:
        for ab in detail_data['abilities']:
            ability_name = ab['ability']['name']
            # 优先使用本地中文映射
            cn_name = ABILITY_NAMES_CN.get(ability_name, ability_name)
            abilities.append({'name': ability_name, 'cn_name': cn_name})
    else:
        abilities = [{'name': a, 'cn_name': a} for a in local_abilities]
    
    return abilities

# ============ 预加载热门宝可梦详情 ============
def prefetch_hot_pokemon_details():
    """预加载热门宝可梦的详情数据（1-30号）"""
    def background_prefetch():
        print("🔄 预加载热门宝可梦详情...")
        for pid in range(1, 31):
            get_pokemon_detail(pid)
        print("✅ 热门宝可梦详情预加载完成!")
    
    threading.Thread(target=background_prefetch, daemon=True).start()

# ============ 路由 ============

# 二跳页宝可梦ID列表
STAGE2_POKEMON_IDS = [
        # 御三家二阶进化
        5,   # 火恐龙
        8,   # 卡咪龟
        2,   # 妙蛙草
        # 、御三家三阶
        # 6,   # 喷火龙
        # 9,   # 水箭龟
        # 5,   # 妙蛙花
        # 关东御三家
        133,  # 伊布
        134,  # 水伊布
        135,  # 雷伊布
        136,  # 火伊布
        # 城都御三家二阶
        155,  # 煤山龟
        158,  # 蓝鳄
        161,  # 尾立
        # 芳缘御三家二阶
        257,  # 火焰马
        260,  # 巨沼怪
        # 神奥御三家二阶
        389,  # 烈焰马
        391,  # 火锅猫
        403,  # 小电击兽
        # 合众御三家二阶
        503,  # 大剑少女
        506,  # 步哨鼠
        509,  # 扒手猫
        # 卡洛斯御三家二阶
        652,  # 布里卡隆
        655,  # 烈箭鹰
        658,  # 黏黏宝
        # 阿罗拉御三家二阶
        806,  # 炽焰咆哮虎
        809,  # 西狮海壬
        813,  # 智挥猩
        # 伽勒尔御三家二阶
        891,  # 蕾冠王
        # 帕底亚御三家二阶
        901,  # 狂怒猿
        905,  # 蜜月
        # 其他常见二跳页
        26,   # 雷丘
        36,   # 胖可丁
        45,   # 霸王花
        51,   # 三头龙
        53,   # 猫老大
        55,   # 哥达鸭
        57,   # 荷荷郎
        59,   # 风速狗
        61,   # 蚊香蛙皇
        63,   # 凯西
        65,   # 胡地
        67,   # 怪力
        69,   # 喇叭芽
        71,   # 大食花
        73,   # 大毒蝰
        75,   # 隆隆岩
        77,   # 小火马
        79,   # 呆壳兽
        81,   # 小磁怪
        82,   # 三合一磁怪
        83,   # 大葱鸭
        84,   # 嘟嘟
        86,   # 小海狮
        88,   # 臭泥
        89,   # 臭臭泥
        91,   # 刺甲贝
        94,   # 耿鬼
        95,   # 大岩蛇
        97,   # 催眠貘
        99,   # 巨钳蟹
        100,  # 闪电球
        101,  # 雷电球
        102,  # 蛋蛋
        103,  # 椰蛋树
        104,  # 卡拉卡拉
        105,  # 嘎啦嘎啦
        106,  # 飞腿郎
        107,  # 快拳郎
        108,  # 大舌头
        109,  # 瓦斯弹
        110,  # 双弹瓦斯
        111,  # 铁甲犀牛
        112,  # 铁甲暴龙
        113,  # 吉利蛋
        114,  # 蔓藤怪
        116,  # 墨海马
        117,  # 海刺龙
        118,  # 角金鱼
        119,  # 海星星
        120,  # 魔墙人偶
        121,  # 宝可梦
        122,  # 魔墙人偶
        124,  # 迷唇姐
        125,  # 电击兽
        126,  # 鸭嘴火兽
        127,  # 大甲
        128,  # 肯泰罗
        131,  # 拉普拉斯
        # 更多
        137,  # 多边兽
        138,  # 化石盔
        139,  # 化石翼龙
        140,  # 化石盔
        141,  # 化石翼龙
        142,  # 化石翼龙
        143,  # 卡比兽
        144,  # 急冻鸟
        145,  # 闪电鸟
        146,  # 火焰鸟
        147,  # 迷你龙
        148,  # 哈克龙
        150,  # 超梦
        151,  # 梦幻
]

@app.route('/')
def index():
    """首页 - 宝可梦列表"""
    page = request.args.get('page', 1, type=int)
    filter_type = request.args.get('type', '', type=str)
    search_query = request.args.get('q', '', type=str).strip()
    
    pokemons = PokemonDataCache.get_data()
    sorted_ids = PokemonDataCache.get_sorted_ids()
    
    # 搜索功能（支持ID、中文名、英文名模糊匹配）
    if search_query:
        search_query_lower = search_query.lower()
        # 判断是否是数字（ID搜索）
        is_numeric = search_query.isdigit()
        
        sorted_ids = [pid for pid in sorted_ids 
                     if (search_query_lower in pokemons[pid]['name'].lower()) or 
                        (get_cn_name(pid) and search_query_lower in get_cn_name(pid).lower()) or
                        (is_numeric and pid == search_query)]
    
    # 类型筛选
    if filter_type:
        sorted_ids = [pid for pid in sorted_ids 
                      if filter_type.lower() in [t.lower() for t in pokemons[pid].get('type', [])]]
    
    # 记录搜索结果数量
    search_results_count = len(sorted_ids) if search_query else None
    
    # 分页
    total_pokemons = len(sorted_ids)
    total_pages = (total_pokemons + POKEMONS_PER_PAGE - 1) // POKEMONS_PER_PAGE if total_pokemons > 0 else 1
    
    start_idx = (page - 1) * POKEMONS_PER_PAGE
    end_idx = min(start_idx + POKEMONS_PER_PAGE, total_pokemons)
    page_ids = sorted_ids[start_idx:end_idx]
    
    # 构建页面数据
    pokemon_list = []
    for pid in page_ids:
        p = pokemons[pid]
        pokemon_list.append({
            'id': int(pid),
            'name': p['name'],
            'cn_name': get_cn_name(pid),
            'types': p['type'],
            'cn_types': get_cn_types(p['type']),
            'sprite_url': get_sprite_url(int(pid))
        })
    
    return render_template('index.html',
                           pokemons=pokemon_list,
                           page=page,
                           total_pages=total_pages,
                           total_pokemon=total_pokemons,
                           filter_type=filter_type,
                           type_colors=TYPE_COLORS,
                           type_names=TYPE_NAMES_CN,
                           search_query=search_query,
                           search_results_count=search_results_count)


@app.route('/pokemon/<int:pokemon_id>')
def detail(pokemon_id):
    """宝可梦详情页 - 优化版"""
    # 获取大师赛模式参数
    master_mode = request.args.get('master', 'false') == 'true'
    # 成功通过大师赛后显示完整页面，但继续大师赛流程
    success_mode = request.args.get('success', 'false') == 'true'
    # 大师赛成功模式（新页面）
    master_success_mode = request.args.get('master_success', 'false') == 'true'
    
    # 如果是成功模式，master_mode 为 false（显示完整内容），但保留大师赛导航
    post_success_mode = success_mode or master_success_mode
    
    # 如果是成功模式，master_mode 为 false（显示完整内容）
    if success_mode or master_success_mode:
        master_mode = False
    
    pokemons = PokemonDataCache.get_data()
    
    if str(pokemon_id) not in pokemons:
        return "宝可梦不存在", 404
    
    p = pokemons[str(pokemon_id)]
    
    # 获取用户来源页面，用于返回时保留筛选状态
    referer = request.headers.get('Referer', '')
    back_filter = ''
    if 'type=' in referer:
        # 从 referer 中提取筛选参数
        import re
        match = re.search(r'type=([^&]+)', referer)
        if match:
            back_filter = match.group(1)
    
    # 计算上一个和下一个宝可梦ID
    sorted_ids = PokemonDataCache.get_sorted_ids()
    current_index = None
    for i, sid in enumerate(sorted_ids):
        if int(sid) == pokemon_id:
            current_index = i
            break
    
    prev_id = None
    next_id = None
    if current_index is not None:
        if current_index > 0:
            prev_id = int(sorted_ids[current_index - 1])
        if current_index < len(sorted_ids) - 1:
            next_id = int(sorted_ids[current_index + 1])
    
    # 获取上一个和下一个宝可梦的信息
    prev_info = None
    next_info = None
    if prev_id:
        prev_info = {
            'id': prev_id,
            'cn_name': get_cn_name(prev_id),
            'sprite_url': get_sprite_url(prev_id)
        }
    if next_id:
        next_info = {
            'id': next_id,
            'cn_name': get_cn_name(next_id),
            'sprite_url': get_sprite_url(next_id)
        }
    
    # 获取详情数据（已缓存）
    detail_data = get_pokemon_detail(pokemon_id)
    
    # 获取特性（使用本地映射，不额外调用API）
    abilities = get_abilities_with_cn(detail_data, p.get('abilities', []))
    
    sprite_url = get_sprite_url(pokemon_id)
    
    # 并发获取进化链和技能
    with ThreadPoolExecutor(max_workers=3) as executor:
        evo_future = executor.submit(get_evolution_chain, pokemon_id)
        moves_future = executor.submit(get_pokemon_moves, pokemon_id)
        desc_future = executor.submit(get_pokemon_description, pokemon_id)
        
        evolutions = evo_future.result()
        moves = moves_future.result()
        pokemon_desc = desc_future.result()
    
    # 获取主要类型颜色用于动态背景
    primary_type = p['type'][0] if p['type'] else 'normal'
    primary_color = TYPE_COLORS.get(primary_type, '#667eea')
    
    return render_template('detail.html',
                           pokemon=p,
                           pokemon_id=pokemon_id,
                           cn_name=get_cn_name(pokemon_id),
                           types=p['type'],
                           cn_types=get_cn_types(p['type']),
                           height=format_height(p['height']),
                           weight=format_weight(p['weight']),
                           abilities=abilities,
                           moves=moves,
                           base_moves=moves[:5] if len(moves) > 5 else moves,
                           extra_moves=moves[5:] if len(moves) > 5 else [],
                           sprite_url=sprite_url,
                           cry_url=get_cry_url(pokemon_id),
                           name_audio_url=get_name_audio_url(pokemon_id),
                           evolutions=evolutions,
                           type_colors=TYPE_COLORS,
                           type_names=TYPE_NAMES_CN,
                           back_filter=back_filter,
                           primary_color=primary_color,
                           primary_type=primary_type,
                           prev_info=prev_info,
                           next_info=next_info,
                           pokemon_desc=pokemon_desc,
                           master_mode=master_mode,
                           post_success_mode=post_success_mode,
                           master_success_mode=master_success_mode)

@app.route('/sprite/<int:pokemon_id>.png')
def serve_sprite(pokemon_id):
    """提供精灵图服务 - 带缓存头"""
    sprite_path = os.path.join(SPRITE_DIR, f"{pokemon_id}.png")
    if os.path.exists(sprite_path):
        response = make_response(send_from_directory(SPRITE_DIR, f"{pokemon_id}.png", mimetype='image/png'))
        response.headers['Cache-Control'] = 'public, max-age=2592000'
        return response
    else:
        if download_sprite(pokemon_id):
            response = make_response(send_from_directory(SPRITE_DIR, f"{pokemon_id}.png", mimetype='image/png'))
            response.headers['Cache-Control'] = 'public, max-age=2592000'
            return response
        abort(404)

@app.route('/tts/<int:pokemon_id>.mp3')
def serve_tts(pokemon_id):
    """提供宝可梦名称语音服务"""
    tts_path = os.path.join(TTS_DIR, f"{pokemon_id}.mp3")
    if os.path.exists(tts_path):
        response = make_response(send_from_directory(TTS_DIR, f"{pokemon_id}.mp3", mimetype='audio/mpeg'))
        response.headers['Cache-Control'] = 'public, max-age=2592000'
        return response
    abort(404)

@app.route('/api/random-stage2')
def random_stage2_pokemon():
    """获取随机二跳页宝可梦（大师赛用）"""
    import random
    
    # 随机选择一个
    random_id = random.choice(STAGE2_POKEMON_IDS)
    return jsonify({'pokemon_id': random_id})


@app.route('/api/random-stage2-with-exclude')
def random_stage2_with_exclude():
    """获取随机二跳页宝可梦（排除指定ID，用于去重）"""
    import random
    
    # 获取要排除的ID列表
    exclude_str = request.args.get('exclude', '')
    if exclude_str:
        exclude_ids = [int(x) for x in exclude_str.split(',') if x.isdigit()]
    else:
        exclude_ids = []
    
    # 从列表中排除已浏览的ID
    available_ids = [x for x in STAGE2_POKEMON_IDS if x not in exclude_ids]
    
    if not available_ids:
        return jsonify({'error': '没有更多宝可梦了', 'pokemon_id': None})
    
    # 随机选择一个
    random_id = random.choice(available_ids)
    return jsonify({'pokemon_id': random_id})



# ============ 启动 ============
if __name__ == '__main__':
    print("🚀 启动宝可梦图鉴 (优化版 v2)...")
    print(f"📁 数据库: {POKEMON_DB_PATH}")
    print(f"📁 精灵图: {SPRITE_DIR}")
    
    # 预加载数据
    PokemonDataCache.load()
    
    # 后台预加载精灵图
    prefetch_sprites()
    
    # 预加载热门宝可梦详情
    prefetch_hot_pokemon_details()
    
    print("🌐 访问地址: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
