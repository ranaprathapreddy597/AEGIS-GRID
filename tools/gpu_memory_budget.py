"""Projected BF16 resident model memory; this is not a hardware measurement."""

import argparse

from aegis_inference.budget import GIB, calculate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", type=int, default=262144)
    parser.add_argument("--sequences", type=int, default=2)
    parser.add_argument("--kv-dtype", choices=["bf16", "fp8"], default="bf16")
    parser.add_argument("--capacity-gib", type=int)
    args = parser.parse_args()
    print(
        calculate(
            args.context,
            args.sequences,
            args.kv_dtype,
            args.capacity_gib * GIB if args.capacity_gib is not None else 192_000_000_000,
        ).model_dump_json(indent=2)
    )


if __name__ == "__main__":
    main()
