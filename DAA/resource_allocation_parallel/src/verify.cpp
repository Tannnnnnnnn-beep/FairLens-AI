#include "common.hpp"
#include <omp.h>

#include <algorithm>
#include <iostream>
#include <string>
#include <vector>

struct DPOutput {
    long long benefit;
    int resourcesUsed;
    std::vector<int> selected;
};

DPOutput runSequential(const InputData& data, bool reconstruct = true) {
    const int n = data.numberOfRequirements;
    const int capacity = data.capacity;

    std::vector<long long> prev(static_cast<std::size_t>(capacity) + 1, 0);
    std::vector<long long> curr(static_cast<std::size_t>(capacity) + 1, 0);

    std::vector<std::vector<unsigned char>> decisions;
    if (reconstruct) {
        decisions.assign(
            static_cast<std::size_t>(n),
            std::vector<unsigned char>(static_cast<std::size_t>(capacity) + 1, 0)
        );
    }

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

            if (reconstruct && cost <= c && take > notTake) {
                decisions[i][c] = 1;
            }
        }

        std::swap(prev, curr);
    }

    DPOutput out{};
    out.benefit = prev[capacity];
    out.resourcesUsed = 0;

    if (reconstruct) {
        int rem = capacity;
        for (int i = n - 1; i >= 0; --i) {
            if (decisions[i][rem] != 0) {
                out.selected.push_back(i);
                out.resourcesUsed += data.requirements[i].cost;
                rem -= data.requirements[i].cost;
            }
        }
        std::reverse(out.selected.begin(), out.selected.end());
    }

    return out;
}

DPOutput runParallel(const InputData& data, int threads, bool reconstruct = true) {
    const int n = data.numberOfRequirements;
    const int capacity = data.capacity;

    std::vector<long long> prev(static_cast<std::size_t>(capacity) + 1, 0);
    std::vector<long long> curr(static_cast<std::size_t>(capacity) + 1, 0);

    std::vector<std::vector<unsigned char>> decisions;
    if (reconstruct) {
        decisions.assign(
            static_cast<std::size_t>(n),
            std::vector<unsigned char>(static_cast<std::size_t>(capacity) + 1, 0)
        );
    }

    omp_set_num_threads(threads);

    #pragma omp parallel
    {
        for (int i = 0; i < n; ++i) {
            const int cost = data.requirements[i].cost;
            const long long benefit = data.requirements[i].benefit;

            #pragma omp for schedule(static)
            for (int c = 0; c <= capacity; ++c) {
                const long long notTake = prev[c];
                long long take = notTake;

                if (cost <= c) {
                    take = benefit + prev[c - cost];
                }

                curr[c] = (take > notTake) ? take : notTake;

                if (reconstruct && cost <= c && take > notTake) {
                    decisions[i][c] = 1;
                }
            }

            #pragma omp single
            {
                std::swap(prev, curr);
            }
        }
    }

    DPOutput out{};
    out.benefit = prev[capacity];
    out.resourcesUsed = 0;

    if (reconstruct) {
        int rem = capacity;
        for (int i = n - 1; i >= 0; --i) {
            if (decisions[i][rem] != 0) {
                out.selected.push_back(i);
                out.resourcesUsed += data.requirements[i].cost;
                rem -= data.requirements[i].cost;
            }
        }
        std::reverse(out.selected.begin(), out.selected.end());
    }

    return out;
}

bool verifyFile(const std::string& filename, const std::vector<int>& threadCounts) {
    try {
        const InputData data = readInputFile(filename);
        const DPOutput seqRes = runSequential(data, true);

        bool allMatched = true;
        long long lastParBenefit = seqRes.benefit;

        for (int t : threadCounts) {
            const DPOutput parRes = runParallel(data, t, true);
            lastParBenefit = parRes.benefit;

            if (parRes.benefit != seqRes.benefit) {
                allMatched = false;
                std::cerr << "Mismatch in benefit for " << filename << " with " << t
                          << " threads: Seq=" << seqRes.benefit
                          << " vs Par=" << parRes.benefit << "\n";
            }
            if (parRes.resourcesUsed != seqRes.resourcesUsed) {
                allMatched = false;
                std::cerr << "Mismatch in resources used for " << filename << " with " << t
                          << " threads: Seq=" << seqRes.resourcesUsed
                          << " vs Par=" << parRes.resourcesUsed << "\n";
            }
            if (parRes.selected != seqRes.selected) {
                allMatched = false;
                std::cerr << "Mismatch in selected requirements for " << filename << " with " << t
                          << " threads.\n";
            }
        }

        std::cout
            << "====================================================\n"
            << " Correctness Verification\n"
            << "====================================================\n"
            << "Test input             : " << filename << '\n'
            << "Sequential benefit     : " << seqRes.benefit << '\n'
            << "Parallel benefit       : " << lastParBenefit << '\n'
            << "Result                 : " << (allMatched ? "PASS" : "FAIL") << '\n'
            << "====================================================\n";

        return allMatched;
    } catch (const std::exception& ex) {
        std::cerr << "Error verifying " << filename << ": " << ex.what() << "\n";
        std::cout
            << "====================================================\n"
            << " Correctness Verification\n"
            << "====================================================\n"
            << "Test input             : " << filename << '\n'
            << "Result                 : FAIL (" << ex.what() << ")\n"
            << "====================================================\n";
        return false;
    }
}

int main(int argc, char* argv[]) {
    const std::vector<int> threadCounts = {1, 2, 4, 8};

    if (argc >= 2) {
        std::string arg = argv[1];
        if (arg != "--all") {
            bool ok = verifyFile(arg, threadCounts);
            return ok ? 0 : 1;
        }
    }

    // Default or --all: verify standard test files
    const std::vector<std::string> testFiles = {
        "data/sample_ip.txt",
        "data/zero_cap.txt",
        "data/no_itemfit.txt",
        "data/oneitem.txt",
        "data/repeated_values.txt",
        "data/ipsmall.txt",
        "data/ipmedium.txt",
        "data/iplarge.txt"
    };

    bool allPassed = true;
    for (const auto& file : testFiles) {
        if (!verifyFile(file, threadCounts)) {
            allPassed = false;
        }
    }

    if (!allPassed) {
        std::cerr << "\nVerification FAILED on one or more test cases!\n";
        return 1;
    }

    std::cout << "\nAll verification test cases PASSED successfully.\n";
    return 0;
}
