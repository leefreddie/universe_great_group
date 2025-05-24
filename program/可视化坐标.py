import os
import pandas as pd
import numpy as np
from scipy.spatial import Delaunay
import matplotlib.pyplot as plt
import tkinter.messagebox as msgbox
import requests
import time
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体为黑体
plt.rcParams['axes.unicode_minus'] = False   # 正确显示负号

# 从 config.py 中导入 API KEY
from program import config

# 百度地图 API 逆地理编码函数
def get_district_from_coords(lng, lat, retry=3):
    url = "https://api.map.baidu.com/reverse_geocoding/v3/"
    params = {
        "ak": config.BAIDU_MAP_API_KEY,
        "output": "json",
        "coordtype": "wgs84ll",
        "location": f"{lat},{lng}"
    }
    for _ in range(retry):
        try:
            response = requests.get(url, params=params, timeout=2)
            if response.status_code == 200:
                data = response.json()
                return data['result']['addressComponent']['district']
        except Exception as e:
            time.sleep(1)
    return None

def triangle_area(a, b, c):
    return 0.5 * abs(
        a[0] * (b[1] - c[1]) +
        b[0] * (c[1] - a[1]) +
        c[0] * (a[1] - b[1])
    )

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.normpath(os.path.join(script_dir, '..', 'data', 'shanghai'))

    csv_files = ["community.csv", "hospitals.csv", "nursing_homes.csv", "parks.csv", "universities.csv"]
    all_points = []

    for filename in csv_files:
        file_path = os.path.join(data_dir, filename)
        try:
            df = pd.read_csv(file_path)
            if "经度" in df.columns and "纬度" in df.columns:
                points = df[["经度", "纬度"]].dropna().values
                all_points.extend(points)
            else:
                print(f"[警告] 文件缺少 '经度' 或 '纬度' 列：{filename}")
        except FileNotFoundError:
            print(f"[错误] 文件未找到：{file_path}")

    if not all_points:
        msgbox.showerror("错误", "未能读取任何有效坐标点，请检查 CSV 文件内容与路径。")
        return

    points = np.array(all_points)
    tri = Delaunay(points)

    plt.figure(figsize=(8, 6))
    plt.triplot(points[:, 0], points[:, 1], tri.simplices, color='blue', linewidth=0.5)
    plt.plot(points[:, 0], points[:, 1], 'o', markersize=2, color='red')
    plt.title("上海康养资源 Delaunay 三角剖分图")
    plt.xlabel("经度")
    plt.ylabel("纬度")
    plt.gca().set_aspect('equal')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # 读取区域信息
    data2_path = os.path.join(data_dir, 'data2.csv')
    df_region = pd.read_csv(data2_path)
    region_info = {
        row['区域']: {
            '人口': row['人口'],
            '面积': row['面积'],
            '收入': row['收入']
        }
        for _, row in df_region.iterrows()
    }

    B_results = []
    print("\n正在计算各三角形 B 指标（含区划信息）……")
    for i, simplex in enumerate(tri.simplices):
        a, b, c = points[simplex]
        S = triangle_area(a, b, c)
        if S == 0:
            continue
        centroid = np.mean([a, b, c], axis=0)
        district = get_district_from_coords(centroid[0], centroid[1])

        if district and district in region_info:
            rho = region_info[district]['人口'] / region_info[district]['面积']
            C = region_info[district]['收入']
            B = 1 / (S ** 2 * rho * C)
            B_results.append((i + 1, B, district))
        else:
            print(f"[警告] 无法确定三角形{i + 1}所在行政区或区数据缺失。")

    print("\n前10个三角形的资源配置合理性指标 B：")
    for i, B, district in B_results[:10]:
        print(f"三角形 {i}（{district}）: B = {B:.6e}")

    msgbox.showinfo("完成", "Delaunay 剖分与 B 指标计算已完成，终端中已输出前10个结果。")

if __name__ == '__main__':
    main()