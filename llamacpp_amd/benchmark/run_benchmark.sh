#!/bin/bash
# llama.cpp 性能测试脚本
# 使用 llama-bench 原生 CSV 输出

MODEL=~/data/models/Qwen3-30B-A3B-Q4_K_M.gguf
LLAMA_BENCH=~/llama.cpp/build/bin/llama-bench
RESULT_DIR=~/lpl_docs/llamacpp_amd/benchmark/results
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULT_FILE=$RESULT_DIR/benchmark_$TIMESTAMP.csv

mkdir -p $RESULT_DIR

echo "=========================================="
echo "llama.cpp 性能测试"
echo "模型: $MODEL"
echo "结果: $RESULT_FILE"
echo "=========================================="

# 预热 (GPU) - 编译 Vulkan 着色器
echo ""
echo "[预热] 运行 GPU 预热测试 (编译着色器)..."
$LLAMA_BENCH -m $MODEL -ngl 99 -p 128 -n 32 -r 1 2>/dev/null
echo "[预热] 完成"
echo ""

# 辅助函数: 运行测试并追加结果 (跳过重复表头)
run_test() {
    local test_id=$1
    local backend=$2
    local ngl_args=$3
    local pp=$4
    local tg=$5

    echo "[$test_id] $backend: pp=$pp tg=$tg"
    output=$($LLAMA_BENCH -m $MODEL $ngl_args -p $pp -n $tg -r 2 -o csv 2>/dev/null)

    if [ ! -s "$RESULT_FILE" ]; then
        # 第一次: 写入表头和数据
        echo "$output" >> $RESULT_FILE
    else
        # 后续: 只写入数据 (跳过表头)
        echo "$output" | tail -n +2 >> $RESULT_FILE
    fi
}

# ==================== GPU 测试 ====================
echo "=========================================="
echo "后端: GPU (Vulkan, -ngl 99)"
echo "=========================================="

run_test "T1" "GPU" "-ngl 99" 128 128
run_test "T2" "GPU" "-ngl 99" 128 256
run_test "T3" "GPU" "-ngl 99" 512 256
run_test "T4" "GPU" "-ngl 99" 1024 128
run_test "T5" "GPU" "-ngl 99" 2048 256
run_test "T6" "GPU" "-ngl 99" 4096 256
run_test "T7" "GPU" "-ngl 99" 512 512
run_test "T8" "GPU" "-ngl 99" 1024 512

# ==================== CPU 测试 ====================
echo ""
echo "=========================================="
echo "后端: CPU (32 线程)"
echo "=========================================="

run_test "T1" "CPU" "-ngl 0 -t 32" 128 128
run_test "T2" "CPU" "-ngl 0 -t 32" 128 256
run_test "T3" "CPU" "-ngl 0 -t 32" 512 256
run_test "T4" "CPU" "-ngl 0 -t 32" 1024 128
run_test "T5" "CPU" "-ngl 0 -t 32" 2048 256
run_test "T6" "CPU" "-ngl 0 -t 32" 4096 256
run_test "T7" "CPU" "-ngl 0 -t 32" 512 512
run_test "T8" "CPU" "-ngl 0 -t 32" 1024 512

echo ""
echo "=========================================="
echo "测试完成!"
echo "结果保存至: $RESULT_FILE"
echo "=========================================="

# 显示结果摘要
echo ""
echo "结果预览:"
head -30 $RESULT_FILE
