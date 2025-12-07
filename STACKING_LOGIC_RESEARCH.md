# CBP Tariff Stacking Logic - Comprehensive Research & Decision Tree

## Overview
This document formalizes the complete decision tree for Chapter 98/99 tariff stacking based on CBP regulations.

---

## 1. STACKING ORDER (CBP Guidance)

Per CBP, tariffs stack in this order:
1. **Section 232** (Steel/Aluminum/Automotive) - FIRST
2. **Section 301** (China tariffs) - SECOND
3. **IEEPA Reciprocal** (99030125) - THIRD
4. **IEEPA Fentanyl** (99030136) - FOURTH (last)

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

### 4.1 IEEPA Reciprocal (HS Code: 99030125)

**Rate:** 10% (NOT 9.6% - need to verify AvaTax response)

**Decision Tree:**

```
IF origin == CN OR origin == HK OR origin == MO:

    # CRITICAL: Reciprocal IEEPA applies to NON-METAL portion only

    CALCULATE total_metal_pct = steel_pct + aluminum_pct + copper_pct + lumber_pct
    CALCULATE non_metal_pct = 100% - total_metal_pct

    IF non_metal_pct > 0:
        ASK: "Percentage of U.S. content by value in product?"
        IF us_content > 20%:
            → EXEMPT on non-metal portion (9903.01.34)
        ELSE:
            ASK: "Is product informational materials (books, films, CDs, artwork)?"
            IF yes:
                → EXEMPT (9903.01.21)
            ELSE:
                → APPLY IEEPA Reciprocal on (non_metal_pct% of value)
    ELSE:
        → NOT APPLICABLE (100% metal content, covered by Section 232)

ELSE:
    → NOT APPLICABLE (not from China/HK/Macau)
```

**Required Data:**
- `us_content_percentage`: 0-100%
- `is_informational_materials`: boolean

**CRITICAL RULE:**
- IEEPA Reciprocal applies ONLY to the non-metal portion of product value
- Metal portion is covered by Section 232
- Section 232 does NOT exempt IEEPA, but they apply to different portions

---

### 4.2 IEEPA Fentanyl (HS Code: 99030136)

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

**Required Data:** None (always applies if tariff is present)

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
- CBP Section 232 FAQs
- CBP Section 301 Trade Remedies
- USTR Federal Register Notices
- Presidential Proclamations (IEEPA)
- HTSUS Chapter 99 Notes
