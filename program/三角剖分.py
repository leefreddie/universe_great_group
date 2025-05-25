import os
import pandas as pd
import numpy as np
from scipy.spatial import Delaunay
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
import tkinter.messagebox as msgbox
import requests
import time

plt.rcParams['font.sans-serif'] = ['SimHei']  # 中文黑体
plt.rcParams['axes.unicode_minus'] = False   # 显示负号

def triangle_area(a, b, c):
    return 0.5 * abs(
        a[0] * (b[1] - c[1]) +
        b[0] * (c[1] - a[1]) +
        c[0] * (a[1] - b[1])
    )
def circumcenter(a, b, c):
    A = np.array(a)
    B = np.array(b)
    C = np.array(c)

    D = 2 * (A[0]*(B[1]-C[1]) + B[0]*(C[1]-A[1]) + C[0]*(A[1]-B[1]))
    if D == 0:
        return np.mean([A, B, C], axis=0)  # 退化成直线，取重心
    Ux = ((np.sum(A**2)*(B[1]-C[1]) + np.sum(B**2)*(C[1]-A[1]) + np.sum(C**2)*(A[1]-B[1])))/D
    Uy = ((np.sum(A**2)*(C[0]-B[0]) + np.sum(B**2)*(A[0]-C[0]) + np.sum(C**2)*(B[0]-A[0])))/D
    return np.array([Ux, Uy])

district_cache = {}  # 全局缓存字典

def get_district_from_baidu(lat, lon, ak):
    key = (round(lat, 5), round(lon, 5))  # 经纬度取5位小数作为缓存键
    if key in district_cache:
        return district_cache[key]

    url = 'http://api.map.baidu.com/reverse_geocoding/v3/'
    params = {
        'ak': 'Hoj1yAURxYIZqtkZTbMLVD8454lczIsc',
        'output': 'json',
        'coordtype': 'wgs84ll',
        'location': f'{lat},{lon}'
    }
    try:
        resp = requests.get(url, params=params)
        result = resp.json()
        if result['status'] == 0:
            district = result['result']['addressComponent']['district']
            district_cache[key] = district
            return district
        else:
            district_cache[key] = None
            print(f"API返回错误: {result}")
            return None
    except Exception as e:
        district_cache[key] = None
        print(f"请求百度API失败: {e}")
        return None


def process_resource(points, df_district, ak, resource_name):
    if len(points) < 3:
        print(f"[警告] 资源 {resource_name} 点数不足，无法进行三角剖分")
        return

    tri = Delaunay(points)

    triangle_info = []
    print(f"\n资源 {resource_name} 三角形资源配置合理性指标 B 计算开始：")
    for idx, simplex in enumerate(tri.simplices):
        a, b, c = points[simplex]
        S = triangle_area(a, b, c)
        if S == 0:
            continue

        center = circumcenter(a, b, c)
        lon, lat = center[0], center[1]

        district_name = get_district_from_baidu(lat, lon, ak)
        if district_name is None:
            print(f"[警告] 无法确定三角形{idx + 1}的区县")
            continue

        matched = df_district['区域'].apply(lambda x: district_name in x or x in district_name)
        district_rows = df_district[matched]
        if district_rows.empty:
            print(f"[警告] 找不到区县数据：{district_name}")
            continue

        district = district_rows.iloc[0]
        P = district['人口']
        C = district['收入']

        B = 1 / (S ** 2 * P * C)

        info = {
            "三角形编号": idx + 1,
            "区县": district['区域'],
            "面积": S,
            "人口": P,
            "收入": C,
            "B": B,
            "vertices": [a, b, c]
        }
        triangle_info.append(info)

        print(f"三角形 {info['三角形编号']}，区县：{info['区县']}，面积={info['面积']:.6f}，B={info['B']:.6e}")

        time.sleep(0.1)

    if not triangle_info:
        print(f"[警告] 资源 {resource_name} 没有有效三角形数据，跳过绘图。")
        return

    B_values = [info['B'] for info in triangle_info]

    min_B = max(min(B_values), 1e-10)  # 防止太小
    max_B = max(B_values)

    # 缩小vmin和vmax的差距，让颜色过渡更“紧凑”，黄色段变更明显
    new_vmin = max(min_B * 0.8, 1e-12)
    new_vmax = max_B * 0.9
    norm = mcolors.LogNorm(vmin=new_vmin, vmax=new_vmax)
    cmap = plt.get_cmap('RdYlGn_r')

    fig, ax = plt.subplots(figsize=(8, 6))

    patches = []
    for info in triangle_info:
        polygon = Polygon(info['vertices'], closed=True)
        patches.append(polygon)

    p = PatchCollection(patches, cmap=cmap, norm=norm, edgecolor='k', linewidth=0.3, alpha=0.7)
    p.set_array(np.array(B_values))

    ax.add_collection(p)
    ax.plot(points[:, 0], points[:, 1], 'o', markersize=2, color='red')

    ax.set_title(f"{resource_name} Delaunay 三角剖分图（按B值着色）")
    ax.set_xlabel("经度")
    ax.set_ylabel("纬度")
    ax.set_aspect('equal')
    ax.grid(True)

    fig.colorbar(p, ax=ax, label='资源配置合理性指标 B')

    plt.tight_layout()
    plt.show()


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.normpath(os.path.join(script_dir, '..', 'data', 'shanghai'))

    csv_files = {
        "社区": "community.csv",
        "医院": "hospitals.csv",
        "养老院": "nursing_homes.csv",
        "公园": "parks.csv",
        "高校": "universities.csv"
    }

    district_file = os.path.join(data_dir, "data2.csv")
    try:
        df_district = pd.read_csv(district_file)
    except Exception as e:
        msgbox.showerror("错误", f"读取区县数据失败: {e}")
        return

    required_cols = ['区域', '人口', '收入']
    for col in required_cols:
        if col not in df_district.columns:
            msgbox.showerror("错误", f"区县数据缺少必需列：{col}")
            return

    ak = '你的百度地图AK'  # 请替换为你的API Key

    for resource_name, filename in csv_files.items():
        file_path = os.path.join(data_dir, filename)
        try:
            df = pd.read_csv(file_path)
            if "经度" in df.columns and "纬度" in df.columns:
                points = df[["经度", "纬度"]].dropna().values
                print(f"[信息] 处理资源：{resource_name}，共{len(points)}个点")
                process_resource(points, df_district, ak, resource_name)
            else:
                print(f"[警告] 文件缺少 '经度' 或 '纬度' 列：{filename}")
        except FileNotFoundError:
            print(f"[错误] 文件未找到：{file_path}")
        except Exception as e:
            print(f"[错误] 读取文件失败：{file_path}，错误：{e}")

    msgbox.showinfo("运行完成", "所有资源的三角剖分及B指标计算已完成，请查看控制台输出。")

if __name__ == '__main__':
    main()
