# Wholesail Integration

A config-driven Python CLI that normalizes invoice CSV files from multiple sellers into one canonical model and generates customer-level balance reports.

## Table of Contents

- [Overview](#overview)
- [Design Goals](#design-goals)
- [Balance Definitions](#balance-definitions)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Usage](#usage)
- [Output](#output)
- [Design Notes](#design-notes)
- [Scalability and Performance](#scalability-and-performance)
- [Error Handling](#error-handling)
- [Extending to New CSV Sources](#extending-to-new-csv-sources)
- [Tests](#tests)
- [Future Improvements](#future-improvements)

## Overview

Different sellers can send CSV files with different field names and formats, even when the business meaning is the same. This project solves that by mapping source-specific CSV rows into one canonical invoice model before any reporting logic is applied.

The current implementation generates a grouped balances report:

- Group first by seller
- Group then by customer
- Calculate `outstanding_balance` and `past_due_balance` for each customer

## Design Goals

- Support multiple CSV schemas without changing core reporting logic
- Add new sellers through configuration whenever possible
- Keep business logic independent from raw source column names
- Continue processing when individual rows are invalid
- Produce output that is easy to review and easy to test

## Balance Definitions

The reporting logic uses the following rules:

```text
balance = trans_amount + adjustment - paid_amount
outstanding balance: balance > 0
past due balance: outstanding and (trans_date + term_schedule_days < current_date)
```

For this take-home challenge, the default `current_date` is `2022-03-31`.

## How It Works

The pipeline is:

```text
CSV file
-> source resolution
-> field mapping
-> type conversion
-> validation
-> canonical invoice record
-> grouped balance aggregation
-> JSON report
```

The important design choice is that reports do not depend on raw CSV headers such as `customer`, `buyer`, `amount`, or `transAmountCents`. They only depend on the canonical model.

## Project Structure

```text
.
|-- configs/
|   `-- sources/
|       |-- golden_gate_produce.toml
|       `-- happy_fruits.toml
|-- data/
|   |-- input/
|   `-- output/
|-- src/
|   `-- wholesail/
|       |-- cli.py
|       |-- config/
|       |   `-- loader.py
|       |-- domain/
|       |   |-- metrics.py
|       |   `-- models.py
|       |-- ingestion/
|       |   |-- converters.py
|       |   |-- csv_reader.py
|       |   |-- row_mapper.py
|       |   |-- source_resolver.py
|       |   `-- validators.py
|       `-- reporting/
|           |-- summary_report.py
|           `-- writers.py
`-- tests/
    |-- test_mapping.py
    |-- test_metrics.py
    `-- test_resolver.py
```

## Setup

Install Python 3.11 or newer, then run:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

## Usage

Place CSV files in `data/input`, then run:

```bash
wholesail --input-dir ./data/input --config-dir ./configs/sources --output ./data/output/report.json
```

You can also run it as a module:

```bash
python -m wholesail.cli --input-dir ./data/input --config-dir ./configs/sources --output ./data/output/report.json
```

Optional arguments:

- `--as-of-date 2022-03-31`
- `--format json`

## Output

The generated report contains two main sections:

- `run_summary`: input discovery, resolved files, and invalid row counts
- `balances_report`: grouped balances by seller and then by customer

Example shape:

```json
{
  "as_of_date": "2022-03-31",
  "run_summary": {
    "source_count": 2,
    "discovered_files": 2,
    "resolved_files": [],
    "unresolved_files": [],
    "valid_record_count": 20,
    "records_in_metrics": 17,
    "invalid_row_count": 0
  },
  "balances_report": {
    "total_outstanding_balance": "3461.18",
    "total_past_due_balance": "2411.18",
    "balances_by_seller": [
      {
        "seller_name": "golden_gate_produce",
        "customers": [
          {
            "customer_name": "customer-7",
            "invoice_count": 2,
            "outstanding_balance": "425.00",
            "past_due_balance": "50.00"
          }
        ]
      }
    ]
  },
  "invalid_rows": []
}
```

## Design Notes

### Canonical Model

All source rows are mapped into one shared invoice shape before reporting. Core fields include:

- `source_name`
- `invoice_id`
- `customer_name`
- `trans_amount`
- `trans_date`
- `adjustment`
- `term_schedule_days`
- `paid_amount`
- `paid_at`
- `note`
- `status`

This keeps the business logic stable even when source CSV column names differ.

### Config-Driven Source Mapping

Each seller has a TOML file in `configs/sources` that defines:

- how to recognize the file
- how each source field maps to a canonical field
- what type conversion should be applied
- what defaults should be used for missing values
- which note values should be treated as statuses
- which statuses should be excluded from metric calculations

Example:

- `customer` and `buyer` both map to `customer_name`
- `amount` maps to `trans_amount`
- `transAmountCents` maps to `trans_amount` with `cents_to_decimal`

## Scalability and Performance

The current implementation is a good fit for small to medium CSV workloads and for take-home style evaluation.

Current strengths:

- simple processing flow
- low dependency footprint
- configuration-based extensibility
- testable business logic

Current limits:

- rows are currently read and processed in Python rather than by a vectorized engine
- very large files would benefit from streaming instead of holding more data in memory than necessary
- many large files would eventually benefit from file-level parallelism

If the system needed to handle much larger datasets, the first improvement would be to switch to streaming row-by-row processing and incremental aggregation.

## Error Handling

The current version is designed to continue processing when individual rows are invalid.

Current behavior:

- invalid rows are excluded from metrics
- invalid rows are captured in the `invalid_rows` section of the output
- missing or malformed data is handled through validation rules and config defaults where appropriate

Examples of row-level validation:

- missing invoice id
- missing customer name
- missing transaction date
- negative transaction amount
- negative paid amount
- negative term schedule

A future production-oriented version would also add clearer file-level error handling for cases such as unreadable files, bad encodings, or malformed CSV structure.

## Extending to New CSV Sources

In the common case, adding a new CSV source should not require Python code changes.

Expected steps:

1. Copy an existing TOML source config.
2. Update filename patterns and required headers.
3. Update field mappings.
4. Set transforms and defaults.
5. Add any status markers or metric exclusions.

If a future CSV only adds extra unused columns, no code change should be needed. Code changes would only be required if a new source introduces:

- a new business concept not present in the canonical model
- a new transformation rule that does not already exist
- a new report requirement that depends on previously unused data

## Tests

Run tests with:

```bash
python -m unittest
```

The test suite currently covers:

- balance calculation rules
- source resolution
- config-driven row mapping
- grouped seller and customer aggregation

## Future Improvements

The next logical improvements would be:

- streaming row processing for large files
- separate invalid-row and file-error output artifacts
- stronger config validation at startup
- additional report formats such as CSV
- more detailed logging and operational summaries
