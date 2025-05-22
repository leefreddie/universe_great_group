import os
import pandas as pd
import folium

# 获取当前目录和 data 目录
current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.normpath(os.path.join(current_dir, '..', 'data'))

# 定义类别信息（编号: 名称, 文件名, 图标颜色, 图标）
categories = {
    "1": {"key": "universities", "label": "大学", "file": "universities.csv", "color": "blue", "icon": "university"},
    "2": {"key": "nursing_homes", "label": "养老院", "file": "nursing_homes.csv", "color": "green", "icon": "heart"},
    "3": {"key": "hospitals", "label": "医院", "file": "hospitals.csv", "color": "red", "icon": "plus-square"},
    "4": {"key": "parks", "label": "公园", "file": "parks.csv", "color": "purple", "icon": "tree"},
}

# 打印选项菜单
print("请选择要显示的类别（可多选，用英文逗号分隔）：")
for num, info in categories.items():
    print(f"{num}. {info['label']}")

# 用户输入编号
user_input = input("输入编号（例如 1,3,4）：").strip()
selected_numbers = [s.strip() for s in user_input.split(',')]

# 初始化地图
shanghai_center = [31.2304, 121.4737]
m = folium.Map(location=shanghai_center, zoom_start=11)

# 加载数据并添加图标
for num in selected_numbers:
    if num in categories:
        info = categories[num]
        filepath = os.path.join(data_dir, info["file"])
        if not os.path.exists(filepath):
            print(f"❌ 找不到文件：{info['file']}，跳过。")
            continue
        df = pd.read_csv(filepath, encoding='utf-8')
        for _, row in df.iterrows():
            folium.Marker(
                location=[row['纬度'], row['经度']],
                popup=f"{info['label']}: {row['名称']}",
                icon=folium.Icon(color=info['color'], icon=info['icon'], prefix='fa')
            ).add_to(m)
    else:
        print(f"⚠️ 无效编号：{num}，跳过。")

# 保存 HTML 地图
output_html = os.path.join(current_dir, 'shanghai_kangyang_map.html')
m.save(output_html)
print(f"\n✅ 地图已保存到：{output_html}")
