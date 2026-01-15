#!/usr/bin/env python3
"""
llama.cpp 性能测试结果分析脚本
用法: python3 analyze_results.py results/benchmark_*.csv
"""
import pandas as pd
import sys

if len(sys.argv) < 2:
    print("用法: python3 analyze_results.py <csv_file>")
    sys.exit(1)

# 读取 CSV
df = pd.read_csv(sys.argv[1])

# 添加测试类型列
df['test_type'] = df.apply(
    lambda r: 'pp' if r['n_prompt'] > 0 else 'tg', axis=1
)
df['tokens'] = df['n_prompt'] + df['n_gen']

# 确定后端类型
df['backend'] = df['n_gpu_layers'].apply(lambda x: 'GPU' if x > 0 else 'CPU')

print("=" * 60)
print("llama.cpp 性能测试结果分析")
print("=" * 60)

# 按后端和测试类型分组
print("\n### 详细结果 (按后端/测试类型/tokens)")
summary = df.groupby(['backend', 'test_type', 'tokens'])['avg_ts'].agg(['mean', 'std', 'count'])
print(summary.round(2).to_string())

# GPU vs CPU 对比
print("\n" + "=" * 60)
print("### GPU vs CPU 速度对比")
print("=" * 60)

gpu_data = df[df['backend'] == 'GPU'].groupby(['test_type', 'tokens'])['avg_ts'].mean()
cpu_data = df[df['backend'] == 'CPU'].groupby(['test_type', 'tokens'])['avg_ts'].mean()

comparison = pd.DataFrame({
    'GPU (t/s)': gpu_data,
    'CPU (t/s)': cpu_data,
    'GPU/CPU': (gpu_data / cpu_data).round(2)
})
print(comparison.round(2).to_string())

# 汇总统计
print("\n" + "=" * 60)
print("### 汇总统计")
print("=" * 60)

for backend in ['GPU', 'CPU']:
    print(f"\n{backend}:")
    backend_df = df[df['backend'] == backend]
    pp_avg = backend_df[backend_df['test_type'] == 'pp']['avg_ts'].mean()
    tg_avg = backend_df[backend_df['test_type'] == 'tg']['avg_ts'].mean()
    print(f"  Prefill (pp) 平均: {pp_avg:.2f} t/s")
    print(f"  Decode (tg) 平均: {tg_avg:.2f} t/s")

# 计算整体速度比
gpu_pp_avg = df[(df['backend'] == 'GPU') & (df['test_type'] == 'pp')]['avg_ts'].mean()
cpu_pp_avg = df[(df['backend'] == 'CPU') & (df['test_type'] == 'pp')]['avg_ts'].mean()
gpu_tg_avg = df[(df['backend'] == 'GPU') & (df['test_type'] == 'tg')]['avg_ts'].mean()
cpu_tg_avg = df[(df['backend'] == 'CPU') & (df['test_type'] == 'tg')]['avg_ts'].mean()

print(f"\n整体 GPU/CPU 速度比:")
print(f"  Prefill: {gpu_pp_avg/cpu_pp_avg:.2f}x")
print(f"  Decode: {gpu_tg_avg/cpu_tg_avg:.2f}x")
