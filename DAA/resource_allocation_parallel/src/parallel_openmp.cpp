#include "common.hpp"
#include <omp.h>

#include <algorithm>
#include <chrono>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

AllocationResult solveParallelOpenMP(
    const InputData& data,
    int threadCount,
    bool reconstructSelection,
    int* actualThreadsUsed = nullptr
) {
    const int n = data.numberOfRequirements;
    const int capacity = data.capacity;

    std::vector<long long> prev(static_cast<std::size_t>(capacity) + 1, 0);
    std::vector<long long> curr(static_cast<std::size_t>(capacity) + 1, 0);

    std::vector<std::vector<unsigned char>> decisions;
    if (reconstructSelection) {
        decisions.assign(
            static_cast<std::size_t>(n),
            std::vector<unsigned char>(static_cast<std::size_t>(capacity) + 1, 0)
        );
    }

    omp_set_num_threads(threadCount);
    int actualThreads = threadCount;

    // Measure only core DP computation time
    const auto start = std::chrono::high_resolution_clock::now();

    #pragma omp parallel
    {
        #pragma omp single
        {
            actualThreads = omp_get_num_threads();
        }

        // Outer requirement loop remains sequential (row i depends on row i-1)
        for (int i = 0; i < n; ++i) {
            const int cost = data.requirements[i].cost;
            const long long benefit = data.requirements[i].benefit;

            // Inner capacity loop is parallelized across threads
            #pragma omp for schedule(static)
            for (int c = 0; c <= capacity; ++c) {
                const long long notTake = prev[c];
                long long take = notTake;

                if (cost <= c) {
                    take = benefit + prev[c - cost];
                }

                curr[c] = (take > notTake) ? take : notTake;

                if (reconstructSelection && cost <= c && take > notTake) {
                    decisions[i][c] = 1;
                }
            }

            // Exactly one thread swaps the rows; implicit barrier ensures completion
            #pragma omp single
            {
                std::swap(prev, curr);
            }
        }
    }

    const auto end = std::chrono::high_resolution_clock::now();
    const double executionTimeSeconds =
        std::chrono::duration<double>(end - start).count();

    if (actualThreadsUsed != nullptr) {
        *actualThreadsUsed = actualThreads;
    }

    AllocationResult result{};
    result.optimalBenefit = prev[capacity];
    result.resourcesUsed = 0;
    result.executionTimeSeconds = executionTimeSeconds;

    if (reconstructSelection) {
        int remainingCapacity = capacity;
        for (int i = n - 1; i >= 0; --i) {
            if (decisions[i][remainingCapacity] != 0) {
                result.selectedRequirements.push_back(i);
                result.resourcesUsed += data.requirements[i].cost;
                remainingCapacity -= data.requirements[i].cost;
            }
        }
        std::reverse(
            result.selectedRequirements.begin(),
            result.selectedRequirements.end()
        );
    }

    return result;
}

void printParallelResult(
    const InputData& data,
    const AllocationResult& result,
    int actualThreadsUsed,
    bool reconstructSelection
) {
    std::cout
        << "====================================================\n"
        << " Parallel Knapsack Allocation Result\n"
        << "====================================================\n"
        << "Algorithm              : 0/1 Knapsack Dynamic Programming\n"
        << "Parallel model         : OpenMP shared-memory parallelization\n"
        << "Threads used           : " << actualThreadsUsed << '\n'
        << "Requirements           : " << data.numberOfRequirements << '\n'
        << "Available resources    : " << data.capacity << '\n';

    if (!reconstructSelection) {
        std::cout << "Selected requirements  : Not reconstructed\n";
        std::cout << "Resources allocated    : Not reconstructed\n";
    } else {
        std::cout << "Selected requirements  : ";
        if (result.selectedRequirements.empty()) {
            std::cout << "None\n";
        } else {
            for (std::size_t i = 0; i < result.selectedRequirements.size(); ++i) {
                if (i > 0) {
                    std::cout << ", ";
                }
                std::cout << "R" << (result.selectedRequirements[i] + 1);
            }
            std::cout << '\n';
        }
        std::cout << "Resources allocated    : " << result.resourcesUsed
                  << " / " << data.capacity << '\n';
    }

    std::cout << "Total benefit          : " << result.optimalBenefit << '\n'
              << "Execution time         : " << std::fixed << std::setprecision(6)
              << result.executionTimeSeconds << " seconds\n"
              << "====================================================\n";
}

int main(int argc, char* argv[]) {
    std::string inputFile;
    int threadCount = 4;
    bool reconstructSelection = true;

    if (argc == 1) {
        std::cout
            << "====================================================\n"
            << " Parallel OpenMP Resource Allocation System\n"
            << "====================================================\n\n"
            << "Enter input file path:\n"
            << "Press Enter to use: data/sample_ip.txt\n";

        std::string line;
        if (!std::getline(std::cin, line) || line.empty()) {
            inputFile = "data/sample_ip.txt";
        } else {
            inputFile = line;
        }

        std::cout << "\nEnter number of threads:\n"
                  << "Press Enter to use: 4\n";

        if (!std::getline(std::cin, line) || line.empty()) {
            threadCount = 4;
        } else {
            try {
                std::size_t pos = 0;
                threadCount = std::stoi(line, &pos);
                if (pos != line.length() || threadCount <= 0) {
                    std::cerr << "Error: Thread count must be a positive integer.\n";
                    return 1;
                }
            } catch (...) {
                std::cerr << "Error: Invalid thread count.\n";
                return 1;
            }
        }
    } else if (argc == 3 || argc == 4) {
        inputFile = argv[1];

        try {
            std::size_t pos = 0;
            std::string tStr = argv[2];
            threadCount = std::stoi(tStr, &pos);
            if (pos != tStr.length() || threadCount <= 0) {
                std::cerr << "Error: Thread count must be a positive integer.\n";
                return 1;
            }
        } catch (...) {
            std::cerr << "Error: Invalid thread count.\n";
            return 1;
        }

        if (argc == 4) {
            const std::string opt = argv[3];
            if (opt == "--no-reconstruct") {
                reconstructSelection = false;
            } else {
                std::cerr << "Error: Unknown option '" << opt << "'.\n"
                          << "Usage: " << argv[0] << " <input_file> <threads> [--no-reconstruct]\n";
                return 1;
            }
        }
    } else {
        std::cerr << "Usage: " << argv[0] << " <input_file> <threads> [--no-reconstruct]\n";
        return 1;
    }

    try {
        const InputData data = readInputFile(inputFile);
        int actualThreadsUsed = 0;
        const AllocationResult result = solveParallelOpenMP(
            data,
            threadCount,
            reconstructSelection,
            &actualThreadsUsed
        );
        printParallelResult(data, result, actualThreadsUsed, reconstructSelection);
        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "Error: " << ex.what() << '\n';
        return 1;
    }
}
