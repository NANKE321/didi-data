#!/usr/bin/env python3
"""
同步数据到腾讯云数据库
GitHub Actions 自动调用
"""
import os
import json
import requests

APPID = os.environ.get('APPID', 'wx3245d86aa6030d44')
SECRET = os.environ.get('SECRET', '')
ENV = os.environ.get('ENV', 'cloud1-d9ga0w2uj0e2de7bd')
COL = 'driver_data'

def get_token():
    if not SECRET:
        print('❌ 未配置 APPSECRET')
        return ''
    r = requests.get(f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={SECRET}')
    data = r.json()
    if data.get('access_token'):
        return data['access_token']
    print(f'❌ Token 获取失败: {data}')
    return ''

def api(token, path, query):
    r = requests.post(f'https://api.weixin.qq.com/tcb/{path}?access_token={token}',
        json={'env': ENV, 'query': query})
    return r.json()

def main():
    # 读取数据
    with open('data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f'📊 数据: {len(data)} 条')

    # 获取 token
    token = get_token()
    if not token:
        return
    print('✅ Token 获取成功')

    # 删除旧数据
    old = api(token, 'databasecount', f'db.collection("{COL}").count()').get('count', 0)
    print(f'🗑️ 旧数据: {old} 条')

    if old > 0:
        # 用 where 条件批量删除
        api(token, 'databasedelete', f'db.collection("{COL}").where({{date:db.command.gte("2020-01-01")}}).remove()')
        print('✅ 旧数据已删除')

    # 写入新数据
    for i in range(0, len(data), 20):
        batch = data[i:i + 20]
        ds = ','.join([json.dumps(x, ensure_ascii=False) for x in batch])
        api(token, 'databaseadd', f'db.collection("{COL}").add({{data:[{ds}]}})')

    # 验证
    new = api(token, 'databasecount', f'db.collection("{COL}").count()').get('count', 0)
    print(f'✅ 完成! 云数据库: {new} 条')

if __name__ == '__main__':
    main()
