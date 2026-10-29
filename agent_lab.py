#!/usr/bin/env python3
"""Command-line entry point for the Agent Lab experiment registry."""

from __future__ import annotations

import argparse
from dataclasses import dataclass


@dataclass(frozen=True)
class Experiment:
    """A runnable or planned agent experiment."""

    name: str
    description: str


EXPERIMENTS = (
    Experiment(
        name="hello-agent",
        description="A placeholder experiment for validating the lab setup.",
    ),
)


def list_experiments() -> str:
    """Return the registry in a human-readable format."""

    return "\n".join(f"{experiment.name}: {experiment.description}" for experiment in EXPERIMENTS)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage Agent Lab experiments.")
    parser.add_argument("command", choices=("list",), help="operation to perform")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "list":
        print(list_experiments())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
