import requests
import time
import csv

# 替换为你自己的百度地图 API Key
API_KEY = 'Hoj1yAURxYIZqtkZTbMLVD8454lczIsc'

# 设置请求参数
base_url = 'http://api.map.baidu.com/place/v2/search'
query = '委员会'
region = '南京'
page_size = 20
max_pages = 50  # 百度地图 API 每个关键词最多能获取 1000 条记录（20 条 × 50 页）

# 存储结果
results = []

for page_num in range(max_pages):
    params = {
        'query': query,
        'region': region,
        'output': 'json',
        'ak': API_KEY,
        'page_size': page_size,
        'page_num': page_num
    }
    
    res = requests.get(base_url, params=params)
    data = res.json()
    
    if data['status'] != 0 or not data['results']:
        print(f"请求第 {page_num + 1} 页失败或无结果")
        break

    for item in data['results']:
        name = item.get('name')
        address = item.get('address')
        lat = item['location']['lat']
        lng = item['location']['lng']
        results.append([name, address, lat, lng])
    
    print(f"已获取第 {page_num + 1} 页数据")
    time.sleep(0.5)  # 防止请求过快被限速

# 保存为 CSV 文件
with open('nursing_home.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['名称', '地址', '纬度', '经度'])
    writer.writerows(results)

print("成功")