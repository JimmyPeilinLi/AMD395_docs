#!/usr/bin/env python3
"""
llama.cpp 性能测试结果分析脚本

用法:
    python3 analyze_results.py results/benchmark_*.csv
    python3 analyze_results.py results/benchmark_q4_k_m_*.csv results/benchmark_bf16_*.csv
"""
import csv
import sys
import os
from collections import defaultdict

def parse_csv(filepath):
    """解析 llama-bench CSV 输出"""
    results = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                results.append({
                    'model': row.get('model_type', 'unknown'),
                    'backend': 'GPU' if int(row.get('n_gpu_layers', 0)) > 0 else 'CPU',
                    'n_gpu_layers': int(row.get('n_gpu_layers', 0)),
                    'n_prompt': int(row.get('n_prompt', 0)),
                    'n_gen': int(row.get('n_gen', 0)),
                    'avg_ts': float(row.get('avg_ts', 0)),
                    'stddev_ts': float(row.get('stddev_ts', 0)),
                    'test_type': 'pp' if int(row.get('n_prompt', 0)) > 0 else 'tg',
                    'tokens': int(row.get('n_prompt', 0)) + int(row.get('n_gen', 0))
                })
            except (ValueError, KeyError) as e:
                continue
    return results

def analyze_results(results):
    """分析测试结果"""
    # 按后端和测试类型分组
    grouped = defaultdict(list)
    for r in results:
        key = (r['backend'], r['test_type'], r['tokens'])
        grouped[key].append(r['avg_ts'])

    return grouped

def print_summary(grouped, title=""):
    """打印汇总结果"""
    if title:
        print(f"\n{'=' * 60}")
        print(f"{title}")
        print('=' * 60)

    # 分离 GPU 和 CPU 结果
    gpu_pp = {}
    gpu_tg = {}
    cpu_pp = {}
    cpu_tg = {}

    for (backend, test_type, tokens), speeds in grouped.items():
        avg_speed = sum(speeds) / len(speeds)
        if backend == 'GPU':
            if test_type == 'pp':
                gpu_pp[tokens] = avg_speed
            else:
                gpu_tg[tokens] = avg_speed
        else:
            if test_type == 'pp':
                cpu_pp[tokens] = avg_speed
            else:
                cpu_tg[tokens] = avg_speed

    # 打印 Prefill 结果
    print("\n### Prefill (Prompt Processing)")
    print("| Tokens | GPU (t/s) | CPU (t/s) | GPU/CPU |")
    print("|--------|-----------|-----------|---------|")
    for tokens in sorted(set(list(gpu_pp.keys()) + list(cpu_pp.keys()))):
        gpu = gpu_pp.get(tokens, 0)
        cpu = cpu_pp.get(tokens, 0)
        ratio = gpu / cpu if cpu > 0 else 0
        print(f"| {tokens:>6} | {gpu:>9.2f} | {cpu:>9.2f} | {ratio:>6.2f}x |")

    # 打印 Decode 结果
    print("\n### Decode (Token Generation)")
    print("| Tokens | GPU (t/s) | CPU (t/s) | GPU/CPU |")
    print("|--------|-----------|-----------|---------|")
    for tokens in sorted(set(list(gpu_tg.keys()) + list(cpu_tg.keys()))):
        gpu = gpu_tg.get(tokens, 0)
        cpu = cpu_tg.get(tokens, 0)
        ratio = gpu / cpu if cpu > 0 else 0
        print(f"| {tokens:>6} | {gpu:>9.2f} | {cpu:>9.2f} | {ratio:>6.2f}x |")

    # 汇总
    if gpu_pp and cpu_pp and gpu_tg and cpu_tg:
        gpu_pp_avg = sum(gpu_pp.values()) / len(gpu_pp)
        cpu_pp_avg = sum(cpu_pp.values()) / len(cpu_pp)
        gpu_tg_avg = sum(gpu_tg.values()) / len(gpu_tg)
        cpu_tg_avg = sum(cpu_tg.values()) / len(cpu_tg)

        print("\n### 汇总")
        print("| 指标 | GPU | CPU | GPU/CPU |")
        print("|------|-----|-----|---------|")
        print(f"| Prefill 平均 | {gpu_pp_avg:.2f} t/s | {cpu_pp_avg:.2f} t/s | {gpu_pp_avg/cpu_pp_avg:.2f}x |")
        print(f"| Decode 平均 | {gpu_tg_avg:.2f} t/s | {cpu_tg_avg:.2f} t/s | {gpu_tg_avg/cpu_tg_avg:.2f}x |")

def main():
    if len(sys.argv) < 2:
        print("用法: python3 analyze_results.py <csv_file> [csv_file2 ...]")
        print("")
        print("示例:")
        print("  python3 analyze_results.py results/benchmark_*.csv")
        print("  python3 analyze_results.py results/benchmark_q4_k_m_*.csv")
        sys.exit(1)

    all_results = []
    files_processed = []

    for filepath in sys.argv[1:]:
        if os.path.exists(filepath):
            results = parse_csv(filepath)
            if results:
                all_results.extend(results)
                files_processed.append(os.path.basename(filepath))

    if not all_results:
        print("错误: 没有找到有效的测试结果")
        sys.exit(1)

    print("=" * 60)
    print("llama.cpp 性能测试结果分析")
    print("=" * 60)
    print(f"\n处理的文件: {len(files_processed)}")
    for f in files_processed:
        print(f"  - {f}")

    # 检查是否有多个模型
    models = set(r['model'] for r in all_results)

    if len(models) > 1:
        # 按模型分别分析
        for model in models:
            model_results = [r for r in all_results if r['model'] == model]
            grouped = analyze_results(model_results)
            print_summary(grouped, f"模型: {model}")
    else:
        # 单模型分析
        grouped = analyze_results(all_results)
        print_summary(grouped, f"模型: {list(models)[0]}")

    print("\n" + "=" * 60)
    print("分析完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
