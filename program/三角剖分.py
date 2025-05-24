import os
import pandas as pd
import numpy as np
from scipy.spatial import Delaunay
import matplotlib.pyplot as plt
import tkinter.messagebox as msgbox

def main():
    # 获取当前脚本路径（即 program/ 三角剖分.py）
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 计算相对路径：跳出一层，到 data/shanghai
    data_dir = os.path.normpath(os.path.join(script_dir, '..', 'data', 'shanghai'))

    # 要读取的 CSV 文件列表
    csv_files = ["community.csv", "hospital.csv", "nursing_home.csv", "park.csv", "school.csv"]
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

    # 转换为 NumPy 数组
    points = np.array(all_points)

    # 执行 Delaunay 三角剖分
    tri = Delaunay(points)

    # 可视化三角剖分结果
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

    # 假设人口密度和人均收入（后续可以换成真实值）
    rho = 20000  # 人口密度 (人/km²)
    C = 80000    # 人均收入 (元)

    # 三角形面积函数
    def triangle_area(a, b, c):
        return 0.5 * abs(
            a[0] * (b[1] - c[1]) +
            b[0] * (c[1] - a[1]) +
            c[0] * (a[1] - b[1])
        )

    # 计算每个三角形的资源配置合理性 B
    B_values = []
    for simplex in tri.simplices:
        a, b, c = points[simplex]
        S = triangle_area(a, b, c)
        if S == 0:
            continue  # 排除面积为 0 的退化三角形
        B = 1 / (S**2 * rho * C)
        B_values.append(B)

    print("\n前10个三角形的资源配置合理性指标 B：")
    for i, B in enumerate(B_values[:10]):
        print(f"三角形 {i + 1}: B = {B:.6e}")

    msgbox.showinfo("运行完成", "Delaunay 剖分与 B 指标计算已完成，终端中显示前 10 个 B 值。")

if __name__ == '__main__':
    main()
