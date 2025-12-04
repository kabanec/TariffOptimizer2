# Knowledge Base Directory

This directory contains JSON files for the RAG (Retrieval-Augmented Generation) system that provides context to the AI for tariff optimization analysis.

## Files

- `de_minimis_values.json` - De minimis thresholds by country
- `executive_orders.json` - Executive orders affecting tariffs (Section 301, 232, etc.)
- `duty_rules.json` - Duty calculation rules and incoterms
- `tariff_ranges.json` - HS code chapter tariff ranges
- `recent_tariff_updates.json` - 2025 tariff updates and IEEPA reciprocal tariffs

## Usage

The knowledge base files are loaded by the application to provide relevant context for AI analysis of AvaTax transactions. You can add your own JSON files following the same structure.

## Example Structure

```json
{
  "countries": {
    "US": {
      "threshold": 800,
      "currency": "USD",
      "notes": "Section 321 de minimis"
    }
  }
}
```

Place your knowledge base files in this directory and they will be automatically cached and used during transaction analysis.
