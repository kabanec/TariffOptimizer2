# CBP Tariff Stacking Logic - Comprehensive Research & Decision Tree

## Overview
This document formalizes the complete decision tree for Chapter 98/99 tariff stacking based on CBP regulations.

**Last Updated:** December 2025
**Source:** CBP IEEPA FAQ - https://www.cbp.gov/trade/programs-administration/trade-remedies/IEEPA-FAQ

---

## 1. STACKING ORDER (CBP Guidance)

Per CBP, tariffs stack in this order:
1. **Section 232** (Steel/Aluminum/Automotive) - FIRST
2. **Section 301** (China tariffs) - SECOND
3. **IEEPA Country-Specific** (Canada/Mexico/China/Brazil/India) - THIRD
4. **IEEPA Reciprocal** (9903.01.25) - FOURTH
5. **IEEPA Fentanyl** (9903.01.36) - FIFTH (last)

**CRITICAL UPDATE:** As of 2025, IEEPA tariffs have expanded significantly:
- Canada: 25% (effective March 4, 2025) - 9903.01.01-9903.01.15
- Mexico: 25% (effective March 4, 2025) - 9903.01.01-9903.01.05
- China: 25% (effective February 4, 2025) - 9903.01.20, 9903.01.24
- Brazil: Specific rates (effective August 6, 2025)
- India: Specific rates (effective August 27, 2025)
- Reciprocal: 10% baseline (effective April 5, 2025) - 9903.01.25
  - China reciprocal escalated to 84% after April 9, 2025 (9903.01.63)
  - China reciprocal was 125% during May 10-13, 2025

---

## 2. SECTION 232 TARIFFS

### 2.1 Section 232 Steel (HS Codes: 9903.81.xx)

**Tariff Codes:**
- 9903.81.04, 9903.81.06, 9903.81.11, 9903.81.12, 9903.81.19, 9903.81.86, 9903.81.87
- Rate: 25%

**Decision Tree:**

```
IF product contains steel:

    IF origin == CA OR origin == MX:
        ASK: "Does product qualify for USMCA?"
        IF yes → EXEMPT (9903.01.26 for CA, 9903.01.27 for MX)
        IF no → APPLY Section 232 Steel

    ELSE IF origin == OTHER:
        ASK: "Percentage of steel in product?" → steel_pct
        ASK: "Country of origin for steel?" → steel_origin

        IF steel_origin == US:
            IF steel melted AND poured in US:
                → EXEMPT (9903.81.92)
            ELSE:
                → APPLY Section 232 Steel on (steel_pct% of value)
        ELSE:
            → APPLY Section 232 Steel on (steel_pct% of value)

ELSE:
    → NOT APPLICABLE (0% steel)
```

**Required Data:**
- `steel_percentage`: 0-100%
- `steel_origin_country`: ISO 2-letter code
- `usmca_qualified`: boolean (only for CA/MX origin)
- `steel_melted_and_poured_us`: boolean (only if steel_origin == US)

---

### 2.2 Section 232 Aluminum (HS Codes: 9903.85.xx)

**Tariff Codes:**
- 9903.85.02, 9903.85.04, 9903.85.07, 9903.85.08, 9903.85.09
- Rate: 10%

**Decision Tree:**

```
IF product contains aluminum:

    IF origin == CA OR origin == MX:
        ASK: "Does product qualify for USMCA?"
        IF yes → EXEMPT (9903.01.26 for CA, 9903.01.27 for MX)
        IF no → APPLY Section 232 Aluminum

    ELSE IF origin == OTHER:
        ASK: "Percentage of aluminum in product?" → aluminum_pct
        ASK: "Country of origin for aluminum?" → aluminum_origin

        IF aluminum_origin == US:
            IF aluminum smelted AND cast in US:
                → EXEMPT (US_ORIGIN_ALUMINUM)
            ELSE:
                → APPLY Section 232 Aluminum on (aluminum_pct% of value)
        ELSE:
            → APPLY Section 232 Aluminum on (aluminum_pct% of value)

ELSE:
    → NOT APPLICABLE (0% aluminum)
```

**Required Data:**
- `aluminum_percentage`: 0-100%
- `aluminum_origin_country`: ISO 2-letter code
- `usmca_qualified`: boolean (only for CA/MX origin)
- `aluminum_smelted_and_cast_us`: boolean (only if aluminum_origin == US)

---

## 3. SECTION 301 CHINA TARIFFS

### 3.1 Section 301 Tariff Codes

**Tariff Codes:**
- 9903.88.03 (List 1: 25%)
- 9903.88.04 (List 2: 25%)
- 9903.88.09 (List 3: 7.5%)
- 9903.88.15 (List 4A: 7.5%)

**Decision Tree:**

```
IF origin == CN OR origin == HK OR origin == MO:

    ASK: "Does product match one of the 164 USTR product-specific exclusions?"
    IF yes → EXEMPT (9903.88.69)

    ELSE:
        ASK: "Is product classified as manufacturing equipment (14 USTR exclusions)?"
        IF yes → EXEMPT (9903.88.70)

        ELSE:
            → APPLY Section 301 tariff

            NOTE: Section 321 de minimis was ELIMINATED for CN/HK/MO in Sept 2024
            → Section 301 applies regardless of shipment value

ELSE:
    → NOT APPLICABLE (not from China/HK/Macau)
```

**Required Data:**
- `ustr_product_exclusion_match`: boolean
- `ustr_manufacturing_equipment`: boolean

**CRITICAL:** Section 321 de minimis NO LONGER APPLIES to CN/HK/MO as of September 2024!

---

## 4. IEEPA TARIFFS

**MAJOR UPDATE (2025):** IEEPA has expanded to multiple countries with various rates and exemption structures.

### 4.1 IEEPA Country-Specific Tariffs

#### 4.1.1 Canada IEEPA (9903.01.01 - 9903.01.15)

**Rate:** 25% additional duty (effective March 4, 2025)

**Decision Tree:**

```
IF origin == CA:

    ASK: "Does product qualify for USMCA?"
    IF yes:
        → EXEMPT (9903.01.26) - effective March 7, 2025 onward
        NOTE: Goods entered 3/4-3/6/25 remain subject to tariffs
              Refunds available via 1520(d) claim within one year

    ELSE IF product is energy or energy resources:
        → APPLY 10% rate (9903.01.13)

    ELSE IF product properly classified under Chapter 98:
        → EXEMPT (9802.00.40, 9802.00.50, 9802.00.60, 9802.00.80, 9813)

    ELSE:
        → APPLY 25% Canada IEEPA

ELSE:
    → NOT APPLICABLE (not from Canada)
```

#### 4.1.2 Mexico IEEPA (9903.01.01 - 9903.01.05)

**Rate:** 25% additional duty (effective March 4, 2025)

**Decision Tree:**

```
IF origin == MX:

    ASK: "Does product qualify for USMCA?"
    IF yes:
        → EXEMPT (9903.01.27) - effective March 7, 2025 onward
        NOTE: Goods entered 3/4-3/6/25 remain subject to tariffs
              Refunds available via 1520(d) claim within one year

    ELSE IF product properly classified under Chapter 98:
        → EXEMPT (9802.00.40, 9802.00.50, 9802.00.60, 9802.00.80, 9813)

    ELSE:
        → APPLY 25% Mexico IEEPA

ELSE:
    → NOT APPLICABLE (not from Mexico)
```

#### 4.1.3 China IEEPA (9903.01.20, 9903.01.24)

**Rate:** 25% additional duty (effective February 4, 2025)

**Decision Tree:**

```
IF origin == CN OR origin == HK OR origin == MO:

    IF product properly classified under Chapter 98:
        → EXEMPT (9802.00.40, 9802.00.50, 9802.00.60, 9802.00.80, 9813)

    ELSE:
        → APPLY 25% China IEEPA

ELSE:
    → NOT APPLICABLE (not from China/HK/Macau)
```

### 4.2 IEEPA Reciprocal (HS Code: 9903.01.25, 9903.01.63)

**Rates:**
- Baseline: 10% (9903.01.25) - effective April 5, 2025
- China escalation: 84% (9903.01.63) - effective April 9, 2025
- China peak: 125% (9903.01.63) - May 10-13, 2025 only
- China return: 10% (9903.01.25) - effective May 14, 2025

**Decision Tree:**

```
IF product subject to reciprocal tariffs:

    # Check Chapter 98 exemptions
    IF product properly classified under Chapter 98:
        → EXEMPT (9802.00.40, 9802.00.50, 9802.00.60, 9802.00.80, 9813)

    # Check preferential trade programs
    ELSE IF eligible under preferential trade program (General Note 3(c)(i)):
        # AGOA (9819), CBTPA/Haiti HOPE (9820), FTAs (9822)
        IF properly claimed:
            → EXEMPT

    # Check Annex II commodities
    ELSE IF product identified in Annex II:
        → EXEMPT (9903.01.32) - applies to articles of any country

    # Check Section 232 metals exemption
    ELSE IF product subject to Section 232 duties:
        → EXEMPT on metal portion (9903.01.33)
        NOTE: Non-metal portion may still be subject to reciprocal tariffs as of June 4, 2025

    # CRITICAL: Metal vs Non-Metal Split (as of June 4, 2025)
    CALCULATE total_metal_pct = steel_pct + aluminum_pct + copper_pct
    CALCULATE non_metal_pct = 100% - total_metal_pct

    IF non_metal_pct > 0:
        # Check U.S. content exemption
        ASK: "Percentage of U.S.-originating content by value?"
        IF us_content >= 20%:
            → EXEMPT on U.S. portion (9903.01.34)
            → APPLY reciprocal rate on non-U.S. portion
            NOTE: Requires split entry summary lines
            NOTE: U.S. content determined by physical characteristics under 19 U.S.C. § 1401a

        ELSE:
            ASK: "Is product informational materials (publications, films, recordings, artwork)?"
            IF yes:
                → EXEMPT (9903.01.22, 9903.01.12, 9903.01.03, 9903.01.31)
                NOTE: Includes HTSUS 8523.80.10, 9701-9705

            ELSE:
                → APPLY reciprocal rate on (non_metal_pct% of value)

    ELSE:
        → NOT APPLICABLE (100% metal content, covered by Section 232)

    # In-transit provisions (vessel mode only, before 6/16/25)
    IF vessel mode AND before 6/16/25:
        → EXEMPT (9903.01.28)

ELSE:
    → NOT APPLICABLE
```

**CRITICAL RULES:**
- Metal portion: Subject to Section 232, exempt from reciprocal under 9903.01.33
- Non-metal portion: Subject to IEEPA reciprocal tariffs (as of June 4, 2025)
- **Must report on separate entry summary lines** for metal vs non-metal
- U.S. content must be ≥20% for exemption (9903.01.34)
- U.S. content determined by physical characteristics only
- Split entry required: one line for U.S. content, one for non-U.S. content

### 4.3 IEEPA Fentanyl (HS Code: 9903.01.36)

**Rate:** 15% (or other rate specified by proclamation)

**Decision Tree:**

```
IF origin == CN OR origin == HK OR origin == MO:

    # CRITICAL: Fentanyl IEEPA applies to ENTIRE product value
    # NO exemptions, NO adjustments for metal composition

    → APPLY IEEPA Fentanyl on 100% of product value

    NOTE: This tariff is not commonly triggered for most products.
          It applies based on proclamation for specific time periods.

ELSE:
    → NOT APPLICABLE (not from China/HK/Macau)
```

**Required Data:** None (always applies if tariff is present, no exemptions)

---

## 5. COMPLETE DECISION ALGORITHM

### Step 1: Get Applicable Tariffs from AvaTax

```python
# Initial API call - NO metal parameters
tariffs = call_avatax_api(
    hs_code=base_hs,
    origin=origin_country,
    value=shipment_value
)

# Filter to Chapter 98/99 punitive tariffs
chapter_99_tariffs = [
    t for t in tariffs
    if t['type'] == 'PUNITIVE' or t['hsCode'].startswith(('9903', '9902', '98', '99'))
]
```

### Step 2: Categorize Tariffs

```python
for tariff in chapter_99_tariffs:
    if tariff['hsCode'].startswith('99038') and 'steel' in description:
        category = 'section_232_steel'
    elif tariff['hsCode'].startswith('99038') and 'aluminum' in description:
        category = 'section_232_aluminum'
    elif tariff['hsCode'].startswith('99038') and '301' in description:
        category = 'section_301'
    elif tariff['hsCode'] == '99030125':
        category = 'ieepa_reciprocal'
    elif tariff['hsCode'] == '99030136':
        category = 'ieepa_fentanyl'
```

### Step 3: Generate Questions Based on Detected Tariffs

```python
questions = []

# Section 232 Steel questions
if 'section_232_steel' in detected_categories:
    if origin in ['CA', 'MX']:
        questions.append({
            'id': 'usmca_qualified',
            'text': 'Does this product qualify for USMCA?',
            'type': 'boolean',
            'required': True
        })
    else:
        questions.extend([
            {
                'id': 'steel_percentage',
                'text': 'What percentage of the product is steel?',
                'type': 'slider',
                'min': 0,
                'max': 100,
                'unit': '%',
                'required': True
            },
            {
                'id': 'steel_origin',
                'text': 'What is the country of origin for the steel content?',
                'type': 'country_select',
                'required': True
            }
        ])
        # If steel_origin == US, ask follow-up:
        # 'Was the steel melted and poured in the United States?'

# Section 232 Aluminum questions (similar structure)

# Section 301 questions
if 'section_301' in detected_categories and origin in ['CN', 'HK', 'MO']:
    questions.extend([
        {
            'id': 'ustr_exclusion_match',
            'text': 'Does this product match one of the 164 USTR product-specific exclusions?',
            'type': 'boolean',
            'help': 'Check USTR Federal Register notices for detailed descriptions',
            'required': True
        },
        {
            'id': 'ustr_manufacturing_equipment',
            'text': 'Is this product classified as manufacturing equipment (14 USTR exclusions)?',
            'type': 'boolean',
            'required': True
        }
    ])

# IEEPA Reciprocal questions
if 'ieepa_reciprocal' in detected_categories and origin in ['CN', 'HK', 'MO']:
    questions.extend([
        {
            'id': 'us_content_percentage',
            'text': 'What percentage of the product value is U.S. content?',
            'type': 'slider',
            'min': 0,
            'max': 100,
            'unit': '%',
            'required': True
        },
        {
            'id': 'is_informational_materials',
            'text': 'Is this product informational materials (books, films, CDs, artwork)?',
            'type': 'boolean',
            'required': True
        }
    ])
```

### Step 4: Apply Stacking Logic

```python
def apply_stacking_logic(tariffs, answers, product_info):
    stacking_order = []

    # Sort by CBP stacking order
    sorted_tariffs = sort_by_cbp_order(tariffs)

    for tariff in sorted_tariffs:
        result = {
            'code': tariff['code'],
            'name': tariff['name'],
            'rate': tariff['rate'],
            'original_amount': tariff['amount'],
            'final_amount': 0,
            'excluded': False,
            'reasoning': ''
        }

        if tariff['category'] == 'section_232_steel':
            result = apply_section_232_steel_logic(tariff, answers, product_info)

        elif tariff['category'] == 'section_232_aluminum':
            result = apply_section_232_aluminum_logic(tariff, answers, product_info)

        elif tariff['category'] == 'section_301':
            result = apply_section_301_logic(tariff, answers, product_info)

        elif tariff['category'] == 'ieepa_reciprocal':
            result = apply_ieepa_reciprocal_logic(tariff, answers, product_info)

        elif tariff['category'] == 'ieepa_fentanyl':
            result = apply_ieepa_fentanyl_logic(tariff, answers, product_info)

        stacking_order.append(result)

    return stacking_order
```

---

## 6. REQUIRED QUESTIONS MATRIX

| Detected Tariff | Required Questions | Question Type | Validation |
|-----------------|-------------------|---------------|------------|
| **Section 232 Steel** | | | |
| (CA/MX origin) | USMCA qualified? | boolean | required |
| (Other origin) | Steel percentage | slider (0-100%) | required |
| (Other origin) | Steel origin country | country dropdown | required |
| (Steel from US) | Melted & poured in US? | boolean | conditional |
| **Section 232 Aluminum** | | | |
| (CA/MX origin) | USMCA qualified? | boolean | required |
| (Other origin) | Aluminum percentage | slider (0-100%) | required |
| (Other origin) | Aluminum origin country | country dropdown | required |
| (Aluminum from US) | Smelted & cast in US? | boolean | conditional |
| **Section 301** | | | |
| (CN/HK/MO only) | USTR exclusion match? | boolean | required |
| (CN/HK/MO only) | Manufacturing equipment? | boolean | required |
| **IEEPA Reciprocal** | | | |
| (CN/HK/MO only) | U.S. content percentage | slider (0-100%) | required |
| (CN/HK/MO only) | Informational materials? | boolean | required |
| **IEEPA Fentanyl** | NONE | N/A | Always applies |

---

## 7. CALCULATION FORMULAS

### Section 232 (Metal Tariffs)
```
IF metal_percentage > 0:
    IF exempt:
        duty = 0
    ELSE:
        duty = shipment_value × (metal_percentage / 100) × rate
ELSE:
    duty = 0  # Not applicable
```

### Section 301
```
IF exempt:
    duty = 0
ELSE:
    duty = shipment_value × rate
```

### IEEPA Reciprocal
```
total_metal_pct = steel_pct + aluminum_pct + copper_pct + lumber_pct
non_metal_pct = 100 - total_metal_pct

IF us_content_percentage > 20:
    duty = 0  # Exempt
ELIF is_informational_materials:
    duty = 0  # Exempt
ELSE:
    duty = shipment_value × (non_metal_pct / 100) × rate
```

### IEEPA Fentanyl
```
duty = shipment_value × rate  # Always 100% of value
```

---

## 8. IMPLEMENTATION NOTES

1. **NO GPT-4 question generation** - Questions are deterministic based on detected tariffs
2. **Static question templates** - Defined in code, not AI-generated
3. **Conditional questions** - Only ask follow-ups when needed (e.g., US origin for metals)
4. **Validation** - All required questions must be answered before analysis
5. **AvaTax Integration** - Single initial call, no metal parameters on first call
6. **Deterministic Logic** - Same inputs always produce same outputs
7. **Clear Reasoning** - Each tariff shows explicit calculation and exemption logic

---

## 9. NEXT STEPS

1. Create static question bank based on matrix above
2. Implement deterministic stacking algorithm
3. Replace GPT-4 question generation with conditional logic
4. Add validation for required questions
5. Show clear calculations in results
6. Test with known scenarios

---

## References

### Official CBP Resources
- **CBP IEEPA FAQ** (Primary Source): https://www.cbp.gov/trade/programs-administration/trade-remedies/IEEPA-FAQ
  - Last updated: December 2025
  - Covers Canada, Mexico, China, Brazil, India IEEPA tariffs
  - Includes exemption codes, effective dates, and implementation details

- **CBP Section 232 FAQs**: https://www.cbp.gov/trade/remedies/232-tariffs
  - Steel and aluminum tariff guidance
  - Exemption codes and requirements

- **CBP Section 301 Trade Remedies**: https://www.cbp.gov/trade/remedies/301-certain-products-china
  - China tariff lists and rates
  - USTR product exclusions

### Federal Regulations
- **19 U.S.C. § 1401a**: Customs value rules (for U.S. content determination)
- **19 CFR 141.57**: Split shipments requirements
- **19 CFR 141.68**: Entry date determination for duty rates
- **General Note 3(c)(i)**: Preferential trade programs (AGOA, CBTPA, FTAs)

### Proclamations and Federal Register
- Presidential Proclamations establishing IEEPA tariffs (2025)
- USTR Federal Register Notices for Section 301 exclusions
- Commerce Department Federal Register Notices for Section 232 exclusions

### Entry Summary Requirements
- **Chapter 98 Exceptions**: 9802.00.40, 9802.00.50, 9802.00.60, 9802.00.80, 9813
- **Split Entry Lines**: Required for metal vs non-metal portions
- **Reconciliation**: FTA reconciliation only method for flagged entries

### Key Exemption Codes Reference

#### USMCA (Canada/Mexico)
- 9903.01.26: Canadian goods (USMCA-qualified)
- 9903.01.27: Mexican goods (USMCA-qualified)

#### Section 232
- 9903.81.92: Steel melted and poured in USA
- 9903.01.94: Aluminum smelted in USA

#### Section 301
- 9903.88.69: USTR product-specific exclusions (164 exclusions)
- 9903.88.70: Manufacturing equipment exclusions (14 exclusions)

#### IEEPA Reciprocal
- 9903.01.25: Reciprocal tariff baseline (10%)
- 9903.01.63: China escalation (84% or 125%)
- 9903.01.28: In-transit exemption (vessel mode, before 6/16/25)
- 9903.01.30-9903.01.33: Various exclusions
- 9903.01.32: Annex II commodities
- 9903.01.33: Section 232 products (metal portion)
- 9903.01.34: U.S. content ≥20%

#### IEEPA Informational Materials
- 9903.01.21, 9903.01.22, 9903.01.12, 9903.01.03, 9903.01.31
- Covers publications, films, recordings, artwork (HTSUS 8523.80.10, 9701-9705)

#### Chapter 98 General Exemptions
- 9802.00.40, 9802.00.50, 9802.00.60: Repairs/alterations
- 9802.00.80: Articles assembled abroad
- 9813: Temporary Importation Under Bond (TIB)

### Implementation Status
- ✅ Research document completed (December 2025)
- ✅ Deterministic stacking algorithm implemented (stacking_logic.py)
- ✅ GPT-4 eliminated from question generation
- ✅ GPT-4 eliminated from stacking analysis
- ⚠️ IEEPA country-specific tariffs (CA/MX/CN) not yet fully implemented
- ⚠️ IEEPA reciprocal 84%/125% rate escalation logic not yet implemented
- ⚠️ Annex II commodity checking not yet implemented
- ⚠️ Preferential trade program checking not yet implemented
- HTSUS Chapter 99 Notes
