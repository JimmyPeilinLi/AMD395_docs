#!/bin/bash
# llama.cpp 性能测试脚本
# 使用 llama-bench 原生 CSV 输出
#
# 用法:
#   ./run_benchmark.sh                    # 使用默认 Q4_K_M 模型
#   ./run_benchmark.sh /path/to/model.gguf # 指定模型路径
#   ./run_benchmark.sh --gpu-only         # 只测试 GPU
#   ./run_benchmark.sh --cpu-only         # 只测试 CPU
#   ./run_benchmark.sh --quick            # 快速测试 (较少测试点)
#   ./run_benchmark.sh --compare          # 对比 Q4_K_M 和 F16

# 默认配置
DEFAULT_MODEL=~/data/models/Qwen3-30B-A3B-Q4_K_M.gguf
F16_MODEL=~/data/models/Qwen3-30B-A3B-F16.gguf
LLAMA_BENCH=~/llama.cpp/build/bin/llama-bench
RESULT_DIR=~/lpl_docs/llamacpp_amd/benchmark/results

# 解析参数
MODEL="$DEFAULT_MODEL"
RUN_GPU=true
RUN_CPU=true
QUICK_MODE=false
COMPARE_MODE=false

for arg in "$@"; do
    case $arg in
        --gpu-only)
            RUN_CPU=false
            ;;
        --cpu-only)
            RUN_GPU=false
            ;;
        --quick)
            QUICK_MODE=true
            ;;
        --compare)
            COMPARE_MODE=true
            RUN_CPU=false  # 对比模式只测 GPU
            ;;
        --help|-h)
            echo "用法: $0 [选项] [模型路径]"
            echo ""
            echo "选项:"
            echo "  --gpu-only    只运行 GPU 测试"
            echo "  --cpu-only    只运行 CPU 测试"
            echo "  --quick       快速测试 (较少测试点)"
            echo "  --compare     对比 Q4_K_M 和 F16 (仅 GPU)"
            echo "  --help        显示帮助"
            echo ""
            echo "示例:"
            echo "  $0                                          # 默认 Q4_K_M 完整测试"
            echo "  $0 ~/data/models/model.gguf                 # 指定模型"
            echo "  $0 --gpu-only --quick                       # 快速 GPU 测试"
            echo "  $0 --compare                                # Q4_K_M vs F16 对比"
            exit 0
            ;;
        *)
            if [ -f "$arg" ]; then
                MODEL="$arg"
            fi
            ;;
    esac
done

# 对比模式处理
if [ "$COMPARE_MODE" = true ]; then
    echo "=========================================="
    echo "Q4_K_M vs F16 对比测试"
    echo "=========================================="

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)

    echo ""
    echo "=== Q4_K_M 测试 ==="
    $LLAMA_BENCH -m "$DEFAULT_MODEL" -ngl 99 -p 128,512,1024,2048 -n 128,256 -r 2 -o csv 2>/dev/null | tee "$RESULT_DIR/q4km_$TIMESTAMP.csv"

    echo ""
    echo "=== F16 测试 ==="
    $LLAMA_BENCH -m "$F16_MODEL" -ngl 99 -p 128,512,1024,2048 -n 128,256 -r 2 -o csv 2>/dev/null | tee "$RESULT_DIR/f16_$TIMESTAMP.csv"

    echo ""
    echo "=========================================="
    echo "对比测试完成!"
    echo "结果: $RESULT_DIR/q4km_$TIMESTAMP.csv"
    echo "结果: $RESULT_DIR/f16_$TIMESTAMP.csv"
    echo "=========================================="
    exit 0
fi

# 从模型路径提取名称用于结果文件
MODEL_NAME=$(basename "$MODEL" .gguf | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/_/g')
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULT_FILE=$RESULT_DIR/benchmark_${MODEL_NAME}_$TIMESTAMP.csv

mkdir -p $RESULT_DIR

# 检查模型文件
if [ ! -f "$MODEL" ]; then
    echo "错误: 模型文件不存在: $MODEL"
    exit 1
fi

MODEL_SIZE=$(ls -lh "$MODEL" | awk '{print $5}')

echo "=========================================="
echo "llama.cpp 性能测试"
echo "模型: $MODEL"
echo "大小: $MODEL_SIZE"
echo "结果: $RESULT_FILE"
echo "GPU测试: $RUN_GPU | CPU测试: $RUN_CPU"
echo "=========================================="

# 辅助函数: 运行测试并追加结果 (跳过重复表头)
run_test() {
    local test_id=$1
    local backend=$2
    local ngl_args=$3
    local pp=$4
    local tg=$5

    echo "[$test_id] $backend: pp=$pp tg=$tg"
    output=$($LLAMA_BENCH -m "$MODEL" $ngl_args -p $pp -n $tg -r 2 -o csv 2>/dev/null)

    if [ ! -s "$RESULT_FILE" ]; then
        # 第一次: 写入表头和数据
        echo "$output" >> $RESULT_FILE
    else
        # 后续: 只写入数据 (跳过表头)
        echo "$output" | tail -n +2 >> $RESULT_FILE
    fi
}

# ==================== GPU 测试 ====================
if [ "$RUN_GPU" = true ]; then
    echo ""
    echo "[预热] 运行 GPU 预热测试 (编译着色器)..."
    $LLAMA_BENCH -m "$MODEL" -ngl 99 -p 128 -n 32 -r 1 2>/dev/null
    echo "[预热] 完成"
    echo ""

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
fi

# ==================== CPU 测试 ====================
if [ "$RUN_CPU" = true ]; then
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
fi

echo ""
echo "=========================================="
echo "测试完成!"
echo "结果保存至: $RESULT_FILE"
echo "=========================================="

# 显示结果摘要
echo ""
echo "结果预览:"
head -30 $RESULT_FILE
