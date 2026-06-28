#!/usr/bin/env python3
"""
Excel → JSON 转换器
从"今日数据" sheet 提取数据，转换为网站所需的 JSON 格式
"""
import json, sys, os
from datetime import datetime

def safe_num(val, default=0):
    """安全转数字"""
    if val is None or val == '-' or val == '':
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def safe_str(val, default='-'):
    """安全转字符串"""
    if val is None or val == '':
        return default
    return str(val).strip()

def convert_status(val):
    """状态映射"""
    s = safe_str(val, '其他')
    if s in ('正常', '备班', '封禁', '其他'):
        return s
    return s

def convert_compliance(val):
    """合规映射: 1→双证合规, 0→不合规"""
    v = safe_num(val, 0)
    return '双证合规' if v == 1 else '不合规'

def excel_to_json(excel_path, output_path):
    try:
        import openpyxl
    except ImportError:
        print("正在安装 openpyxl...")
        os.system(f"{sys.executable} -m pip install openpyxl -q")
        import openpyxl

    wb = openpyxl.load_workbook(excel_path, read_only=True, data_only=True)

    # 优先用"今日数据" sheet
    if '今日数据' in wb.sheetnames:
        ws = wb['今日数据']
        print(f"  使用 sheet: 今日数据")
    elif '数据' in wb.sheetnames:
        ws = wb['数据']
        print(f"  使用 sheet: 数据")
    else:
        # 用第一个有数据的 sheet
        ws = wb.active
        print(f"  使用 sheet: {ws.title}")

    rows = list(ws.iter_rows(values_only=True))
    if len(rows) < 2:
        print("❌ 数据为空")
        sys.exit(1)

    header = rows[0]
    data_rows = rows[1:]

    # 建立列名索引
    col = {}
    for i, h in enumerate(header):
        if h:
            col[str(h).strip()] = i

    print(f"  找到 {len(data_rows)} 条记录")

    # 检查必需列
    required = ['司机姓名', '车牌号']
    for r in required:
        if r not in col:
            # 尝试备用列名
            alt_map = {'姓名': '司机姓名', '车牌': '车牌号'}
            for alt, target in alt_map.items():
                if alt in col:
                    col[target] = col[alt]
                    break

    results = []
    for row in data_rows:
        def get(name, default=None):
            idx = col.get(name)
            if idx is not None and idx < len(row):
                return row[idx]
            return default

        name = safe_str(get('司机姓名', get('姓名', '')))
        if not name or name == '-':
            continue

        # 日期处理
        date_val = get('取数日期', get('滴滴数据取值日期'))
        if isinstance(date_val, datetime):
            date_str = date_val.strftime('%Y-%m-%d')
        else:
            date_str = safe_str(date_val, datetime.now().strftime('%Y-%m-%d'))[:10]

        entered = safe_str(get('是否入围', '0'), '0')
        if entered == '1' or entered == 1:
            entered = '1'
        else:
            entered = '0'

        tier = safe_str(get('档位', '-'), '-')
        if tier == 'None' or tier == '':
            tier = '-'

        # 计算差额
        billing_time = safe_num(get('计费时长（剔除培训）', get('你总计费时长', 0)))
        threshold = safe_num(get('入围门槛', get('当前入围门槛', 0)))
        diff = round(billing_time - threshold, 2)

        # 比率转百分比
        peak_ratio = safe_num(get('工作日高峰计费占比', 0))
        fast_ratio = safe_num(get('快优订单占比', 0))
        if peak_ratio <= 1:
            peak_ratio = round(peak_ratio * 100, 1)
        if fast_ratio <= 1:
            fast_ratio = round(fast_ratio * 100, 1)

        record = {
            "date": date_str,
            "name": name,
            "plate": safe_str(get('车牌号', '-')),
            "status": convert_status(get('司机状态')),
            "entered": entered,
            "tier": tier,
            "compliance": convert_compliance(get('是否车证合规')),
            "days_worked": int(safe_num(get('在职天数', get('本月绑车天数', 0)))),
            "daily_service_score": round(safe_num(get('日均服务分', 0)), 2),
            "total_orders": int(safe_num(get('完单数', get('本月完单数', 0)))),
            "total_flow": round(safe_num(get('司机基础流水', get('你总基础流水', 0))), 2),
            "share_amount": round(safe_num(get('分账金额', 0)), 2),
            "total_billing_time": round(billing_time, 2),
            "online_time": round(safe_num(get('在线时间', 0)), 2),
            "peak_online_time": round(safe_num(get('高峰在线时间', 0)), 2),
            "threshold": round(threshold, 2),
            "diff": diff,
            "daily_min_billing": round(safe_num(get('剩余每天最低计费时长', 0)), 2),
            "early_peak": round(safe_num(get('早高峰计费', 0)), 2),
            "noon_peak": round(safe_num(get('午高峰计费', 0)), 2),
            "late_peak": round(safe_num(get('晚高峰计费', 0)), 2),
            "night_peak": round(safe_num(get('夜高峰计费', 0)), 2),
            "workday_peak_billing": round(safe_num(get('工作日高峰计费', 0)), 2),
            "workday_billing": round(safe_num(get('工作日计费', 0)), 2),
            "peak_ratio": peak_ratio,
            "fast_ratio": fast_ratio,
            "fast_count": int(safe_num(get('快优订单数', get('快优单量', 0)))),
            "total_orders2": int(safe_num(get('订单数', get('本月完单数', 0)))),
            "vehicle_owner": safe_str(get('车辆所有人', '-')),
            "company": safe_str(get('公司名称', '上海超阳汽车租赁有限公司'))
        }
        results.append(record)

    wb.close()

    # === 合并历史数据，保留最近 7 天 ===
    d7_path = os.path.join(os.path.dirname(output_path), 'data_7d.json')
    all_data = list(results)
    if os.path.exists(d7_path):
        try:
            with open(d7_path, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
            new_dates = set(r['date'] for r in results)
            for r in old_data:
                if r['date'] not in new_dates:
                    all_data.append(r)
            all_dates = sorted(set(r['date'] for r in all_data), reverse=True)
            keep_dates = set(all_dates[:7])
            all_data = [r for r in all_data if r['date'] in keep_dates]
            print(f"  📅 合并后: {len(all_data)} 条, 日期: {sorted(keep_dates, reverse=True)}")
        except Exception as e:
            print(f"  ⚠️ 合并失败: {e}，使用新数据")

    all_data.sort(key=lambda r: (r['date'], -r['total_flow']))

    # 同时写入 data_latest.json 和 data_7d.json
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=None)
    with open(d7_path, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=None)

    print(f"  ✅ 转换完成: {len(all_data)} 条记录")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python3 excel_to_json.py <input.xlsx> <output.json>")
        sys.exit(1)
    excel_to_json(sys.argv[1], sys.argv[2])
