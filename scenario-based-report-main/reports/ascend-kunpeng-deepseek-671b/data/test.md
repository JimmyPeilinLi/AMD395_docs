1. # 基本信息

| **项目** | 基于 2 卡 昇腾910B4 NPU（64GiB）+ 鲲鹏920B CPU测试 DeepSeek R1 性能 |
| -------- | ------------------------------------------------------------ |
| **模型** | DeepSeek R1（671B），NPU 权重 W8A8                           |
| **时间** | 2025 年 12 月 29 日                                          |

1. # 测试环境

1. ## 硬件配置

| **硬件** | **配置信息**                         |
| :------- | :----------------------------------- |
| **CPU**  | Huawei Kunpeng 920 7263Z (128 Cores) |
| **GPU**  | Huawei Ascend 910B4（64 GiB）* 2     |
| **内存** | DDR5 64 GB * 20                      |

1. ## 软件配置

| **软件名称** | **版本信息**                        |
| :----------- | :---------------------------------- |
| **操作系统** | openEuler 22.03                     |
| **内核版本** | 5.10.0-182.0.0.95.oe2203sp3.aarch64 |
| **推理引擎** | Ftransformers v3.3.1                |
| 测试工具     | evalscope v1.0.1                    |

1. # 测试过程

1. ## 启动测试

| **启动模型** | export HCCL_OP_EXPANSION_MODE=AIV python -m ftransformers.launch_server --host 0.0.0.0 --port 8001 --model-path /home/model/DeepSeek-R1-W8A8 --attention-backend ascend --chunked-prefill-size 8192 --tensor-parallel-size 2 --device npu --trust-remote-code --mem-fraction-static 0.92 --disable-radix-cache --max-total-tokens 190000 --cpu-weight-path /home/model/deepseek-int4 --cpuinfer 128 --subpool-count 4 --num-gpu-experts 0 --quantization w8a8_int8 --served-model-name DeepSeek-R1-W8A8 --enable-defer |
| ------------ | ------------------------------------------------------------ |
| **执行测试** | // 以输入长度为 16k 为例，其他场景类似：python perf_via_es10x.py --ip 127.0.0.1 --port 8001 --parallel 1 2 4 8 --number 1 2 4 8 --model DeepSeek-R1-W8A8 --tokenizer-path /home/model/DeepSeek-R1-W8A8 --input-length 16000 --output-length 512 |

1. ## 性能数据

   | 模型                  | 环境                                | 输入 | 输出   | 并发数 | 端到端时延（s） Avg Latency(s) | 系统吞吐 Output token  throughput (tok/s) | 平均首 token 时延 Avg TTFT(s) | 平均每 token 延迟 Avg TPOT(s) | 单个请求每秒生成 token 数 Avg TPS | 平均单路吞吐  （tokens/s） |
   | --------------------- | ----------------------------------- | ---- | ------ | ------ | ------------------------------ | ----------------------------------------- | ----------------------------- | ----------------------------- | --------------------------------- | -------------------------- |
   | DeepSeek-R1-0528-w8a8 | CPU: 鲲鹏920B 128 核；GPU:2 x 910B4 | 128  | 512    | 1      | 28.94                          | 17.69                                     | 2.38                          | 0.06                          | 17.270                            | 17.690                     |
   |                       |                                     | 2    | 44.56  | 22.98  | 2.65                           | 0.09                                      | 11.260                        | 11.490                        |                                   |                            |
   |                       |                                     | 4    | 77.82  | 26.32  | 4.72                           | 0.16                                      | 6.240                         | 6.580                         |                                   |                            |
   |                       |                                     | 8    | 169.07 | 24.23  | 10.93                          | 0.32                                      | 3.120                         | 3.030                         |                                   |                            |
   |                       |                                     | 16   | 230.64 | 35.52  | 19.07                          | 0.47                                      | 2.120                         | 2.220                         |                                   |                            |
   |                       |                                     | 1024 | 512    | 1      | 38.44                          | 13.32                                     | 13.53                         | 0.05                          | 20.410                            | 13.320                     |
   |                       |                                     | 2    | 59     | 17.36  | 17.38                          | 0.08                                      | 12.330                        | 8.680                         |                                   |                            |
   |                       |                                     | 4    | 106.93 | 19.15  | 34.21                          | 0.18                                      | 5.650                         | 4.790                         |                                   |                            |
   |                       |                                     | 2k   | 512    | 1      | 47.84                          | 10.7                                      | 24.47                         | 0.05                          | 21.930                            | 10.700                     |
   |                       |                                     | 2    | 74.63  | 13.72  | 34.01                          | 0.12                                      | 8.430                         | 6.860                         |                                   |                            |
   |                       |                                     | 4    | 144.96 | 14.13  | 73.87                          | 0.17                                      | 5.780                         | 3.530                         |                                   |                            |
   |                       |                                     | 4k   | 512    | 1      | 57.39                          | 8.92                                      | 33.83                         | 0.05                          | 20.750                            | 8.920                      |
   |                       |                                     | 2    | 106.01 | 9.66   | 67.73                          | 0.15                                      | 6.710                         | 4.830                         |                                   |                            |
   |                       |                                     | 4    | 212.03 | 9.66   | 143.8                          | 0.17                                      | 6.020                         | 2.410                         |                                   |                            |
   |                       |                                     | 8k   | 512    | 1      | 88.64                          | 5.78                                      | 64.78                         | 0.05                          | 21.510                            | 5.780                      |
   |                       |                                     | 10k  | 3k     | 1      | 222.63                         | 13.48                                     | 79.55                         | 0.05                          | 20.960                            | 13.480                     |
   |                       |                                     | 20k  | 3k     | 1      | 311.26                         | 9.64                                      | 163.35                        | 0.05                          | 20.280                            | 9.640                      |
   |                       |                                     | 40k  | 3k     | 1      | 479.15                         | 6.26                                      | 327.33                        | 0.05                          | 18.550                            | 6.260                      |

1. # 测试结论

- 经测试，上述测试性能符合预期

1. # 附件

1. ## 硬件详细信息

hardware_info_20251208_115831.txt

1. ## 测试脚本

```Bash
import os
import csv
import json
import click
from glob import glob
from uuid import uuid4
from datetime import datetime
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

from evalscope.perf.main import run_perf_benchmark
from evalscope.perf.arguments import Arguments


def extract_json_to_csv(input_dir, output_csv, input_length, output_length, loop, concurrency: int = None):
    # 定义要提取的字段
    fields_to_extract = [
        "Average latency (s)",
        "Output token throughput (tok/s)",
        "Average time to first token (s)",
        "Average time per output token (s)",
    ]

    # CSV 表头
    headers = ["Input Length", "Output Length", "Loop", "Concurrency"] + fields_to_extract

    # 检查文件是否存在以决定写入模式
    file_exists = os.path.isfile(output_csv)

    # 收集当前 loop 的所有行数据
    all_rows = []

    # 遍历 benchmark_summary.json
    for json_file in glob(os.path.join(input_dir, "**", "benchmark_summary.json"), recursive=True):
        # 从路径中提取并发数
        dir_name = os.path.basename(os.path.dirname(json_file))
        if dir_name.startswith("parallel_"):
            concurrency = dir_name.split("_")[1]
        else:
            concurrency = concurrency or "1"  # 默认值

        with open(json_file, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"警告: 无法解析JSON文件: {json_file}")
                continue

        # 准备行数据
        row = [input_length, output_length, loop, int(concurrency)]  # 将并发数转为整数以便排序
        for field in fields_to_extract:
            row.append(data.get(field, ""))

        all_rows.append(row)

    # 按并发数从小到大排序
    all_rows.sort(key=lambda x: x[3])  # 索引 3 是并发数列

    # 处理 csv
    with open(output_csv, "a" if file_exists else "w", newline="") as csvfile:
        writer = csv.writer(csvfile)

        # 只在文件不存在时写入表头
        if not file_exists:
            writer.writerow(headers)

        # 写入排序后的所有行
        writer.writerows(all_rows)


def parse_csv_to_xlsx(in_csv, out_xlsx):

    # 1. 读数据
    df = pd.read_csv(in_csv)

    # 2. 计算每一轮的 Avg TPS 和 Avg throughput
    df["单轮次 Avg TPS"] = 1 / df["Average time per output token (s)"]
    df["单轮次平均单路吞吐（tok/s）"] = df["Output token throughput (tok/s)"] / df["Concurrency"]

    # 3. 计算相同工况所有轮次的 Avg TPS 和 Avg throughput
    avg_tps_all_round = (
        df.groupby(["Input Length", "Output Length", "Concurrency"])["单轮次 Avg TPS"]
        .mean()
        .rename("所有轮次平均 TPS")
        .reset_index()
    )

    df = df.merge(avg_tps_all_round, on=["Input Length", "Output Length", "Concurrency"], how="left")

    avg_tp_all_round = (
        df.groupby(["Input Length", "Output Length", "Concurrency"])["单轮次平均单路吞吐（tok/s）"]
        .mean()
        .rename("所有轮次平均单路吞吐（tok/s）")
        .reset_index()
    )
    df = df.merge(avg_tp_all_round, on=["Input Length", "Output Length", "Concurrency"], how="left")

    # 4. 写 Excel
    wb = Workbook()
    ws = wb.active
    for r in dataframe_to_rows(df, index=False, header=True):
        ws.append(r)

    ws.cell(row=1, column=df.columns.get_loc("所有轮次平均单路吞吐（tok/s）") + 1).column_letter

    wb.save(out_xlsx)
    print("Save the xlsx result to: ", out_xlsx)


@click.command(
    context_settings=dict(ignore_unknown_options=True, allow_extra_args=True, help_option_names=["-h", "--help"])
)
@click.option("--ip", type=str, default="127.0.0.1", show_default=True, help="AMaaS 管理 IP")
@click.option("--port", type=str, default=10011, show_default=True, help="AMaaS API 端口")
@click.option("--parallel", type=str, default="1 4", show_default=True, help="并发数, 请用引号引起来, 如 '1 4'")
@click.option("--number", type=str, default="1 4", show_default=True, help="请求数, 请用引号引起来, 如 '1 4'")
@click.option("--model", type=str, default="DeepSeek-R1", show_default=True, help="模型名称")
@click.option("--tokenizer-path", type=str, default="/mnt/data/models/DeepSeek-R1-GPTQ4-experts", show_default=True)
@click.option(
    "--api-key",
    type=str,
    default="AMES_89c2bb9cfba90d8b_5d7e9cc1d9f412b038bd11d7b559fd47",
    show_default=True,
    help="API Key, 从 AMaaS 上创建.",
)
@click.option("--input-length", type=int, default=128, show_default=True)
@click.option("--output-length", type=int, default=512, show_default=True)
@click.option("--read-timeout", type=int, default=600, show_default=True)
@click.option("--seed", type=int, default=42, show_default=True)
@click.option("--loop", type=int, default=1, show_default=True)
@click.option("--name", type=str, default="appauto-bench", show_default=True, help="任务名称")
@click.option("--debug", is_flag=True, show_default=True)
@click.option("--output-csv", type=str, default=None, show_default=True, help="输出 csv 文件名称, 不填写会默认填充")
@click.option("--output-xlsx", type=str, default=None, show_default=True, help="同时输出一份 xlsx 文件")
def runner(
    ip,
    port,
    parallel,
    number,
    model,
    api_key,
    input_length,
    output_length,
    read_timeout,
    tokenizer_path,
    seed,
    loop,
    name,
    debug,
    output_csv,
    output_xlsx,
):
    start_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_csv = f"{output_csv}.csv" if output_csv else f"{start_time}.csv"
    output_xlsx = output_csv.replace(".csv", ".xlsx")

    number = [int(n) for n in number.split()]
    parallel = [int(p) for p in parallel.split()]

    for i in range(0, int(loop)):
        print(f" loop {i} ".center(100, "*"))

        task_cfg = Arguments(
            parallel=parallel,
            number=number,
            model=model,
            url=f"http://{ip}:{int(port)}/v1/chat/completions",
            api_key=api_key,
            api="openai",
            dataset="random",
            min_tokens=int(output_length),
            max_tokens=int(output_length),
            read_timeout=int(read_timeout),
            prefix_length=0,
            min_prompt_length=int(input_length),
            max_prompt_length=int(input_length),
            tokenizer_path=tokenizer_path,
            extra_args={"ignore_eos": True},
            # swanlab_api_key="local",
            seed=int(seed),
            name=f"{name}-{i}",
            debug=debug,
            stream=True,
        )

        # len(number) != 1: ./outputs/20250709_142517/{name}/parallel_x_number_x/benchmark_summary.json
        # len(number) == 1: ./outputs/20250708_232819/{name}/benchmark_summary.json
        run_perf_benchmark(task_cfg)

        # 从 json 提取至 csv
        if len(number) == 1:
            # 读 json TODO 如何感知 timestamp? -> args.outputs_dir 可以感知到
            json_dir = task_cfg.outputs_dir  # 已经包括了 name

        elif len(number) > 1:
            json_dir = "/".join(task_cfg.outputs_dir.split("/")[:-2])

        extract_json_to_csv(
            json_dir, output_csv, input_length, output_length, i, None if len(parallel) > 1 else parallel[0]
        )

    print(f"Save the csv result to: {output_csv}")

    parse_csv_to_xlsx(output_csv, output_xlsx)


if __name__ == "__main__":
    runner(obj={})
(evalscope-py) (base) zkyd@zkyd46-4090:/mnt/data/
```