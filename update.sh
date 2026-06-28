#!/bin/bash
# ============================================
# 滴滴数据网站 - 一键更新脚本
# 用法: ./update.sh <数据文件.json>
# 示例: ./update.sh ../data_7d.json
# ============================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HTML_FILE="$SCRIPT_DIR/index.html"

# 颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查参数
if [ -z "$1" ]; then
    echo -e "${YELLOW}用法: ./update.sh <数据文件.json>${NC}"
    echo ""
    echo "可用的数据文件:"
    ls -lh "$SCRIPT_DIR"/../*.json 2>/dev/null || echo "  (未找到 JSON 文件)"
    echo ""
    echo -e "步骤: 1) 准备 JSON 数据文件  2) 运行 ./update.sh 数据文件.json"
    exit 1
fi

DATA_FILE="$1"

# 如果是相对路径，转换为绝对路径
if [[ "$DATA_FILE" != /* ]]; then
    DATA_FILE="$(pwd)/$DATA_FILE"
fi

# 检查文件是否存在
if [ ! -f "$DATA_FILE" ]; then
    echo -e "${RED}❌ 文件不存在: $DATA_FILE${NC}"
    exit 1
fi

# 检查 JSON 格式
if ! python3 -c "import json; json.load(open('$DATA_FILE'))" 2>/dev/null; then
    echo -e "${RED}❌ 不是有效的 JSON 文件${NC}"
    exit 1
fi

echo -e "${GREEN}📦 数据文件: $DATA_FILE${NC}"

# 获取数据统计
python3 -c "
import json
with open('$DATA_FILE') as f:
    data = json.load(f)
dates = sorted(set(r['date'] for r in data), reverse=True)
print(f'  记录数: {len(data)}')
print(f'  日期范围: {dates[-1]} ~ {dates[0]}')
print(f'  人数: {len(set(r[\"name\"] for r in data))}')
"

# 备份原 HTML
cp "$HTML_FILE" "$HTML_FILE.bak"

# 用 Python 替换 HTML 中的数据
python3 - "$DATA_FILE" "$HTML_FILE" << 'PYEOF'
import json, re, sys

data_file = sys.argv[1]
html_file = sys.argv[2]

# 读取新数据
with open(data_file, 'r', encoding='utf-8') as f:
    new_data = json.load(f)

# 读取 HTML
with open(html_file, 'r', encoding='utf-8') as f:
    html = f.read()

# 替换 var D=[...];
# 匹配从 "var D=[" 到 "];" 的内容
pattern = r'var D=\[.*?\];'
new_json = json.dumps(new_data, ensure_ascii=False)
replacement = f'var D={new_json};'

new_html, count = re.subn(pattern, replacement, html, count=1, flags=re.DOTALL)

if count == 0:
    print("❌ 未找到数据变量 var D=[...]")
    sys.exit(1)

# 写回 HTML
with open(html_file, 'w', encoding='utf-8') as f:
    f.write(new_html)

print(f"✅ HTML 数据已更新 ({len(new_data)} 条记录)")
PYEOF

# Git 提交并推送
cd "$SCRIPT_DIR"

# 检查是否有变化
if git diff --quiet index.html; then
    echo -e "${YELLOW}⚠️  数据无变化，跳过推送${NC}"
    exit 0
fi

git add index.html
DATE=$(date '+%Y-%m-%d %H:%M')
git commit -m "data: 更新数据 ($DATE)" --quiet

echo -e "${GREEN}🚀 推送到 GitHub...${NC}"

# 支持通过环境变量 GITHUB_TOKEN 设置认证
if [ -n "$GITHUB_TOKEN" ]; then
    git remote set-url origin "https://NANKE321:${GITHUB_TOKEN}@github.com/NANKE321/didi-data.git"
fi

if git push --quiet 2>&1; then
    # 清理 URL 中的 token
    git remote set-url origin "https://github.com/NANKE321/didi-data.git"
    echo -e "${GREEN}✅ 更新完成！${NC}"
    echo -e "🌐 网站: https://nanke321.github.io/didi-data/"
else
    echo -e "${RED}❌ 推送失败，请检查网络或 Token${NC}"
    echo -e "${YELLOW}提示: 可以手动运行 'git push' 重试${NC}"
    exit 1
fi
