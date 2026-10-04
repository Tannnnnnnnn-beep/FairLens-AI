#!/usr/bin/env python3
"""
Plot Generator for 0/1 Knapsack Resource Allocation Benchmarks

Reads measured data from result/benchmark_results.csv and produces:
1. execution_time_vs_threads.png
2. speedup_vs_threads.png
3. efficiency_vs_threads.png
4. execution_time_vs_requirements.png
5. execution_time_vs_resources.png
"""

import csv
import os
import sys
import matplotlib.pyplot as plt

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSV_PATH = os.path.join(PROJECT_ROOT, "result", "benchmark_results.csv")
RESULT_DIR = os.path.join(PROJECT_ROOT, "result")


def load_csv(csv_path: str):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Benchmark CSV not found at {csv_path}. Run benchmark first.")

    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                "experiment_type": row["experiment_type"],
                "requirements": int(row["requirements"]),
                "resources": int(row["resources"]),
                "threads": int(row["threads"]),
                "sequential_time_seconds": float(row["sequential_time_seconds"]),
                "parallel_time_seconds": float(row["parallel_time_seconds"]),
                "speedup": float(row["speedup"]),
                "efficiency": float(row["efficiency"]),
                "sequential_benefit": int(row["sequential_benefit"]),
                "parallel_benefit": int(row["parallel_benefit"]),
                "result_match": row["result_match"],
                "repetitions": int(row["repetitions"]),
                "random_seed": int(row["random_seed"]),
            })
    return rows


def plot_execution_time_vs_threads(rows, output_dir):
    exp_c_rows = [r for r in rows if r["experiment_type"].startswith("Experiment C")]
    scales = ["Small", "Medium", "Large"]
    markers = {"Small": "o", "Medium": "s", "Large": "^"}
    colors = {"Small": "#1f77b4", "Medium": "#ff7f0e", "Large": "#2ca02c"}

    plt.figure(figsize=(8, 5.5), dpi=150)
    for scale in scales:
        scale_data = [r for r in exp_c_rows if f"({scale})" in r["experiment_type"]]
        if not scale_data:
            continue
        scale_data.sort(key=lambda x: x["threads"])
        threads = [d["threads"] for d in scale_data]
        times = [d["parallel_time_seconds"] for d in scale_data]
        label = f"{scale} (N={scale_data[0]['requirements']}, C={scale_data[0]['resources']})"
        plt.plot(threads, times, marker=markers[scale], color=colors[scale], linewidth=2, markersize=7, label=label)

    plt.title("Execution Time vs OpenMP Threads", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Number of OpenMP Threads", fontsize=11)
    plt.ylabel("Execution Time (seconds)", fontsize=11)
    plt.xticks([1, 2, 4, 8])
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(frameon=True)
    plt.tight_layout()
    out_path = os.path.join(output_dir, "execution_time_vs_threads.png")
    plt.savefig(out_path)
    plt.close()
    print(f"Saved: {out_path}")


def plot_speedup_vs_threads(rows, output_dir):
    exp_c_rows = [r for r in rows if r["experiment_type"].startswith("Experiment C")]
    scales = ["Small", "Medium", "Large"]
    markers = {"Small": "o", "Medium": "s", "Large": "^"}
    colors = {"Small": "#1f77b4", "Medium": "#ff7f0e", "Large": "#2ca02c"}

    plt.figure(figsize=(8, 5.5), dpi=150)
    threads_set = set()
    for scale in scales:
        scale_data = [r for r in exp_c_rows if f"({scale})" in r["experiment_type"]]
        if not scale_data:
            continue
        scale_data.sort(key=lambda x: x["threads"])
        threads = [d["threads"] for d in scale_data]
        threads_set.update(threads)
        speedups = [d["speedup"] for d in scale_data]
        label = f"{scale} (N={scale_data[0]['requirements']}, C={scale_data[0]['resources']})"
        plt.plot(threads, speedups, marker=markers[scale], color=colors[scale], linewidth=2, markersize=7, label=label)

    sorted_threads = sorted(list(threads_set))
    if sorted_threads:
        plt.plot(sorted_threads, sorted_threads, color="#d62728", linestyle="--", linewidth=1.8, label="Ideal Speedup")

    plt.title("Speedup vs OpenMP Threads (Strong Scaling)", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Number of OpenMP Threads", fontsize=11)
    plt.ylabel("Speedup (Sequential Time / Parallel Time)", fontsize=11)
    plt.xticks(sorted_threads if sorted_threads else [1, 2, 4, 8])
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(frameon=True)
    plt.tight_layout()
    out_path = os.path.join(output_dir, "speedup_vs_threads.png")
    plt.savefig(out_path)
    plt.close()
    print(f"Saved: {out_path}")


def plot_efficiency_vs_threads(rows, output_dir):
    exp_c_rows = [r for r in rows if r["experiment_type"].startswith("Experiment C")]
    scales = ["Small", "Medium", "Large"]
    markers = {"Small": "o", "Medium": "s", "Large": "^"}
    colors = {"Small": "#1f77b4", "Medium": "#ff7f0e", "Large": "#2ca02c"}

    plt.figure(figsize=(8, 5.5), dpi=150)
    threads_set = set()
    for scale in scales:
        scale_data = [r for r in exp_c_rows if f"({scale})" in r["experiment_type"]]
        if not scale_data:
            continue
        scale_data.sort(key=lambda x: x["threads"])
        threads = [d["threads"] for d in scale_data]
        threads_set.update(threads)
        efficiencies = [d["efficiency"] for d in scale_data]
        label = f"{scale} (N={scale_data[0]['requirements']}, C={scale_data[0]['resources']})"
        plt.plot(threads, efficiencies, marker=markers[scale], color=colors[scale], linewidth=2, markersize=7, label=label)

    sorted_threads = sorted(list(threads_set))
    if sorted_threads:
        plt.axhline(1.0, color="#d62728", linestyle="--", linewidth=1.8, label="Ideal Efficiency (1.0)")

    plt.title("Parallel Efficiency vs OpenMP Threads", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Number of OpenMP Threads", fontsize=11)
    plt.ylabel("Efficiency (Speedup / Threads)", fontsize=11)
    plt.xticks(sorted_threads if sorted_threads else [1, 2, 4, 8])
    plt.ylim(0.0, 1.2)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(frameon=True)
    plt.tight_layout()
    out_path = os.path.join(output_dir, "efficiency_vs_threads.png")
    plt.savefig(out_path)
    plt.close()
    print(f"Saved: {out_path}")


def plot_execution_time_vs_requirements(rows, output_dir):
    exp_a_rows = [r for r in rows if r["experiment_type"] == "Experiment A"]
    exp_a_rows.sort(key=lambda x: x["requirements"])

    reqs = [r["requirements"] for r in exp_a_rows]
    seq_times = [r["sequential_time_seconds"] for r in exp_a_rows]
    par_times = [r["parallel_time_seconds"] for r in exp_a_rows]
    threads = exp_a_rows[0]["threads"] if exp_a_rows else 4
    capacity = exp_a_rows[0]["resources"] if exp_a_rows else 40000

    plt.figure(figsize=(8, 5.5), dpi=150)
    plt.plot(reqs, seq_times, marker="o", color="#d62728", linewidth=2, markersize=7, label="Sequential DP")
    plt.plot(reqs, par_times, marker="s", color="#1f77b4", linewidth=2, markersize=7, label=f"OpenMP Parallel DP ({threads} Threads)")

    plt.title(f"Execution Time vs Requirements (Fixed Capacity = {capacity:,})", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Number of Requirements (N)", fontsize=11)
    plt.ylabel("Execution Time (seconds)", fontsize=11)
    plt.xticks(reqs)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(frameon=True)
    plt.tight_layout()
    out_path = os.path.join(output_dir, "execution_time_vs_requirements.png")
    plt.savefig(out_path)
    plt.close()
    print(f"Saved: {out_path}")


def plot_execution_time_vs_resources(rows, output_dir):
    exp_b_rows = [r for r in rows if r["experiment_type"] == "Experiment B"]
    exp_b_rows.sort(key=lambda x: x["resources"])

    caps = [r["resources"] for r in exp_b_rows]
    seq_times = [r["sequential_time_seconds"] for r in exp_b_rows]
    par_times = [r["parallel_time_seconds"] for r in exp_b_rows]
    threads = exp_b_rows[0]["threads"] if exp_b_rows else 4
    reqs = exp_b_rows[0]["requirements"] if exp_b_rows else 1000

    plt.figure(figsize=(8, 5.5), dpi=150)
    plt.plot(caps, seq_times, marker="o", color="#d62728", linewidth=2, markersize=7, label="Sequential DP")
    plt.plot(caps, par_times, marker="s", color="#1f77b4", linewidth=2, markersize=7, label=f"OpenMP Parallel DP ({threads} Threads)")

    plt.title(f"Execution Time vs Resource Capacity (Fixed Requirements = {reqs:,})", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Resource Capacity (C)", fontsize=11)
    plt.ylabel("Execution Time (seconds)", fontsize=11)
    plt.xticks(caps, [f"{c:,}" for c in caps], rotation=15)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend(frameon=True)
    plt.tight_layout()
    out_path = os.path.join(output_dir, "execution_time_vs_resources.png")
    plt.savefig(out_path)
    plt.close()
    print(f"Saved: {out_path}")


def main():
    try:
        rows = load_csv(CSV_PATH)
        os.makedirs(RESULT_DIR, exist_ok=True)
        print("Generating benchmark plots...")
        plot_execution_time_vs_threads(rows, RESULT_DIR)
        plot_speedup_vs_threads(rows, RESULT_DIR)
        plot_efficiency_vs_threads(rows, RESULT_DIR)
        plot_execution_time_vs_requirements(rows, RESULT_DIR)
        plot_execution_time_vs_resources(rows, RESULT_DIR)
        print("All 5 plots successfully generated in result/ folder.")
    except Exception as e:
        print(f"Error generating plots: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
