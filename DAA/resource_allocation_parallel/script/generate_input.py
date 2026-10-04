#!/usr/bin/env python3
"""
Input Generator for 0/1 Knapsack Resource Allocation

Generates benchmark and test datasets with deterministic pseudo-random values.
"""

import argparse
import os
import random
import sys


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Generate input datasets for 0/1 Knapsack Resource Allocation."
    )
    parser.add_argument(
        "--requirements",
        type=int,
        required=True,
        help="Number of requirements / items (N > 0)",
    )
    parser.add_argument(
        "--resources",
        type=int,
        required=True,
        help="Available resource capacity (C >= 0)",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output file path (e.g. data/medium_input.txt)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--max-cost",
        type=int,
        default=100,
        help="Maximum resource cost per requirement (default: 100)",
    )
    parser.add_argument(
        "--max-benefit",
        type=int,
        default=500,
        help="Maximum benefit per requirement (default: 500)",
    )
    return parser.parse_args()


def generate_input(requirements: int, resources: int, output_path: str,
                   seed: int, max_cost: int, max_benefit: int):
    if requirements <= 0:
        raise ValueError("Number of requirements must be strictly positive.")
    if resources < 0:
        raise ValueError("Resource capacity must be non-negative.")
    if max_cost <= 0:
        raise ValueError("max-cost must be strictly positive.")
    if max_benefit < 0:
        raise ValueError("max-benefit must be non-negative.")

    random.seed(seed)

    parent_dir = os.path.dirname(os.path.abspath(output_path))
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"{requirements} {resources}\n")
        for _ in range(requirements):
            cost = random.randint(1, max_cost)
            benefit = random.randint(1, max_benefit)
            f.write(f"{cost} {benefit}\n")

    file_size_kb = os.path.getsize(output_path) / 1024.0
    print(f"Generated {requirements} requirements with capacity {resources} (seed={seed}).")
    print(f"Output saved to: {output_path} ({file_size_kb:.1f} KB)")


def main():
    args = parse_arguments()
    try:
        generate_input(
            requirements=args.requirements,
            resources=args.resources,
            output_path=args.output,
            seed=args.seed,
            max_cost=args.max_cost,
            max_benefit=args.max_benefit,
        )
    except Exception as e:
        print(f"Error generating input: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
