#include "common.hpp"

#include <algorithm>
#include <chrono>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

AllocationResult solveSequential(
    const InputData& data,
    bool reconstructSelection
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

    // Measure only core DP computation time
    const auto start = std::chrono::high_resolution_clock::now();

    for (int i = 0; i < n; ++i) {
        const int cost = data.requirements[i].cost;
        const long long benefit = data.requirements[i].benefit;

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

        std::swap(prev, curr);
    }

    const auto end = std::chrono::high_resolution_clock::now();
    const double executionTimeSeconds =
        std::chrono::duration<double>(end - start).count();

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

void printSequentialResult(
    const InputData& data,
    const AllocationResult& result,
    bool reconstructSelection
) {
    std::cout
        << "====================================================\n"
        << " Sequential Knapsack Allocation Result\n"
        << "====================================================\n"
        << "Algorithm              : 0/1 Knapsack Dynamic Programming\n"
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
    bool reconstructSelection = true;

    if (argc == 1) {
        std::cout
            << "====================================================\n"
            << " Sequential Resource Allocation System\n"
            << "====================================================\n\n"
            << "Enter input file path:\n"
            << "Press Enter to use: data/sample_ip.txt\n";

        std::string line;
        if (!std::getline(std::cin, line) || line.empty()) {
            inputFile = "data/sample_ip.txt";
        } else {
            inputFile = line;
        }
    } else if (argc == 2 || argc == 3) {
        inputFile = argv[1];
        if (argc == 3) {
            const std::string opt = argv[2];
            if (opt == "--no-reconstruct") {
                reconstructSelection = false;
            } else {
                std::cerr << "Error: Unknown option '" << opt << "'.\n"
                          << "Usage: " << argv[0] << " <input_file> [--no-reconstruct]\n";
                return 1;
            }
        }
    } else {
        std::cerr << "Usage: " << argv[0] << " <input_file> [--no-reconstruct]\n";
        return 1;
    }

    try {
        const InputData data = readInputFile(inputFile);
        const AllocationResult result = solveSequential(data, reconstructSelection);
        printSequentialResult(data, result, reconstructSelection);
        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "Error: " << ex.what() << '\n';
        return 1;
    }
}