# WhisperLeaf Energy Benchmark v0.1 — Document Summarization

This folder contains a small, local-only benchmark scaffold for measuring
energy use during **document summarization** workflows with WhisperLeaf.

The goal is not to automate power measurement, but to give you a repeatable
structure for recording runs and comparing them over time or across devices
and models.

## Benchmark Workflow (v0.1)

Target workflow:

> **Local document summarization** using WhisperLeaf and a local model
> (e.g. via Ollama), with no cloud calls.

You are free to choose the exact summarization procedure (prompt, length,
temperature, etc.), but it should be kept consistent within a benchmark
campaign so results are comparable.

Typical steps per run:

1. Ensure WhisperLeaf and the local model (e.g. `llama3.2`) are running.
2. Choose a test document and assign a stable `document_id`.
3. Run the summarization workflow locally (possibly multiple times).
4. Measure:
   - `runtime_seconds` for the workflow
   - `avg_power_watts` and `total_energy_wh` using external tools or hardware
   - qualitative scores for accuracy, completeness, readability
5. Log the run using the benchmark script.

## Data Schema

All runs are appended to:

`benchmarks/whisperleaf_energy_summary_v0_1.csv`

Columns:

- `run_id` — unique identifier for this benchmark run  
- `device_name` — e.g. `M2 Air 16GB`, `Ryzen 7 5800X`  
- `model_name` — e.g. `llama3.2`, `mistral:latest`  
- `quantization` — e.g. `q4_K_M`, `q6_K`, `full-precision`  
- `document_id` — stable identifier for the test document  
- `runtime_seconds` — total runtime of the summarization workflow  
- `avg_power_watts` — average power draw during the run (measured externally)  
- `total_energy_wh` — total energy consumed during the run (measured or derived)  
- `idle_power_watts` — baseline idle power draw (same duration, no task)  
- `idle_energy_wh` — baseline idle energy over the same duration as the task  
- `net_task_energy_wh` — task-only energy: `total_energy_wh - idle_energy_wh`  
- `output_word_count` — word count of the generated summary  
- `energy_per_1000_words` — `total_energy_wh` normalized by summary length  
- `device_state` — `"plugged_in"` or `"battery"` during the run  
- `quality_accuracy` — subjective or rubric-based accuracy score  
- `quality_completeness` — subjective or rubric-based completeness score  
- `quality_readability` — subjective or rubric-based readability score  
- `pass_fail` — `"pass"` or `"fail"` based on your benchmark criteria  
- `notes` — free-form notes (e.g. measurement method, anomalies)  

## Logging a Run

Use the helper script:

```bash
python benchmarks/energy_summary_benchmark.py log-run \
  --run-id run_001 \
  --device-name "M2 Air 16GB" \
  --model-name "llama3.2" \
  --quantization "q4_K_M" \
  --document-id "doc_001_blogpost" \
  --runtime-seconds 12.4 \
  --avg-power-watts 18.2 \
  --total-energy-wh 0.0627 \
  --idle-power-watts 8.0 \
  --idle-energy-wh 0.0280 \
  --output-word-count 215 \
  --device-state plugged_in \
  --quality-accuracy 4.5 \
  --quality-completeness 4.0 \
  --quality-readability 4.7 \
  --pass-fail pass \
  --notes "fan stayed quiet; first-run warm model"
```

This will append a single row to the CSV. You can then analyze results in
Python, a spreadsheet, or any other tool.

## Extensibility

The script is intentionally simple and modular:

- New workflows (e.g. Q&A, multi-document comparison) can be added later as
  separate scripts or by extending the schema.
- Additional fields can be added in new benchmark versions (e.g. v0.2,
  v0.3) without affecting the v0.1 CSV.

For now, **v0.1 is focused only on local document summarization** and does
not implement any cloud comparisons or remote measurements.

