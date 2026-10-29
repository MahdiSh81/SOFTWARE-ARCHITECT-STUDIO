# Capacity and cloud cost modeling

Compute with explicit units, assumptions, and ranges. Model realistic workloads rather than invented cloud list prices. `tools/architect_cli.py capacity --input capacity.json` accepts the schema below.

## Input example (illustrative, not a quote)

```json
{
  "daily_requests": 1800000,
  "peak_factor": 6,
  "average_payload_kib": 8,
  "records_per_day": 80000,
  "average_record_bytes": 1800,
  "retention_days": 365,
  "storage_overhead_multiplier": 2.5,
  "replica_count": 2,
  "monthly_compute_hours": 730,
  "assumed_compute_price_per_hour": null,
  "assumed_storage_price_per_gb_month": null,
  "assumed_egress_price_per_gb": null,
  "currency": "USD"
}
```

- `average_qps = daily_requests / 86400`
- `peak_qps = average_qps * peak_factor`, where peak_factor is the ratio of busiest *second* to daily average; users using busiest-hour traffic should instead recalculate by the hour.
- `monthly_network_bytes = daily_requests * average_payload_kib * 1024 * 30`. Payload is KiB; the legacy `average_payload_kb` input remains a KiB alias. This is a *one-way* rough traffic volume and may not equal billable egress.
- `monthly_network_gib = monthly_network_bytes / 1024^3`; `monthly_network_gb = monthly_network_bytes / 10^9`. Egress prices in this calculator use decimal GB.
- `retained_gb = records_per_day * retention_days * average_record_bytes / 10^9`
- `physical_storage_gb = retained_gb * storage_overhead_multiplier * replica_count`. Confirm whether a provider's stated replica/billing semantics already include storage multipliers before using this figure in real bills.
- Monthly indicative cost = `monthly_compute_hours * assumed_compute_price_per_hour + physical_storage_gb * assumed_storage_price_per_gb_month + monthly_network_gb * assumed_egress_price_per_gb`, **only** if all inputs specified; else result `null` and explain missing prices.

Inputs, weights and derived results must be finite. Reject booleans, NaN, infinity, numeric overflow and invalid ranges. Use unrounded intermediate values and round only displayed outputs. A zero-volume workload is valid; unknown prices remain unknown.

Provide scenario analysis, including 1x baseline/3x growth and a 0.5–2x sensitivity range for payload and replication if material. Report omitted costs: databases, API gateways, NAT, load balancers, logs/metrics, backups, regional transfer, support, taxes, reserved commitment discounts and engineering labor unless explicitly modeled.

Before claiming AWS/GCP/Azure costs, look up exact service/SKU, region, on-demand/reserved price, date, tenancy and usage, cite vendor calculator or pricing docs. Do not invent quotes; distinguish scenario math from invoices or production measurements.
