# Wholesail Integration

This project is a config-driven Python CLI for normalizing invoice CSV files from multiple sources into one canonical model and generating balance reports.

## Goals

- Support multiple CSV providers with different column names.
- Add new providers through configuration, not by changing Python code.
- Validate incomplete or invalid rows without stopping the whole run.
- Calculate two metrics from normalized invoice records:
  - Outstanding Balance
  - Past Due Balance
- Group the report by seller first, then by customer.

## Balance Rules

The reporting logic uses the following definitions:

```text
balance = trans_amount + adjustment - paid_amount
outstanding balance: balance > 0
past due balance: outstanding and (trans_date + term_schedule_days < current_date)
```

For the take-home challenge, the default `current_date` is `2022-03-31`.

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

## Canonical Model

All source rows are mapped into one shared invoice shape before any reporting happens.

Core fields in the canonical invoice record:

- `source_name`
- `invoice_id`
- `customer_name`
- `trans_amount`
- `trans_date`
- `adjustment`
- `term_schedule_days`
- `paid_amount`
- `paid_at`
- `billing_address`
- `shipping_address`
- `raw_items_json`
- `note`
- `status`

## Source Configuration

Each provider has its own TOML configuration file in `configs/sources`.

Each config defines:

- How to recognize a file
- Which source column maps to each canonical field
- Which transform to apply
- Which defaults to use for missing values
- Which note values should be treated as status markers
- Which statuses should be excluded from metrics

Example concepts:

- `customer` and `buyer` both map to `customer_name`
- `amount` maps directly to `trans_amount`
- `transAmountCents` maps to `trans_amount` with a `cents_to_decimal` transform

## How New Sources Should Be Added

1. Copy an existing provider config.
2. Update the `required_headers`.
3. Update the field mappings and transforms.
4. Add or adjust status markers if needed.
5. Add any metric exclusion statuses if needed.
6. Drop the new CSV into the input directory.

The goal is that no Python code should change for a standard new source.

## Assumptions

- One CSV row represents one complete invoice record.
- Empty `adjustment` defaults to `0`.
- Empty `paid_amount` defaults to `0`.
- Empty `paid_at` remains null.
- Records whose note matches `VOIDED` are marked with status `voided`.
- `voided` records are excluded from metric totals by configuration.
- The line item JSON is preserved as raw text because the current metrics do not depend on item-level calculations.
- The report groups balances by seller and then by customer.

## Local Setup

1. Install Python 3.11 or newer.
2. Create and activate a virtual environment.
3. Install the project in editable mode.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

## Run the CLI

Place your CSV files in `data/input`, then run:

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

## Example Output Shape

The generated report is a JSON file shaped like this:

```json
{
  "as_of_date": "2022-03-31",
  "run_summary": {
    "source_count": 2,
    "discovered_files": 2,
    "resolved_files": [
      {
        "file": "data/input/data-golden-gate-produce-10.csv",
        "source_name": "golden_gate_produce"
      }
    ],
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
        "customer_count": 3,
        "outstanding_balance": "1900.00",
        "past_due_balance": "1400.00",
        "customers": [
          {
            "customer_name": "customer-7",
            "invoice_count": 2,
            "outstanding_balance": "425.00",
            "past_due_balance": "300.00"
          }
        ]
      }
    ]
  },
  "invalid_rows": []
}
```

## Validation Strategy

The current validation rules check for:

- Missing invoice id
- Missing customer name
- Missing transaction date
- Negative transaction amount
- Negative paid amount
- Negative term schedule

Invalid rows are collected into the report instead of crashing the whole run.

## Tests

Run tests with:

```bash
python -m unittest
```

## Notes

- Monetary values are normalized to the main currency unit using `Decimal`.
- Happy Fruits amounts are converted from cents before metric calculation.
- If you want a new provider to treat a different note value as voided or excluded, update its TOML config rather than editing Python code.
