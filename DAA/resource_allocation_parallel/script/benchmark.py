#!/usr/bin/env python3
"""
Benchmark Runner for 0/1 Knapsack Resource Allocation

Runs controlled experiments comparing Sequential DP and OpenMP Parallel DP:
- Experiment A: Varying requirements (N) with fixed capacity (C)
- Experiment B: Varying capacity (C) with fixed requirements (N)
- Experiment C: Varying thread counts (1, 2, 4, 8) across small, medium, large inputs
"""

import csv
import os
import re
import statistics
import subprocess
import sys

# Ensure MSYS2 UCRT64 toolchain is in PATH on Windows
MSYS2_PATH = r"C:\msys64\ucrt64\bin"
if os.path.exists(MSYS2_PATH) and MSYS2_PATH not in os.environ.get("PATH", ""):
    os.environ["PATH"] = MSYS2_PATH + os.pathsep + os.environ.get("PATH", "")

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SEQ_EXE = os.path.join(PROJECT_ROOT, "seq.exe")
PAR_EXE = os.path.join(PROJECT_ROOT, "parallel_openmp.exe")
CSV_PATH = os.path.join(PROJECT_ROOT, "result", "benchmark_results.csv")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


def parse_program_output(output_text: str):
    benefit_match = re.search(r"Total benefit\s*:\s*(\d+)", output_text)
    time_match = re.search(r"Execution time\s*:\s*([\d\.]+)\s*seconds", output_text)

    if not benefit_match or not time_match:
        raise ValueError(
            f"Failed to parse output format. Got:\n{output_text}"
        )

    benefit = int(benefit_match.group(1))
    exec_time = float(time_match.group(1))
    return benefit, exec_time


def generate_input_file(filepath: str, n: int, c: int, seed: int):
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    cmd = [
        sys.executable,
        os.path.join(PROJECT_ROOT, "script", "generate_input.py"),
        "--requirements", str(n),
        "--resources", str(c),
        "--seed", str(seed),
        "--output", filepath
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def run_single(exe_cmd: list) -> tuple:
    result = subprocess.run(
        exe_cmd,
        check=True,
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )
    return parse_program_output(result.stdout)


def benchmark_configuration(
    experiment_type: str,
    n: int,
    c: int,
    threads: int,
    input_file: str,
    repetitions: int = 3,
    seed: int = 42
) -> dict:
    print(f"[{experiment_type}] N={n}, C={c}, Threads={threads} ({repetitions} runs)...", end="", flush=True)

    seq_times = []
    seq_benefits = []
    for _ in range(repetitions):
        benefit, exec_time = run_single([SEQ_EXE, input_file, "--no-reconstruct"])
        seq_benefits.append(benefit)
        seq_times.append(exec_time)

    par_times = []
    par_benefits = []
    for _ in range(repetitions):
        benefit, exec_time = run_single([PAR_EXE, input_file, str(threads), "--no-reconstruct"])
        par_benefits.append(benefit)
        par_times.append(exec_time)

    seq_benefit = seq_benefits[0]
    par_benefit = par_benefits[0]
    result_match = (seq_benefit == par_benefit)

    if not result_match:
        print(" FAILED (Mismatch!)")
        raise RuntimeError(
            f"Correctness failure for N={n}, C={c}: Seq={seq_benefit} != Par={par_benefit}"
        )

    median_seq_time = statistics.median(seq_times)
    median_par_time = statistics.median(par_times)

    # Avoid zero division if timer resolution is small
    effective_par_time = max(median_par_time, 1e-7)
    effective_seq_time = max(median_seq_time, 1e-7)
    speedup = effective_seq_time / effective_par_time
    efficiency = speedup / threads

    print(f" Done. Seq={median_seq_time:.5f}s, Par={median_par_time:.5f}s, Speedup={speedup:.2f}x")

    return {
        "experiment_type": experiment_type,
        "requirements": n,
        "resources": c,
        "threads": threads,
        "sequential_time_seconds": round(median_seq_time, 6),
        "parallel_time_seconds": round(median_par_time, 6),
        "speedup": round(speedup, 4),
        "efficiency": round(efficiency, 4),
        "sequential_benefit": seq_benefit,
        "parallel_benefit": par_benefit,
        "result_match": "PASS" if result_match else "FAIL",
        "repetitions": repetitions,
        "random_seed": seed
    }


def main():
    if not os.path.exists(SEQ_EXE) or not os.path.exists(PAR_EXE):
        print(f"Error: Executables missing. Please compile seq.exe and parallel_openmp.exe first.", file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.join(PROJECT_ROOT, "result"), exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    results = []
    fixed_seed = 42

    print("====================================================")
    print(" 0/1 Knapsack Resource Allocation Benchmark")
    print("====================================================\n")

    # ----------------------------------------------------
    # Experiment A: Increase requirements with fixed capacity
    # ----------------------------------------------------
    fixed_capacity_a = 40000
    requirements_a = [250, 500, 1000, 1500, 2000]
    threads_a = 4

    print("--- Running Experiment A: Varying Requirements (Fixed Capacity=40000, Threads=4) ---")
    for req in requirements_a:
        filename = os.path.join(DATA_DIR, f"bench_a_{req}_{fixed_capacity_a}.txt")
        generate_input_file(filename, req, fixed_capacity_a, fixed_seed)
        row = benchmark_configuration(
            experiment_type="Experiment A",
            n=req,
            c=fixed_capacity_a,
            threads=threads_a,
            input_file=filename,
            repetitions=3,
            seed=fixed_seed
        )
        results.append(row)

    print()

    # ----------------------------------------------------
    # Experiment B: Increase capacity with fixed requirements
    # ----------------------------------------------------
    fixed_requirements_b = 1000
    capacities_b = [10000, 20000, 40000, 60000, 80000]
    threads_b = 4

    print("--- Running Experiment B: Varying Capacity (Fixed Requirements=1000, Threads=4) ---")
    for cap in capacities_b:
        filename = os.path.join(DATA_DIR, f"bench_b_{fixed_requirements_b}_{cap}.txt")
        generate_input_file(filename, fixed_requirements_b, cap, fixed_seed)
        row = benchmark_configuration(
            experiment_type="Experiment B",
            n=fixed_requirements_b,
            c=cap,
            threads=threads_b,
            input_file=filename,
            repetitions=3,
            seed=fixed_seed
        )
        results.append(row)

    print()

    # ----------------------------------------------------
    # Experiment C: Increase OpenMP thread count
    # Small, medium, and large practical inputs across 1, 2, 4, 8 threads
    # ----------------------------------------------------
    test_scales = [
        ("Small", 500, 20000),
        ("Medium", 1000, 40000),
        ("Large", 1500, 60000),
    ]
    thread_counts = [1, 2, 4, 8]

    print("--- Running Experiment C: Varying Thread Counts (1, 2, 4, 8) ---")
    for scale_name, n_val, c_val in test_scales:
        filename = os.path.join(DATA_DIR, f"bench_c_{scale_name.lower()}_{n_val}_{c_val}.txt")
        generate_input_file(filename, n_val, c_val, fixed_seed)
        for t in thread_counts:
            row = benchmark_configuration(
                experiment_type=f"Experiment C ({scale_name})",
                n=n_val,
                c=c_val,
                threads=t,
                input_file=filename,
                repetitions=3,
                seed=fixed_seed
            )
            results.append(row)

    # ----------------------------------------------------
    # Write CSV
    # ----------------------------------------------------
    fieldnames = [
        "experiment_type",
        "requirements",
        "resources",
        "threads",
        "sequential_time_seconds",
        "parallel_time_seconds",
        "speedup",
        "efficiency",
        "sequential_benefit",
        "parallel_benefit",
        "result_match",
        "repetitions",
        "random_seed",
    ]

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print("\n====================================================")
    print(f" Benchmark complete. {len(results)} configurations evaluated.")
    print(f" Results written to: {CSV_PATH}")
    print("====================================================")


if __name__ == "__main__":
    main()
