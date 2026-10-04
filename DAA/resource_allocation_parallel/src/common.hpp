#ifndef COMMON_HPP
#define COMMON_HPP

#include <chrono>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

struct Requirement {
    int cost;
    long long benefit;
};

struct InputData {
    int numberOfRequirements;
    int capacity;
    std::vector<Requirement> requirements;
};

struct AllocationResult {
    long long optimalBenefit;
    int resourcesUsed;
    std::vector<int> selectedRequirements;
    double executionTimeSeconds;
};

inline InputData readInputFile(const std::string& filename) {
    std::ifstream inputFile(filename);

    if (!inputFile.is_open()) {
        throw std::runtime_error(
            "Unable to open input file: " + filename
        );
    }

    InputData data;

    if (!(inputFile >> data.numberOfRequirements >> data.capacity)) {
        throw std::runtime_error(
            "Invalid input format: expected number of requirements (N) "
            "and capacity (C) on the first line."
        );
    }

    if (data.numberOfRequirements <= 0) {
        throw std::runtime_error(
            "Invalid number of requirements: N must be greater than 0."
        );
    }

    if (data.capacity < 0) {
        throw std::runtime_error(
            "Invalid capacity: capacity must be greater than or equal to 0."
        );
    }

    data.requirements.reserve(
        static_cast<std::size_t>(data.numberOfRequirements)
    );

    for (int i = 0; i < data.numberOfRequirements; ++i) {
        Requirement requirement{};

        if (!(inputFile >> requirement.cost >> requirement.benefit)) {
            throw std::runtime_error(
                "Invalid input format: expected cost and benefit for "
                "requirement " + std::to_string(i + 1) + "."
            );
        }

        if (requirement.cost <= 0) {
            throw std::runtime_error(
                "Invalid cost for requirement " +
                std::to_string(i + 1) +
                ": cost must be strictly positive (greater than 0)."
            );
        }

        if (requirement.benefit < 0) {
            throw std::runtime_error(
                "Invalid benefit for requirement " +
                std::to_string(i + 1) +
                ": benefit must be non-negative."
            );
        }

        data.requirements.push_back(requirement);
    }

    std::string trailing;
    if (inputFile >> trailing) {
        throw std::runtime_error(
            "Invalid input format: extra tokens found after reading " +
            std::to_string(data.numberOfRequirements) + " requirements."
        );
    }

    return data;
}

inline void printBasicResult(
    const std::string& algorithmName,
    const InputData& input,
    const AllocationResult& result
) {
    std::cout << "\n========================================\n";
    std::cout << "        Resource Allocation Result\n";
    std::cout << "========================================\n";
    std::cout << "Algorithm              : " << algorithmName << '\n';
    std::cout << "Number of Requirements : "
              << input.numberOfRequirements << '\n';
    std::cout << "Resource Capacity      : "
              << input.capacity << '\n';
    std::cout << "Resources Used         : "
              << result.resourcesUsed << '\n';
    std::cout << "Optimal Benefit        : "
              << result.optimalBenefit << '\n';
    std::cout << "Execution Time         : "
              << std::fixed << std::setprecision(6)
              << result.executionTimeSeconds << " seconds\n";
    std::cout << "========================================\n";
}

#endif // COMMON_HPP