"""
WhisperLeaf Energy Benchmark v0.1 — Document Summarization

This script provides a small, modular scaffold for logging energy-related
benchmark runs for local document summarization workflows.

It does NOT measure power or energy itself. Instead, it assumes you run
WhisperLeaf locally (and, if desired, external power tools) and then log
the results here in a consistent CSV format.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List


BENCHMARK_DIR = Path(__file__).resolve().parent
CSV_PATH = BENCHMARK_DIR / "whisperleaf_energy_summary_v0_1.csv"


@dataclass
class SummaryBenchmarkResult:
    run_id: str
    device_name: str
    model_name: str
    quantization: str
    document_id: str
    runtime_seconds: float
    avg_power_watts: float
    total_energy_wh: float
    idle_power_watts: float
    idle_energy_wh: float
    net_task_energy_wh: float
    output_word_count: int
    energy_per_1000_words: float
    device_state: str
    quality_accuracy: float
    quality_completeness: float
    quality_readability: float
    pass_fail: str
    notes: str


CSV_FIELDS: List[str] = [
    "run_id",
    "device_name",
    "model_name",
    "quantization",
    "document_id",
    "runtime_seconds",
    "avg_power_watts",
    "total_energy_wh",
    "idle_power_watts",
    "idle_energy_wh",
    "net_task_energy_wh",
    "output_word_count",
    "energy_per_1000_words",
    "device_state",
    "quality_accuracy",
    "quality_completeness",
    "quality_readability",
    "pass_fail",
    "notes",
]


def ensure_csv_header() -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    if CSV_PATH.exists() and CSV_PATH.stat().st_size > 0:
        return
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()


def append_result(result: SummaryBenchmarkResult) -> None:
    ensure_csv_header()
    row = asdict(result)
    with CSV_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writerow(row)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="WhisperLeaf Energy Benchmark v0.1 — Document Summarization",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    log = sub.add_parser(
        "log-run",
        help="Log a single document summarization benchmark run (values measured externally).",
    )
    log.add_argument("--run-id", required=True)
    log.add_argument("--device-name", required=True)
    log.add_argument("--model-name", required=True)
    log.add_argument("--quantization", required=True, help="e.g. q4_K_M, q6_K, full-precision")
    log.add_argument("--document-id", required=True, help="Stable identifier for the test document")
    log.add_argument("--runtime-seconds", type=float, required=True)
    log.add_argument("--avg-power-watts", type=float, required=True)
    log.add_argument("--total-energy-wh", type=float, required=True)
    log.add_argument(
        "--idle-power-watts",
        type=float,
        required=True,
        help="Baseline idle power draw measured over the same duration",
    )
    log.add_argument(
        "--idle-energy-wh",
        type=float,
        required=True,
        help="Baseline idle energy over the same duration as the task",
    )
    log.add_argument("--output-word-count", type=int, required=True)
    log.add_argument(
        "--device-state",
        required=True,
        choices=["plugged_in", "battery"],
        help="Power state during the run.",
    )
    log.add_argument("--quality-accuracy", type=float, required=True, help="e.g. 1–5 or 0.0–1.0 scale")
    log.add_argument("--quality-completeness", type=float, required=True, help="e.g. 1–5 or 0.0–1.0 scale")
    log.add_argument("--quality-readability", type=float, required=True, help="e.g. 1–5 or 0.0–1.0 scale")
    log.add_argument(
        "--pass-fail",
        required=True,
        choices=["pass", "fail"],
        help="Overall assessment of this run.",
    )
    log.add_argument(
        "--notes",
        default="",
        help="Optional free-form notes (e.g. measurement method, anomalies).",
    )

    return parser.parse_args()


def cmd_log_run(ns: argparse.Namespace) -> None:
    # Derived metrics
    net_task_energy_wh = ns.total_energy_wh - ns.idle_energy_wh
    if ns.output_word_count > 0:
        energy_per_1000_words = ns.total_energy_wh * (1000.0 / float(ns.output_word_count))
    else:
        energy_per_1000_words = 0.0

    result = SummaryBenchmarkResult(
        run_id=ns.run_id,
        device_name=ns.device_name,
        model_name=ns.model_name,
        quantization=ns.quantization,
        document_id=ns.document_id,
        runtime_seconds=ns.runtime_seconds,
        avg_power_watts=ns.avg_power_watts,
        total_energy_wh=ns.total_energy_wh,
        idle_power_watts=ns.idle_power_watts,
        idle_energy_wh=ns.idle_energy_wh,
        net_task_energy_wh=net_task_energy_wh,
        output_word_count=ns.output_word_count,
        energy_per_1000_words=energy_per_1000_words,
        device_state=ns.device_state,
        quality_accuracy=ns.quality_accuracy,
        quality_completeness=ns.quality_completeness,
        quality_readability=ns.quality_readability,
        pass_fail=ns.pass_fail,
        notes=ns.notes,
    )
    append_result(result)
    print(f"Logged run {result.run_id} to {CSV_PATH}")


def main() -> None:
    ns = parse_args()
    if ns.command == "log-run":
        cmd_log_run(ns)
    else:
        raise SystemExit(f"Unknown command: {ns.command}")


if __name__ == "__main__":
    main()

