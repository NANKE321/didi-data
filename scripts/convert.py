#!/usr/bin/env python3
"""
Excel → JSON 转换脚本
GitHub Actions 自动调用
"""
import os
import json
import glob
from datetime import datetime, timedelta

def parse_excel(path):
    """解析 Excel 文件"""
    try:
        import xlrd
        wb = xlrd.open_workbook(path)
    except:
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        return parse_openpyxl(wb)

    all_data = []
    for ws in wb.sheets():
        if ws.nrows < 2:
            continue
        headers = [ws.cell_value(0, c) for c in range(ws.ncols)]
        col = {}
        for i, h in enumerate(headers):
            if h:
                col[str(h).strip()] = i

        for r in range(1, ws.nrows):
            def get(name, default=''):
                idx = col.get(name)
                if idx is not None and idx < ws.ncols:
                    return ws.cell_value(r, idx)
                return default

            n = str(get('司机姓名', '')).strip()
            if not n or n == '-' or n == '司机姓名':
                continue

            date_val = get('取数日期')
            if isinstance(date_val, float) and date_val > 40000:
                d = (datetime(1899, 12, 30) + timedelta(days=int(date_val))).strftime('%Y-%m-%d')
            else:
                d = str(date_val)[:10]

            def f(v, def_=0):
                if v == '' or v is None or v == '-':
                    return def_
                try:
                    return float(v)
                except:
                    return def_

            pr = f(get('工作日高峰计费占比'))
            fr = f(get('快优订单占比'))

            all_data.append({
                'date': d, 'name': n, 'plate': str(get('车牌号', '-')).strip(),
                'status': str(get('司机状态', '其他')).strip(),
                'entered': '1' if f(get('是否入围')) == 1 else '0',
                'tier': str(get('档位', '-')).strip() or '-',
                'compliance': str(get('合规类型', '-')).strip() or ('双证合规' if f(get('是否车证合规')) == 1 else '不合规'),
                'days_worked': int(f(get('在职天数'))), 'daily_service_score': round(f(get('日均服务分')), 2),
                'total_orders': int(f(get('完单数'))), 'total_flow': round(f(get('司机基础流水')), 2),
                'total_billing_time': round(f(get('计费时长（剔除培训）')), 2),
                'online_time': round(f(get('在线时间')), 2),
                'peak_online_time': round(f(get('高峰在线时间')), 2),
                'threshold': round(f(get('入围门槛')), 2),
                'diff': round(f(get('计费时长（剔除培训）')) - f(get('入围门槛')), 2),
                'daily_min_billing': 0,
                'early_peak': round(f(get('早高峰计费')), 2), 'noon_peak': round(f(get('午高峰计费')), 2),
                'late_peak': round(f(get('晚高峰计费')), 2), 'night_peak': round(f(get('夜高峰计费')), 2),
                'workday_peak_billing': round(f(get('工作日高峰计费')), 2),
                'workday_billing': round(f(get('工作日计费')), 2),
                'peak_ratio': round(pr * 100, 1) if pr <= 1 else round(pr, 1),
                'fast_ratio': round(fr * 100, 1) if fr <= 1 else round(fr, 1),
                'fast_count': int(f(get('快优订单数'))), 'total_orders2': int(f(get('订单数'))),
                'vehicle_owner': str(get('车辆所有人', '-')).strip(),
                'company': str(get('公司名称', '-')).strip(),
                'biz_line': str(get('业务线', '-')).strip()
            })

    return all_data

def parse_openpyxl(wb):
    """解析 openpyxl 工作簿"""
    all_data = []
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        if len(rows) < 2:
            continue
        headers = [str(h).strip() if h else '' for h in rows[0]]
        col = {h: i for i, h in enumerate(headers) if h}

        for row in rows[1:]:
            def get(name, default=''):
                idx = col.get(name)
                if idx is not None and idx < len(row):
                    return row[idx] or default
                return default

            n = str(get('司机姓名', '')).strip()
            if not n or n == '-' or n == '司机姓名':
                continue

            date_val = get('取数日期')
            if isinstance(date_val, datetime):
                d = date_val.strftime('%Y-%m-%d')
            elif isinstance(date_val, (int, float)) and date_val > 40000:
                d = (datetime(1899, 12, 30) + timedelta(days=int(date_val))).strftime('%Y-%m-%d')
            else:
                d = str(date_val)[:10]

            def f(v, def_=0):
                if v == '' or v is None or v == '-':
                    return def_
                try:
                    return float(v)
                except:
                    return def_

            pr = f(get('工作日高峰计费占比'))
            fr = f(get('快优订单占比'))

            all_data.append({
                'date': d, 'name': n, 'plate': str(get('车牌号', '-')).strip(),
                'status': str(get('司机状态', '其他')).strip(),
                'entered': '1' if f(get('是否入围')) == 1 else '0',
                'tier': str(get('档位', '-')).strip() or '-',
                'compliance': str(get('合规类型', '-')).strip() or ('双证合规' if f(get('是否车证合规')) == 1 else '不合规'),
                'days_worked': int(f(get('在职天数'))), 'daily_service_score': round(f(get('日均服务分')), 2),
                'total_orders': int(f(get('完单数'))), 'total_flow': round(f(get('司机基础流水')), 2),
                'total_billing_time': round(f(get('计费时长（剔除培训）')), 2),
                'online_time': round(f(get('在线时间')), 2),
                'peak_online_time': round(f(get('高峰在线时间')), 2),
                'threshold': round(f(get('入围门槛')), 2),
                'diff': round(f(get('计费时长（剔除培训）')) - f(get('入围门槛')), 2),
                'daily_min_billing': 0,
                'early_peak': round(f(get('早高峰计费')), 2), 'noon_peak': round(f(get('午高峰计费')), 2),
                'late_peak': round(f(get('晚高峰计费')), 2), 'night_peak': round(f(get('夜高峰计费')), 2),
                'workday_peak_billing': round(f(get('工作日高峰计费')), 2),
                'workday_billing': round(f(get('工作日计费')), 2),
                'peak_ratio': round(pr * 100, 1) if pr <= 1 else round(pr, 1),
                'fast_ratio': round(fr * 100, 1) if fr <= 1 else round(fr, 1),
                'fast_count': int(f(get('快优订单数'))), 'total_orders2': int(f(get('订单数'))),
                'vehicle_owner': str(get('车辆所有人', '-')).strip(),
                'company': str(get('公司名称', '-')).strip(),
                'biz_line': str(get('业务线', '-')).strip()
            })

    return all_data

def main():
    # 查找所有 Excel 文件
    files = glob.glob('uploads/*.xls') + glob.glob('uploads/*.xlsx')
    if not files:
        print('没有找到 Excel 文件')
        return

    print(f'找到 {len(files)} 个文件')

    # 读取现有数据
    existing = []
    if os.path.exists('data.json'):
        with open('data.json', 'r', encoding='utf-8') as f:
            existing = json.load(f)
    print(f'现有数据: {len(existing)} 条')

    # 解析所有文件
    new_data = []
    for f in files:
        print(f'解析: {f}')
        try:
            rows = parse_excel(f)
            new_data.extend(rows)
            print(f'  → {len(rows)} 条')
        except Exception as e:
            print(f'  → 错误: {e}')

    # 合并去重
    data_map = {r['date'] + '_' + r['name']: r for r in existing}
    for r in new_data:
        data_map[r['date'] + '_' + r['name']] = r
    all_data = list(data_map.values())

    # 保留最近7天
    dates = sorted(set(r['date'] for r in all_data), reverse=True)[:7]
    final = [r for r in all_data if r['date'] in dates]

    # 写入
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(final, f, ensure_ascii=False)

    print(f'完成! {len(final)} 条, 日期: {dates}')

if __name__ == '__main__':
    main()
