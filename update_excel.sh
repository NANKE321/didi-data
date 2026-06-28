#!/bin/bash
# ============================================
# 滴滴数据网站 - Excel 一键更新
# 用法: bash update_excel.sh <Excel文件.xlsx>
# ============================================

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ -z "$1" ]; then
    echo -e "${YELLOW}用法: bash update_excel.sh <Excel文件>${NC}"
    echo ""
    echo "示例: bash update_excel.sh ../新数据.xlsx"
    echo ""
    echo "支持的文件:"
    ls -lh "$SCRIPT_DIR"/../*.xls* 2>/dev/null || echo "  (未找到 Excel 文件)"
    exit 1
fi

EXCEL_FILE="$1"
[[ "$EXCEL_FILE" != /* ]] && EXCEL_FILE="$(pwd)/$EXCEL_FILE"

if [ ! -f "$EXCEL_FILE" ]; then
    echo -e "${RED}❌ 文件不存在: $EXCEL_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}📊 正在处理: $(basename "$EXCEL_FILE")${NC}"

# Step 1: Excel → JSON
python3 "$SCRIPT_DIR/excel_to_json.py" "$EXCEL_FILE" "$SCRIPT_DIR/../data_latest.json"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Excel 转换失败${NC}"
    exit 1
fi

# Step 2: JSON → HTML → Git Push
# 支持传 Token: bash update_excel.sh data.xlsx YOUR_TOKEN
if [ -n "$2" ]; then
    export GITHUB_TOKEN="$2"
elif [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${YELLOW}💡 提示: 未设置 Token，推送可能失败${NC}"
    echo -e "   用法: bash update_excel.sh <文件> <GitHub Token>"
fi
bash "$SCRIPT_DIR/update.sh" "$SCRIPT_DIR/../data_latest.json"
