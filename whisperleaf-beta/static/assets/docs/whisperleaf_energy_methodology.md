# WhisperLeaf Energy Benchmark Methodology (v0.2)

This document describes the methodology for **WhisperLeaf Energy Benchmark v0.2**
for **local document summarization**. It is intended as product evidence, not as
an academic paper.

## Purpose

The goal of this benchmark is to measure the **energy use of WhisperLeaf** for
summarizing local text documents on a user's own machine in a way that is:

- transparent  
- repeatable  
- defensible for product discussions  

The benchmark focuses on *one* specific workflow: private document
summarization using a local model (e.g. via Ollama).

## Workflow Tested

Workflow under test:

> Summarize a local text document using WhisperLeaf with a fixed prompt and a
> chosen local model profile (e.g. Fast / Balanced).

Key constraints:

- Local-only (no cloud APIs)  
- Same prompt for all documents  
- Same model configuration per run within a run set  

## Dataset Description

The benchmark assumes a local folder:

`benchmark_docs/`

containing plain-text files such as:

- `doc01_ai_energy_policy.txt`  
- `doc02_digital_economy_growth.txt`  
- `doc03_climate_transition_policy.txt`  
- `doc04_public_health_systems.txt`  
- `doc05_global_supply_chain_risk.txt`  
- `doc06_urban_infrastructure_future.txt`  
- `doc07_food_security_and_agriculture.txt`  
- `doc08_water_management_policy.txt`  
- `doc09_emerging_ai_regulation.txt`  
- `doc10_clean_energy_transition.txt`  

Documents should be stable over time so that repeated runs measure changes in
hardware, models, and configuration rather than changes in content.

## Fixed Prompt

All runs use the same prompt:

> “Summarize the key points of this document in 5 bullet points and a
> 1-paragraph overview.”

The prompt version is recorded as:

`prompt_version = "v1_bullets_plus_overview"`

## Hardware Metadata Fields

Each run records basic hardware metadata:

- `device_name` — human-readable label (e.g. `M2 Air 16GB`)  
- `cpu_gpu_config` — short description of CPU / GPU configuration  
- `ram_gb` — system RAM in GB  
- `device_state` — `"plugged_in"` or `"battery"`  

These fields are not exhaustive but provide enough context to interpret
differences between runs on different machines.

## Measurement Fields

The v0.2 benchmark records the following measurements per run:

- `run_id` — unique identifier for the run  
- `date` — date of the run in ISO format (YYYY-MM-DD)  
- `model_name` — e.g. `llama3.2`  
- `quantization` — e.g. `q4_K_M`, `q6_K`  
- `document_id` — derived from the filename (e.g. `doc01_ai_energy_policy`)  
- `document_word_count` — word count of the source document  
- `prompt_version` — fixed prompt version identifier  
- `runtime_seconds` — total runtime of the summarization workflow  
- `avg_power_watts` — average power draw during the run (measured externally)  
- `total_energy_wh` — total energy consumed during the run (measured or derived)  
- `idle_power_watts` — baseline idle power (no task)  
- `idle_energy_wh` — baseline idle energy over the same duration as the task  
- `net_task_energy_wh` — task-only energy (derived, see below)  
- `output_word_count` — word count of the generated summary  
- `energy_per_1000_words` — normalized energy metric (derived, see below)  
- `quality_pass_fail` — simple quality gate (`pass` / `fail`)  
- `notes` — free-form notes (measurement method, anomalies, etc.)  

All energy and power values are obtained using external tools or hardware.
WhisperLeaf does not attempt to read from power sensors directly.

## Idle Baseline Explanation

To estimate **task-only energy**, we measure a short **idle baseline** before
each run:

1. Ensure WhisperLeaf and the system are in the same state as during the actual
   run (e.g. same model loaded, same device_state).  
2. Measure power/energy over a short fixed window while the system is idle
   (no summarization task running).  
3. Record:
   - `idle_power_watts`  
   - `idle_energy_wh`  

The summarization run records:

- `avg_power_watts` and `total_energy_wh` for the active workflow  

The difference between the active run and the idle baseline is treated as the
energy attributable to the summarization task.

## Derived Metrics Explanation

Two derived metrics are computed:

1. **Net task energy**

   ```text
   net_task_energy_wh = total_energy_wh - idle_energy_wh
   ```

   This estimates the energy attributable to the summarization task by
   subtracting the idle baseline from the total measured energy.

2. **Energy per 1000 words**

   ```text
   energy_per_1000_words = net_task_energy_wh / output_word_count * 1000
   ```

   If `output_word_count` is zero or missing, this value is set to `0.0` to
   avoid division by zero.

These metrics allow meaningful comparison between runs with different summary
lengths.

## Quality Gate

The benchmark records a simple quality indicator:

- `quality_pass_fail` — `"pass"` or `"fail"`

This is intentionally minimal. A run is marked as `pass` if the summary meets
the operator's basic expectations (e.g. on-topic, not obviously truncated).
There is no numeric rubric or automated evaluation in v0.2.

## Limitations

Key limitations of this methodology:

- Power and energy measurements depend on the external tools and hardware
  used; precision and accuracy may vary between setups.  
- The benchmark covers **only one workflow**: local document summarization.  
- Results are not intended to generalize to all AI workloads or to cloud
  deployments.  
- Quality is captured as a simple pass/fail flag, not a detailed score.  

Despite these limitations, the benchmark is designed to be transparent and
repeatable for product-level comparison across devices, models, and versions
of WhisperLeaf.

## Cloud Comparison (Future Work)

Future versions of the methodology may add **cloud comparison** using published
energy/emissions estimates from cloud providers or independent studies.

Important:

- The benchmark itself will remain **local-first**.  
- Cloud comparison will use published or independently measured data rather
  than direct cloud instrumentation from WhisperLeaf.  

For now, v0.2 is focused entirely on **local energy use** for document
summarization workflows.

