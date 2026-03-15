#!/bin/bash
# 启动脚本 - 使用 Gunicorn 替代 Flask 开发服务器
# 性能提升：多 worker 并发处理请求

cd /Users/lailixiang/.openclaw/workspace/pokemon

# 使用 gunicorn 运行，4个 worker
exec /Users/lailixiang/Library/Python/3.11/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:5000 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    "pokedex:app"
