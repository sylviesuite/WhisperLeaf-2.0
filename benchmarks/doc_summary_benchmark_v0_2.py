"""
WhisperLeaf Energy Benchmark v0.2 — Document Summarization

This script defines a practical, local-only benchmark runner for measuring
energy use during document summarization workflows. It is designed for
product evidence, not academic publication.

It does NOT measure power itself. Instead, it assumes you:

- run WhisperLeaf locally with a chosen model profile (e.g. Fast / Balanced)
- use external tools or hardware to measure power and energy
- enter the measurements here, in a structured, repeatable way
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_DIR = Path(__file__).resolve().parent
DOCS_DIR = PROJECT_ROOT / "benchmark_docs"
CSV_PATH = BENCHMARK_DIR / "whisperleaf_energy_summary_v0_2.csv"

# Fixed benchmark prompt
BENCHMARK_PROMPT = (
    "Summarize the key points of this document in 5 bullet points "
    "and a 1-paragraph overview."
)
PROMPT_VERSION = "v1_bullets_plus_overview"

# Example model profiles – adjust to match your local model setup.
MODEL_PROFILES: Dict[str, Dict[str, str]] = {
    "fast": {
        "model_name": "llama3.2",
        "quantization": "q4_K_M",
    },
    "balanced": {
        "model_name": "llama3.2",
        "quantization": "q6_K",
    },
}


@dataclass
class DocSummaryBenchmarkV02:
    run_id: str
    date: str
    device_name: str
    cpu_gpu_config: str
    ram_gb: float
    device_state: str
    model_name: str
    quantization: str
    document_id: str
    document_word_count: int
    prompt_version: str
    runtime_seconds: float
    avg_power_watts: float
    total_energy_wh: float
    idle_power_watts: float
    idle_energy_wh: float
    net_task_energy_wh: float
    output_word_count: int
    energy_per_1000_words: float
    quality_pass_fail: str
    notes: str


CSV_FIELDS: List[str] = [
    "run_id",
    "date",
    "device_name",
    "cpu_gpu_config",
    "ram_gb",
    "device_state",
    "model_name",
    "quantization",
    "document_id",
    "document_word_count",
    "prompt_version",
    "runtime_seconds",
    "avg_power_watts",
    "total_energy_wh",
    "idle_power_watts",
    "idle_energy_wh",
    "net_task_energy_wh",
    "output_word_count",
    "energy_per_1000_words",
    "quality_pass_fail",
    "notes",
]


def ensure_csv_header() -> None:
    BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)
    if CSV_PATH.exists() and CSV_PATH.stat().st_size > 0:
        return
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()


def append_result(result: DocSummaryBenchmarkV02) -> None:
    ensure_csv_header()
    row = asdict(result)
    with CSV_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writerow(row)


def iter_documents(selected: Optional[List[str]] = None) -> Iterable[Path]:
    """
    Yield .txt documents from benchmark_docs/.

    If selected is provided, it should contain specific filenames to include.
    """
    if not DOCS_DIR.exists():
        raise SystemExit(f"benchmark_docs/ folder not found at {DOCS_DIR}")

    docs = sorted(p for p in DOCS_DIR.glob("*.txt") if p.is_file())
    if selected:
        wanted = set(selected)
        docs = [p for p in docs if p.name in wanted]
    if not docs:
        raise SystemExit("No matching .txt documents found in benchmark_docs/.")
    return docs


def count_words(text: str) -> int:
    return len(text.split())


def load_document(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def generate_run_id(model_profile: str, document_id: str, rep_index: int) -> str:
    ts = _dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    return f"{model_profile}_{document_id}_rep{rep_index+1}_{ts}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="WhisperLeaf Energy Benchmark v0.2 — Document Summarization",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser(
        "run",
        help="Run the document summarization benchmark over benchmark_docs/ and log results.",
    )
    run.add_argument(
        "--model-profile",
        required=True,
        choices=sorted(MODEL_PROFILES.keys()),
        help="Model profile to use (maps to model_name + quantization).",
    )
    run.add_argument(
        "--repetitions",
        type=int,
        default=1,
        help="Number of runs per document (for averaging).",
    )
    run.add_argument(
        "--docs",
        nargs="*",
        help="Optional specific document filenames from benchmark_docs/ (default: all .txt files).",
    )
    run.add_argument(
        "--device-name",
        required=True,
        help="e.g. 'M2 Air 16GB', 'Ryzen 7 5800X + RTX 4070'.",
    )
    run.add_argument(
        "--cpu-gpu-config",
        required=True,
        help="Short description of CPU/GPU configuration.",
    )
    run.add_argument(
        "--ram-gb",
        type=float,
        required=True,
        help="Total system RAM in GB (e.g. 16, 32).",
    )
    run.add_argument(
        "--device-state",
        required=True,
        choices=["plugged_in", "battery"],
        help="Power state during the runs.",
    )
    run.add_argument(
        "--notes",
        default="",
        help="Optional notes to copy onto each run row (you can extend per-run interactively).",
    )

    return parser.parse_args()


def prompt_for_float(prompt: str) -> float:
    while True:
        raw = input(prompt).strip()
        try:
            return float(raw)
        except ValueError:
            print("Please enter a numeric value.")


def prompt_for_int(prompt: str) -> int:
    while True:
        raw = input(prompt).strip()
        try:
            return int(raw)
        except ValueError:
            print("Please enter an integer value.")


def prompt_for_pass_fail(prompt: str) -> str:
    while True:
        raw = input(prompt).strip().lower()
        if raw in {"pass", "fail"}:
            return raw
        print("Please enter 'pass' or 'fail'.")


def cmd_run(ns: argparse.Namespace) -> None:
    profile = MODEL_PROFILES[ns.model_profile]
    model_name = profile["model_name"]
    quantization = profile["quantization"]

    docs = list(iter_documents(ns.docs))
    today = _dt.date.today().isoformat()

    print("WhisperLeaf Energy Benchmark v0.2 — Document Summarization")
    print(f"Dataset folder: {DOCS_DIR}")
    print(f"Model profile: {ns.model_profile} (model={model_name}, quant={quantization})")
    print(f"Prompt version: {PROMPT_VERSION}")
    print()
    print("Fixed prompt:")
    print(f'  "{BENCHMARK_PROMPT}"')
    print()
    print("For each run, you will:")
    print("- Ensure WhisperLeaf is running locally with the selected model profile.")
    print("- Apply the fixed prompt to the current document.")
    print("- Measure runtime and power/energy (including an idle baseline).")
    print("- Enter the measurements when prompted.")
    print()

    for doc_path in docs:
        doc_id = doc_path.stem
        text = load_document(doc_path)
        doc_word_count = count_words(text)
        print("=" * 80)
        print(f"Document: {doc_path.name}  (id={doc_id}, words={doc_word_count})")
        print("=" * 80)

        for rep in range(ns.repetitions):
            print()
            print(f"Run {rep + 1} / {ns.repetitions} for document {doc_id}")
            print("------------------------------------------------------------")
            print("1) Measure idle baseline for a short fixed period (no task).")
            idle_power_watts = prompt_for_float("   Enter idle_power_watts: ")
            idle_energy_wh = prompt_for_float("   Enter idle_energy_wh: ")
            print()
            print("2) Run the summarization in WhisperLeaf with the fixed prompt.")
            runtime_seconds = prompt_for_float("   Enter runtime_seconds: ")
            avg_power_watts = prompt_for_float("   Enter avg_power_watts: ")
            total_energy_wh = prompt_for_float("   Enter total_energy_wh: ")
            output_word_count = prompt_for_int("   Enter output_word_count (summary words): ")
            quality_pass_fail = prompt_for_pass_fail("   Quality pass/fail for this run (pass/fail): ")
            extra_notes = input("   Optional extra notes for this run (press Enter to skip): ").strip()

            net_task_energy_wh = total_energy_wh - idle_energy_wh
            if output_word_count > 0:
                energy_per_1000_words = net_task_energy_wh * (1000.0 / float(output_word_count))
            else:
                energy_per_1000_words = 0.0

            run_id = generate_run_id(ns.model_profile, doc_id, rep)
            combined_notes = ns.notes
            if extra_notes:
                combined_notes = (combined_notes + " | " + extra_notes).strip(" |")

            result = DocSummaryBenchmarkV02(
                run_id=run_id,
                date=today,
                device_name=ns.device_name,
                cpu_gpu_config=ns.cpu_gpu_config,
                ram_gb=ns.ram_gb,
                device_state=ns.device_state,
                model_name=model_name,
                quantization=quantization,
                document_id=doc_id,
                document_word_count=doc_word_count,
                prompt_version=PROMPT_VERSION,
                runtime_seconds=runtime_seconds,
                avg_power_watts=avg_power_watts,
                total_energy_wh=total_energy_wh,
                idle_power_watts=idle_power_watts,
                idle_energy_wh=idle_energy_wh,
                net_task_energy_wh=net_task_energy_wh,
                output_word_count=output_word_count,
                energy_per_1000_words=energy_per_1000_words,
                quality_pass_fail=quality_pass_fail,
                notes=combined_notes,
            )
            append_result(result)
            print(f"Logged run {run_id} to {CSV_PATH}")

    print()
    print("Benchmark complete.")
    print(f"All runs appended to: {CSV_PATH}")


def main() -> None:
    ns = parse_args()
    if ns.command == "run":
        cmd_run(ns)
    else:
        raise SystemExit(f"Unknown command: {ns.command}")


if __name__ == "__main__":
    # Example usage:
    # python benchmarks/doc_summary_benchmark_v0_2.py run \
    #   --model-profile fast \
    #   --repetitions 3 \
    #   --device-name "M2 Air 16GB" \
    #   --cpu-gpu-config "Apple M2 (8-core)" \
    #   --ram-gb 16 \
    #   --device-state plugged_in \
    #   --notes "fan quiet; desk ambient 22C"
    main()

