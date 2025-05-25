import pandas as pd
import numpy as np

def normalize_matrix(matrix):
    """标准化矩阵"""
    # 添加一个小的常数以避免除以零
    return (matrix - matrix.min()) / (matrix.max() - matrix.min() + 1e-10)

def calculate_entropy_weight(data):
    """计算熵权法权重"""
    # 标准化数据
    normalized_data = normalize_matrix(data)
    
    # 计算第j个指标下第i个样本值占该指标的比重
    p = normalized_data / (normalized_data.sum(axis=0) + 1e-10)
    
    # 处理log(0)的情况
    p = np.where(p == 0, 1e-10, p)
    
    # 计算熵值
    k = 1 / np.log(len(data))
    e = -k * (p * np.log(p)).sum(axis=0)
    
    # 计算权重
    w = (1 - e) / (1 - e).sum()
    
    return w

def calculate_sigma(G_list):
    """计算资源配置合理性σ"""
    G_array = np.array(G_list)
    G_mean = G_array.mean()
    sigma = np.sqrt(((G_array - G_mean) ** 2).mean())
    return sigma

def calc_E(df):
    # E = R / P * 1e5
    R = df['医院'] + df['养老院'] + df['公园'] + df['院校']
    P = df['人口']
    E = R / P * 1e5
    return E

def calc_W(df):
    # W = R / C
    R = df['医院'] + df['养老院'] + df['公园'] + df['院校']
    C = df['收入']
    W = R / C
    return W

def calc_G(df):
    # G = R / (P * C)
    R = df['医院'] + df['养老院'] + df['公园'] + df['院校']
    P = df['人口']
    C = df['收入']
    G = R / (P * C)
    return G

def main():
    # 读取数据
    df1 = pd.read_csv('data/data1.csv')
    city_names = df1['区域'].tolist()
    E = calc_E(df1)
    W = calc_W(df1)
    G = calc_G(df1)
    sigma = calculate_sigma(G)
    # 构建新DataFrame
    result = pd.DataFrame({
        'E': E,
        'W': W,
        'G': G,
        'sigma': [sigma]*len(df1)
    })
    # 熵值法权重分析
    weights = calculate_entropy_weight(result.values)
    print(f"各城市E/W/G/σ 熵值法权重：")
    for col, w in zip(['E','W','G','σ'], weights):
        print(f"{col}: {w:.4f}")
    print()
    # 计算A
    A = weights[0]*E + weights[1]*W + weights[2]*G + weights[3]*(1/sigma)
    df1['A'] = A
    print('各城市A值如下：')
    for city, a in zip(city_names, A):
        print(f'{city}: {a:.4f}')
    # 保存到csv
    df1[['区域','A']].to_csv('city_A.csv', index=False)

if __name__ == "__main__":
    main() 