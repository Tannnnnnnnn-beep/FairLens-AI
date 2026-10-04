# Performance Analysis of Sequential and Parallel Resource Allocation Using 0/1 Knapsack Dynamic Programming and OpenMP

## 1. Problem Statement

> **Faculty Problem Statement:**  
> *"Develop a computational solution for allocating limited resources among a large number of competing requirements. Evaluate its performance for increasing numbers of resources and requirements."*

In modern enterprise resource planning, cloud computing infrastructure, and public-sector budgeting, organizations must distribute limited resources (e.g., budget, CPU cores, memory, raw materials) across competing project proposals or requirements. Each requirement has a specific resource demand and an expected business return or priority.

---

## 2. Problem Formulation as 0/1 Knapsack

The resource allocation problem maps directly to the classical **0/1 Knapsack Problem**:

- **Requirements ($N$):** Each competing proposal $i \in \{1, 2, \dots, N\}$ can either be selected ($x_i = 1$) or skipped ($x_i = 0$). Fractional selection is not permitted.
- **Resource Cost ($\text{cost}_i$):** The amount of resource required to fulfill requirement $i$ ($\text{cost}_i > 0$).
- **Benefit ($\text{benefit}_i$):** The utility, priority, or value achieved by fulfilling requirement $i$ ($\text{benefit}_i \ge 0$).
- **Resource Capacity ($C$):** Total available resource budget ($C \ge 0$).
- **Objective:** Maximize total benefit without exceeding resource capacity:

$$\max \sum_{i=1}^{N} \text{benefit}_i \cdot x_i \quad \text{subject to} \quad \sum_{i=1}^{N} \text{cost}_i \cdot x_i \le C, \quad x_i \in \{0, 1\}$$

---

## 3. Input Format

Input files follow a standard text structure:

- **Line 1:** Two space-separated integers: `N` (number of requirements) and `C` (resource capacity).
- **Next $N$ lines:** Two space-separated integers per line: `cost` (resource required) and `benefit` (value achieved).

### Example (`data/sample_ip.txt`)
```text
6 10
6 30
3 14
4 16
2 9
5 20
1 7
```

**Interpretation:**
- 6 requirements competing for a maximum capacity of 10 resource units.
- Requirement 1 costs 6 units and provides 30 benefit.
- Requirement 2 costs 3 units and provides 14 benefit, etc.

---

## 4. Sequential Dynamic Programming

The problem is solved using bottom-up Dynamic Programming with two rows (`prev` and `curr`) to achieve space optimization.

### Recurrence Relation

The recurrence relation used to determine the optimal allocation is:

```text
If cost[i] > c:
    dp[i][c] = dp[i - 1][c]

Otherwise:
    dp[i][c] = max(
        dp[i - 1][c],
        benefit[i] + dp[i - 1][c - cost[i]]
    )
```

### Two-Row Memory Optimization
- Rather than maintaining an $N \times (C+1)$ matrix, only two rows of size $C + 1$ are needed:
  - `prev[c]`: Optimal benefit for capacity $c$ using items up to $i - 1$.
  - `curr[c]`: Optimal benefit for capacity $c$ using items up to $i$.
- After filling `curr` for requirement $i$, `std::swap(prev, curr)` prepares the state for the next requirement.

---

## 5. OpenMP Parallel Strategy

Shared-memory parallelization is implemented using OpenMP (`#pragma omp`).

### Why Only the Capacity Loop is Parallelized
1. **Outer Loop (Requirements $1 \dots N$):** Must execute sequentially. DP row $i$ strictly depends on row $i - 1$. Iterations cannot run concurrently without violating data flow dependencies.
2. **Inner Loop (Capacities $0 \dots C$):** Can be safely parallelized. For a fixed requirement $i$, computing `curr[c]` reads exclusively from `prev[c]` and `prev[c - cost]`, and writes solely to index `c` of `curr`.

### Thread Structure
- A single parallel region (`#pragma omp parallel`) wraps the entire outer loop, avoiding the recurring overhead of spawning and destroying thread pools on every item iteration.
- The inner capacity loop uses `#pragma omp for schedule(static)` to divide the range $[0, C]$ evenly among active threads.
- Exactly one thread performs `std::swap(prev, curr)` inside `#pragma omp single`. The implicit barrier at the end of `#pragma omp for` and `#pragma omp single` guarantees all threads synchronize before advancing to requirement $i + 1$.

---

## 6. Race-Condition Safety

The parallel implementation is race-free by construction without needing locks, mutexes, or atomic instructions:
- **Read-Only Previous Row (`prev`):** All threads only read from `prev`. No thread writes to `prev` during capacity computation.
- **Disjoint Writes to Current Row (`curr`):** Thread $T_k$ writes only to elements $c$ assigned to its static chunk in `curr[c]`. No two threads write to the same memory location.
- **Disjoint Decision Matrix:** If path reconstruction is enabled, thread writes to `decisions[i][c]` are similarly separated by capacity index $c$.
- **Barriers:** Implicit barriers ensure all writes to `curr` finish before the row swap occurs, and the swap completes before any thread reads `prev` in the next iteration.

---

## 7. Correctness Verification

A standalone verification tool (`src/verify.cpp`) confirms that the sequential and parallel algorithms produce identical results:
- Runs both implementations across 1, 2, 4, and 8 threads.
- Verifies:
  1. Maximum total benefit matches exactly.
  2. Selected requirement set matches exactly.
  3. Total resources allocated match exactly.
- Tests include:
  - Standard sample input (`data/sample_ip.txt`)
  - Zero-capacity allocation (`data/zero_cap.txt`)
  - No-item-fits case (`data/no_itemfit.txt`)
  - Single-item case (`data/oneitem.txt`)
  - Repeated/equal values (`data/repeated_values.txt`)
  - Small, medium, and large synthetic datasets (`data/ipsmall.txt`, `data/ipmedium.txt`, `data/iplarge.txt`)

---

## 8. Complexity Analysis

| Metric | Sequential DP | OpenMP Parallel DP ($P$ threads) |
|---|---|---|
| **Time Complexity** | $O(N \times C)$ | $O\left(N \times \frac{C}{P}\right) + \text{synchronization overhead}$ |
| **Space Complexity** | $O(C)$ (computation only) / $O(N \times C)$ (with reconstruction) | $O(C)$ (computation only) / $O(N \times C)$ (with reconstruction) |

> **Computational Note:** The 0/1 Knapsack DP algorithm is **pseudo-polynomial**. Performance depends directly on the product $N \times C$. As verified by measured benchmark data in `result/benchmark_results.csv`, practical workloads run efficiently (e.g., measured sequential runtime is $0.038468\text{ s}$ for $N = 2000, C = 40000$, and $0.038639\text{ s}$ for $N = 1000, C = 80000$). However, arbitrary combinations such as $N = 10^6, C = 10^6$ require $10^{12}$ operations, which is computationally intractable for exact dynamic programming.

---

## 9. Folder Structure

```text
resource_allocation_parallel/
├── .gitignore
├── README.md
├── backup_before_knapsack_migration/   # Safety backups of original files
│   ├── common.hpp.backup
│   ├── parallel_openmp.cpp.backup
│   ├── seq.cpp.backup
│   └── verify.cpp.backup
├── data/                               # Sample, edge-case, and benchmark inputs
│   ├── sample_ip.txt
│   ├── zero_cap.txt
│   ├── no_itemfit.txt
│   ├── oneitem.txt
│   ├── repeated_values.txt
│   ├── ipsmall.txt
│   ├── ipmedium.txt
│   └── iplarge.txt
├── result/                             # Benchmark CSV and generated plots
│   ├── benchmark_results.csv
│   ├── execution_time_vs_threads.png
│   ├── speedup_vs_threads.png
│   ├── efficiency_vs_threads.png
│   ├── execution_time_vs_requirements.png
│   └── execution_time_vs_resources.png
├── script/                             # Automation scripts
│   ├── generate_input.py
│   ├── benchmark.py
│   └── plot_results.py
└── src/                                # C++ source files
    ├── common.hpp
    ├── seq.cpp
    ├── parallel_openmp.cpp
    ├── verify.cpp
    └── menu.cpp
```

---

## 10. Software Requirements

- **C++ Compiler:** GCC with C++17 support and OpenMP (`-fopenmp`).
- **Python:** Python 3.8+ with `matplotlib` for graph generation.
- **Operating System:** Windows 10/11 (or Linux / macOS).

### Windows MSYS2 UCRT64 Setup Note
On Windows, use the modern **MSYS2 UCRT64** GCC toolchain (`C:\msys64\ucrt64\bin`). MinGW.org GCC 6.x is outdated and lacks full modern OpenMP runtime DLLs.
To ensure the compiler and OpenMP runtime DLLs (`libgomp-1.dll`, `libwinpthread-1.dll`) are accessible, prepend the UCRT64 binary path in your terminal:

```powershell
$env:PATH = "C:\msys64\ucrt64\bin;" + $env:PATH
```

---

## 11. Compilation Commands

From the project root directory:

```bash
# Sequential binary
g++ -O3 -std=c++17 src/seq.cpp -o seq.exe

# Parallel OpenMP binary
g++ -O3 -std=c++17 -fopenmp src/parallel_openmp.cpp -o parallel_openmp.exe

# Verification binary
g++ -O3 -std=c++17 -fopenmp src/verify.cpp -o verify.exe
```

---

## 12. Run Commands

### Sequential Execution
```bash
# With reconstructed item list (default)
.\seq.exe data/sample_ip.txt

# DP computation only (no reconstruction)
.\seq.exe data/sample_ip.txt --no-reconstruct

# Interactive mode (prompts for input file, Enter for default)
.\seq.exe
```

### Parallel Execution
```bash
# With 4 threads and reconstruction
.\parallel_openmp.exe data/sample_ip.txt 4

# DP computation only with 8 threads
.\parallel_openmp.exe data/sample_ip.txt 8 --no-reconstruct

# Interactive mode (prompts for input file and thread count)
.\parallel_openmp.exe
```

### Verification Command
```bash
# Verify a specific input file
.\verify.exe data/sample_ip.txt

# Run the complete test suite across all edge cases and threads
.\verify.exe --all
```

---

## 13. Input Generation Command

Generate reproducible datasets using `script/generate_input.py`:

```bash
python script/generate_input.py --requirements 1000 --resources 40000 --seed 42 --output data/medium_input.txt
```

---

## 14. Benchmark and Graph Commands

### Run Controlled Experiments
```bash
python script/benchmark.py
```
This executes:
- **Experiment A:** Requirements $N \in [250, 2000]$, fixed capacity $C = 40,000$, 4 threads.
- **Experiment B:** Capacity $C \in [10000, 80000]$, fixed requirements $N = 1000$, 4 threads.
- **Experiment C:** Thread counts $T \in [1, 2, 4, 8]$ across Small, Medium, and Large inputs.
- All runs are repeated 3 times; the median time is recorded in `result/benchmark_results.csv`.

### Generate Plots
```bash
python script/plot_results.py
```
Generates 5 publication-ready PNG charts in `result/`:
1. `execution_time_vs_threads.png`
2. `speedup_vs_threads.png` (with dashed Ideal Speedup reference)
3. `efficiency_vs_threads.png` (with dashed Ideal Efficiency reference)
4. `execution_time_vs_requirements.png`
5. `execution_time_vs_resources.png`

---

## 15. Performance Formulas & Scaling Analysis

### Speedup Formula
$$S(P) = \frac{T_{\text{sequential}}}{T_{\text{parallel}}(P)}$$

Where $T_{\text{sequential}}$ is the execution time of the sequential implementation, and $T_{\text{parallel}}(P)$ is the execution time using $P$ OpenMP threads.

### Efficiency Formula
$$E(P) = \frac{S(P)}{P} = \frac{T_{\text{sequential}}}{P \times T_{\text{parallel}}(P)}$$

### Scalability Limits & Realities
- **Amdahl's Law:** The outer loop must remain sequential to satisfy dynamic programming dependencies. Synchronization barriers between rows introduce minor latency.
- **Memory Bandwidth:** For 0/1 knapsack, the inner loop performs very few arithmetic operations per memory access (reading `prev[c]` and writing `curr[c]`). At higher thread counts, memory bus contention becomes the primary bottleneck rather than CPU ALU throughput.
- **Problem Size Granularity:** For small capacities ($C \le 10,000$), thread scheduling and barrier synchronization overhead outweigh parallel work. OpenMP achieves its best speedup on larger capacities ($C \ge 40,000$) where each thread receives a substantial capacity chunk.
