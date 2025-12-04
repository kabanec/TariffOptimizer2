# Tariff Lookup Feature - User Guide

## Overview

The Tariff Lookup feature replicates Flexport's tariff calculator functionality, providing comprehensive duty and tariff analysis for any HS code with AI-powered insights.

## Accessing the Tool

1. **Login** to the application at https://tariff-optimizer2.onrender.com
2. From the **homepage**, click **"Launch Tariff Lookup →"**
3. Or navigate directly to: https://tariff-optimizer2.onrender.com/tariff-lookup

## How to Use

### Step 1: Enter Basic Information

**HS Code** (Required)
- Enter the full HS code (6-10 digits)
- Example: `3305.10.00.00` (perfumes) or `8517.62.00` (smartphones)

**Country of Origin** (Required)
- Select the country where goods are manufactured
- Default: China (CN)
- Common origins: CN, MX, VN, IN, JP, KR

**Destination Country** (Required)
- Select the destination country
- Default: United States (US)

**Entry Date** (Required)
- Select the expected entry date
- Defaults to today's date
- Important for time-sensitive tariffs

**Shipment Value** (Required)
- Enter the value in USD
- Used to calculate actual duty amounts
- Example: 100

### Step 2: Optional Parameters

**Mode of Transport**
- Air (default)
- Ocean
- Ground
- Rail

**AvaTax Environment**
- Sandbox (default) - for testing
- Production - for live data

### Step 3: Calculate

Click **"Calculate Tariffs"** button to:
1. Call AvaTax API with your parameters
2. Parse duty breakdown
3. Identify punitive tariffs
4. Generate AI analysis

## Understanding the Results

### 1. Tariff Summary

Displays overview metrics:
- **HS Code**: The code you entered
- **Origin → Destination**: Trade route
- **Shipment Value**: Base value
- **Total Duties & Taxes**: All applicable charges
- **Total Landed Cost**: Value + duties
- **Effective Duty Rate**: Percentage of duties vs value

### 2. Detailed Duty Breakdown

Table showing all standard duties:

| Tax Type | Rate | Amount | Description |
|----------|------|--------|-------------|
| Duty | 5.00% | $5.00 | Standard customs duty (MFN rate) |
| MPF | 0.35% | $0.35 | Merchandise Processing Fee |
| HMF | 0.13% | $0.13 | Harbor Maintenance Fee |

**Key Tax Types:**
- **Duty**: Standard customs duty (MFN rate)
- **Import VAT/GST**: Value-added tax
- **MPF**: US Merchandise Processing Fee (0.3464%)
- **HMF**: US Harbor Maintenance Fee (0.125%)

### 3. Punitive Tariffs (Chapter 98/99)

Highlighted section showing additional tariffs:

**Section 301 Tariffs** (Chinese imports)
- Rates: 7.5% to 25% depending on product list
- Reason: Unfair trade practices
- Applies to most Chinese goods

**Section 232 Tariffs** (Steel/Aluminum)
- Steel: 25%
- Aluminum: 10%
- Reason: National security
- Applies to metal content only

**Chapter 99 Tariffs**
- Additional punitive tariffs from executive orders
- Trade action measures
- Country-specific restrictions

**Anti-Dumping/Countervailing Duties**
- Product-specific measures
- Offset unfair pricing or subsidies

### 4. AI-Powered Analysis

Brief, technical analysis including:
- **Root Cause**: Why duties are calculated this way
- **Key Findings**: Important rates and regulations
- **Action Items**: What to verify or consider

Example:
```
Root Cause:
Chinese electronics subject to MFN rate + Section 301 tariff stack.

Key Findings:
- MFN rate: 0% (duty-free electronics)
- Section 301: +25% (List 4A)
- Total effective rate: 25.48% (including fees)

Action:
Verify HS classification and explore country of origin alternatives.
```

### 5. Raw API Response

Collapsible section with full JSON response from AvaTax API.
- Click **"Toggle"** to show/hide
- Click **"Copy"** to copy to clipboard
- Useful for debugging and integration

## Example Scenarios

### Scenario 1: Chinese Electronics

```
HS Code: 8517.62.00
Origin: China (CN)
Destination: United States (US)
Value: $1000

Results:
- MFN Duty: 0% (duty-free)
- Section 301: +25% ($250)
- MPF: 0.3464% ($3.46)
- HMF: 0.125% ($1.25)
- Total: $254.71 (25.47% effective)
```

### Scenario 2: French Perfume

```
HS Code: 3305.10.00.00
Origin: France (FR)
Destination: United States (US)
Value: $100

Results:
- MFN Duty: 0% (duty-free)
- MPF: 0.3464% ($0.35)
- HMF: 0.125% ($0.13)
- Total: $0.48 (0.48% effective)
```

### Scenario 3: Chinese Steel Products

```
HS Code: 7210.49.00
Origin: China (CN)
Destination: United States (US)
Value: $5000

Results:
- MFN Duty: 0%
- Section 232: +25% ($1250)
- Section 301: +25% ($1250)
- MPF: $25
- HMF: $6.25
- Total: $2531.25 (50.63% effective)
```

## Key Features Compared to Flexport

### Similar Features ✅
- HS code lookup
- Country of origin/destination selection
- Entry date selection
- Value-based calculations
- Mode of transport options
- Detailed rate breakdowns
- Punitive tariff identification

### Additional Features ⭐
- **AI-Powered Analysis**: Automated insights and recommendations
- **Explanation Text**: Human-readable descriptions for each duty
- **Avalara Branding**: Professional Avalara styling
- **Real-time AvaTax**: Direct API integration
- **Raw Response View**: Full API response for debugging

### Different Approach
- **Flexport**: Uses static tariff database with regular updates
- **Tariff Optimizer**: Uses live AvaTax API for real-time calculations

## Troubleshooting

### Error: "AvaTax bearer token not configured"

**Solution**: Set `AVATAX_BEARER_TOKEN` environment variable in Render dashboard.

### Error: "Invalid HS code"

**Causes:**
- HS code too short (minimum 6 digits)
- HS code contains non-numeric characters
- HS code doesn't exist in AvaTax database

**Solution**: Verify HS code format and try a valid code like `8517.62.00`

### No Punitive Tariffs Shown

**This is normal** if:
- Product isn't subject to Section 301/232
- Origin country isn't China
- Product doesn't have anti-dumping duties

### Sandbox vs Production

**Sandbox**:
- Test environment
- May have limited HS codes
- Safe for testing

**Production**:
- Live data
- Full HS code coverage
- Requires production AvaTax credentials

## API Integration

For programmatic access, use the REST API:

```bash
curl -X POST https://tariff-optimizer2.onrender.com/api/tariff-lookup \
  -H "Content-Type: application/json" \
  -d '{
    "hsCode": "3305.10.00.00",
    "originCountry": "CN",
    "destinationCountry": "US",
    "entryDate": "2025-12-04",
    "shipmentValue": 100,
    "modeOfTransport": "AIR",
    "environment": "sandbox"
  }'
```

Response:
```json
{
  "success": true,
  "apiResponse": { ... },
  "dutyBreakdown": [ ... ],
  "punitiveTariffs": [ ... ],
  "aiAnalysis": "..."
}
```

## Best Practices

1. **Always verify HS codes** with a customs broker
2. **Use the correct origin country** (manufacturing, not shipping)
3. **Check entry dates** for time-sensitive tariffs
4. **Review AI analysis** for optimization suggestions
5. **Compare sandbox vs production** for accuracy
6. **Save raw responses** for audit trails

## Limitations

- Requires valid AvaTax credentials
- HS code must exist in AvaTax database
- Some countries may have limited support
- Tariff rates change - verify with official sources
- AI analysis is advisory only

## Support

- **Documentation**: See DEPLOYMENT.md and API_INTEGRATION_GUIDE.md
- **Issues**: Report at https://github.com/kabanec/TariffOptimizer2/issues
- **Live Tool**: https://tariff-optimizer2.onrender.com/tariff-lookup

## Future Enhancements

- [ ] Bulk HS code lookup
- [ ] Historical rate comparison
- [ ] Export results to PDF/Excel
- [ ] Save favorite calculations
- [ ] Rate change alerts
- [ ] Multi-currency support
- [ ] Duty drawback calculator
