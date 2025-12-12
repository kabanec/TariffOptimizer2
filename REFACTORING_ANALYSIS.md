# Tariff Optimizer Refactoring Analysis
## Based on Budget Lab Yale Tariff ETRs Repository

**Date:** December 11, 2025
**Analyzed Repository:** https://github.com/Budget-Lab-Yale/Tariff-ETRs
**Target Pages:**
- https://tariff-optimizer2.onrender.com/exclusion-tester
- https://tariff-optimizer2.onrender.com/test-validator

---

## Executive Summary

After analyzing the Budget Lab Yale Tariff ETRs repository, I've identified several opportunities to enhance the Exclusion Tester and Test Validator pages. The Yale repository uses a sophisticated **hierarchical configuration system** with **authority precedence** and **import-weighted aggregation** that can inform improvements to our stacking logic validation.

### Key Takeaways from Budget Lab Yale Repository:

1. **Hierarchical Configuration Approach**: YAML-based tariff structures at variable HTS code lengths (4, 6, 8, 10 digits) using prefix matching
2. **Authority Hierarchy**: Clear stacking precedence (Section 232 > IEEPA Reciprocal > IEEPA Fentanyl)
3. **Multiple Specificity Levels**: Headline rates → Product rates → Product-country combinations
4. **USMCA Exemptions & Automobile Rebates**: Systematic handling of trade agreement adjustments
5. **Validation Through Aggregation**: Import-weighted averaging to partner×GTAP sector level

---

## Part 1: Exclusion Tester Refactoring Recommendations

### Current Strengths ✅

1. **Comprehensive Exclusion Database**: Well-researched with CBP/USTR sources
2. **Visual Comparison**: Side-by-side before/after duty display
3. **Conditional Logic Display**: Shows exclusion conditions and logic
4. **Update Checker**: AI-powered multi-phase analysis system
5. **Brand Compliance**: Updated to Avalara brand guidelines

### Recommended Refactoring 🔧

#### 1. Implement Hierarchical Configuration System

**Inspiration from Yale:** YAML-based tariff configuration at multiple HTS lengths

**Current Issue:**
```javascript
const EXCLUSIONS_DATABASE = {
    'section_232_steel': [
        {
            code: '9903.01.26',
            appliesToHsCodes: ['99038187', '99038188', ...]  // Hardcoded list
        }
    ]
}
```

**Proposed Refactoring:**
```javascript
const TARIFF_CONFIGURATION = {
    // Prefix matching like Yale repository
    prefixRules: {
        '7208': {  // Steel products chapter
            authorityLevel: 1,  // Section 232 = highest priority
            baseRate: 0.25,
            chapter99Codes: ['99038187', '99038188'],
            exclusions: {
                'USMCA_CA': {
                    prefix: '9903.01.26',
                    condition: (product) => product.origin === 'CA' && product.usmc a_qualified
                },
                'US_ORIGIN': {
                    prefix: '9903.81.92',
                    condition: (product) => product.melted_in_us && product.poured_in_us
                }
            }
        }
    },

    // Authority precedence (like Yale's stacking logic)
    authorityHierarchy: [
        { level: 1, name: 'Section 232', categories: ['steel', 'aluminum', 'automotive', 'lumber', 'copper'] },
        { level: 2, name: 'IEEPA Reciprocal', mutuallyExclusive: ['Section 232'] },
        { level: 3, name: 'IEEPA Fentanyl', stackingRule: 'additive', countries: ['CN', 'HK', 'MO'] },
        { level: 4, name: 'Section 301', countries: ['CN'] }
    ]
}
```

**Benefits:**
- Dynamic HTS code matching via prefix (like Yale's approach)
- Clear authority precedence hierarchy
- Easier to maintain and extend
- Aligns with CBP's actual stacking rules

---

#### 2. Add Specificity-Based Rate Selection

**Inspiration from Yale:** Headline rates → Product rates → Product-country combinations

**Proposed Addition:**
```javascript
function getApplicableRate(hsCode, country, tariffType) {
    // Check product-country specific rate (most specific)
    const productCountryRate = TARIFF_CONFIG[tariffType]
        .productCountryRates?.[`${hsCode}_${country}`];
    if (productCountryRate) return productCountryRate;

    // Check product-level rate (medium specificity)
    const productRate = TARIFF_CONFIG[tariffType]
        .productRates?.[hsCode];
    if (productRate) return productRate;

    // Fall back to headline rate (country default)
    return TARIFF_CONFIG[tariffType].headlineRates[country] || 0;
}
```

**Example Configuration:**
```javascript
IEEPA_RECIPROCAL: {
    headlineRates: {
        'CN': 0.10,  // 10% default for China
        'EU': 0.15,  // 15% default for EU
        'JP': 0.15   // 15% for Japan
    },
    productRates: {
        '8703': 0.20,  // Automobiles: 20% regardless of country
        '8471': 0.05   // Computers: 5% regardless of country
    },
    productCountryRates: {
        '8703_JP': 0.0,   // Japanese autos: exempt due to MFN >= 15%
        '7208_CA': 0.0    // Canadian steel: USMCA exempt
    }
}
```

---

#### 3. Implement Import-Weighted Validation

**Inspiration from Yale:** Validate using actual trade data

**Proposed Feature:**
```javascript
// Add trade volume data for statistical validation
const VALIDATION_DATA = {
    '3305.10.00.00': {
        'CN': {
            monthlyImportValue: 5000000,  // $5M/month
            yearlyVolume: 60000000,
            topExclusions: ['9903.88.69', 'SECTION_321']  // Most commonly used
        }
    }
};

function validateExclusionUsage(hsCode, country, selectedExclusion) {
    const data = VALIDATION_DATA[hsCode]?.[country];
    if (!data) return null;

    const isCommon = data.topExclusions.includes(selectedExclusion.code);
    return {
        importVolume: data.monthlyImportValue,
        isCommonlyUsed: isCommon,
        warning: !isCommon ? 'This exclusion is rarely used for this product/country combination' : null
    };
}
```

---

#### 4. Enhanced Duty Calculation Engine

**Current Implementation:**
```javascript
function generateMockDuties(hsCode, origin, value) {
    // Hardcoded logic with fixed percentages
    if (hsCode.startsWith('3305') && origin === 'CN') {
        duties.push({ rate: 0.25, amount: value * 0.25 });
    }
}
```

**Proposed Refactoring:**
```javascript
class TariffCalculationEngine {
    constructor(config) {
        this.config = config;
        this.appliedTariffs = [];
    }

    calculate(product) {
        this.appliedTariffs = [];

        // Step 1: Identify all potentially applicable tariffs
        const applicableTariffs = this.findApplicableTariffs(product);

        // Step 2: Apply authority hierarchy (Section 232 > IEEPA > 301)
        const stackedTariffs = this.applyStackingRules(applicableTariffs, product);

        // Step 3: Apply exclusions
        const finalTariffs = this.applyExclusions(stackedTariffs, product);

        // Step 4: Calculate totals with component breakdown
        return this.calculateTotals(finalTariffs, product);
    }

    findApplicableTariffs(product) {
        const tariffs = [];

        // Check each authority type
        for (const authority of this.config.authorityHierarchy) {
            const applicableTariff = this.checkAuthority(authority, product);
            if (applicableTariff) {
                tariffs.push({
                    ...applicableTariff,
                    authorityLevel: authority.level,
                    authorityName: authority.name
                });
            }
        }

        return tariffs;
    }

    applyStackingRules(tariffs, product) {
        // Sort by authority level (lower = higher priority)
        tariffs.sort((a, b) => a.authorityLevel - b.authorityLevel);

        const stacked = [];
        const excludedAuthorities = new Set();

        for (const tariff of tariffs) {
            // Check mutual exclusivity
            if (this.isMutuallyExclusive(tariff, stacked)) {
                tariff.excluded = true;
                tariff.exclusionReason = `Excluded due to ${stacked[0].authorityName} taking precedence`;
            } else {
                stacked.push(tariff);
            }
        }

        return tariffs;  // Return all for display, but mark excluded ones
    }

    applyExclusions(tariffs, product) {
        return tariffs.map(tariff => {
            if (tariff.excluded) return tariff;

            const applicableExclusion = this.findExclusion(tariff, product);
            if (applicableExclusion) {
                return {
                    ...tariff,
                    exclusion: applicableExclusion,
                    effectiveRate: applicableExclusion.effect === 'EXEMPT' ? 0 : tariff.rate * applicableExclusion.reduction,
                    originalRate: tariff.rate
                };
            }

            return tariff;
        });
    }

    calculateTotals(tariffs, product) {
        const breakdown = {
            tariffs: tariffs,
            totalBefore: 0,
            totalAfter: 0,
            savings: 0,
            components: []
        };

        tariffs.forEach(tariff => {
            if (!tariff.excluded) {
                const beforeAmount = product.value * tariff.rate;
                const afterAmount = product.value * (tariff.effectiveRate || tariff.rate);

                breakdown.totalBefore += beforeAmount;
                breakdown.totalAfter += afterAmount;
                breakdown.components.push({
                    name: tariff.authorityName,
                    beforeAmount,
                    afterAmount,
                    excluded: !!tariff.exclusion
                });
            }
        });

        breakdown.savings = breakdown.totalBefore - breakdown.totalAfter;
        return breakdown;
    }
}
```

---

#### 5. Add Scenario Comparison Tool

**New Feature Inspired by Yale:**

```html
<div class="scenario-comparison-section">
    <h3>Compare Tariff Scenarios</h3>
    <p>Compare duties under different product configurations:</p>

    <div class="scenario-grid">
        <!-- Scenario 1: Current Product -->
        <div class="scenario-card">
            <h4>Scenario 1: As-Is</h4>
            <ul>
                <li>Origin: China</li>
                <li>USMCA: No</li>
                <li>US Content: 0%</li>
                <li><strong>Total: $90.00</strong></li>
            </ul>
        </div>

        <!-- Scenario 2: USMCA Qualified -->
        <div class="scenario-card">
            <h4>Scenario 2: USMCA Qualified</h4>
            <ul>
                <li>Origin: Mexico</li>
                <li>USMCA: Yes</li>
                <li>US Content: 0%</li>
                <li><strong>Total: $25.00</strong></li>
                <li class="savings">💰 Save $65.00</li>
            </ul>
        </div>

        <!-- Scenario 3: High US Content -->
        <div class="scenario-card">
            <h4>Scenario 3: >20% US Content</h4>
            <ul>
                <li>Origin: China</li>
                <li>USMCA: No</li>
                <li>US Content: 25%</li>
                <li><strong>Total: $70.00</strong></li>
                <li class="savings">💰 Save $20.00</li>
            </ul>
        </div>
    </div>
</div>
```

---

## Part 2: Test Validator Comprehensive Test Scenarios

### Current Test Coverage Analysis

**Existing Tests:** 25 test cases covering Section 232, 301, IEEPA
**Gap Analysis:** Missing critical edge cases from Yale repository methodology

---

### Recommended Additional Test Scenarios

#### Category A: Authority Hierarchy & Stacking (Yale-Inspired)

**Test 26: Section 232 Dominance Over IEEPA**
```json
{
    "test_id": "TEST-026",
    "category": "stacking_precedence",
    "scenario": "Section 232 steel duty blocks IEEPA Reciprocal application",
    "input": {
        "hs_code": "7208.10.00.00",
        "origin_country": "CN",
        "value": 1000,
        "steel_content": 100,
        "duties_applied": [
            {"code": "99038187", "name": "Section 232 Steel", "rate": 0.25, "amount": 250},
            {"code": "99030125", "name": "IEEPA Reciprocal - China", "rate": 0.10, "amount": 100}
        ]
    },
    "expected_outcome": {
        "applicable_exclusions": [],
        "status": "Section 232 applies; IEEPA Reciprocal automatically excluded per 9903.01.33",
        "total_duty_before": 350,
        "total_duty_after": 250,
        "savings": 100,
        "broker_notes": "Per CBP guidance, products subject to Section 232 are exempt from IEEPA Reciprocal. Only Section 232 should apply."
    }
}
```

**Test 27: IEEPA Fentanyl Additive Stacking**
```json
{
    "test_id": "TEST-027",
    "category": "ieepa_fentanyl",
    "scenario": "IEEPA Fentanyl stacks additively with Section 301",
    "input": {
        "hs_code": "8471.30.01.00",
        "origin_country": "CN",
        "value": 5000,
        "duties_applied": [
            {"code": "99038803", "name": "Section 301 - List 1", "rate": 0.25, "amount": 1250},
            {"code": "99030122", "name": "IEEPA Fentanyl - China", "rate": 0.20, "amount": 1000}
        ]
    },
    "expected_outcome": {
        "applicable_exclusions": [],
        "status": "Both tariffs apply additively (no mutual exclusivity)",
        "total_duty_before": 2250,
        "total_duty_after": 2250,
        "savings": 0,
        "broker_notes": "IEEPA Fentanyl stacks with 301. Total effective rate = 45%."
    }
}
```

---

#### Category B: Specificity Hierarchy (Yale Multi-Level Rates)

**Test 28: Product-Country Specific Rate Override**
```json
{
    "test_id": "TEST-028",
    "category": "rate_specificity",
    "scenario": "Product-country rate overrides headline country rate",
    "input": {
        "hs_code": "8703.23.00.40",
        "origin_country": "JP",
        "value": 30000,
        "column_1_rate": 2.5,
        "duties_applied": [
            {"code": "99030124", "name": "IEEPA Reciprocal - Japan", "rate": 0.0, "amount": 0}
        ]
    },
    "expected_outcome": {
        "applicable_exclusions": [],
        "status": "Column 1 rate (2.5%) < 15%, so reciprocal = 15% - 2.5% = 12.5%. But product-country exemption applies.",
        "total_duty_before": 0,
        "total_duty_after": 0,
        "savings": 0,
        "broker_notes": "Japanese automobiles may have specific bilateral agreement rates. Verify with current IEEPA product-country matrix."
    }
}
```

**Test 29: Headline vs Product Rate Selection**
```json
{
    "test_id": "TEST-029",
    "category": "rate_specificity",
    "scenario": "Product-specific rate applies instead of country headline",
    "input": {
        "hs_code": "8471.50.01.50",
        "origin_country": "CN",
        "value": 2000,
        "duties_applied": [
            {"code": "99030125", "name": "IEEPA Reciprocal - China", "rate": 0.05, "amount": 100}
        ]
    },
    "expected_outcome": {
        "applicable_exclusions": [],
        "status": "Product-level rate (5% for electronics) applies instead of China headline (10%)",
        "total_duty_before": 100,
        "total_duty_after": 100,
        "savings": 0,
        "broker_notes": "Verify if this HTS has a specific product-level IEEPA rate different from China's 10% headline rate."
    }
}
```

---

#### Category C: USMCA Regional Value Content

**Test 30: USMCA 75% Auto Rule**
```json
{
    "test_id": "TEST-030",
    "category": "usmca_automotive",
    "scenario": "Automotive with 75% regional value content qualifies for USMCA",
    "input": {
        "hs_code": "8703.23.00.40",
        "origin_country": "MX",
        "value": 25000,
        "regional_value_content": 76,
        "usmca_qualified": true,
        "duties_applied": [
            {"code": "99038187", "name": "Section 232 Steel", "rate": 0.25, "amount": 6250},
            {"code": "99030801", "name": "Section 232 Automotive", "rate": 0.25, "amount": 6250}
        ]
    },
    "expected_outcome": {
        "applicable_exclusions": ["9903.01.27"],
        "status": "USMCA-qualified: Both Section 232 tariffs exempt",
        "total_duty_before": 12500,
        "total_duty_after": 0,
        "savings": 12500,
        "broker_notes": "USMCA automotive requires 75% RVC. Must verify labor value content and steel/aluminum melting origin requirements."
    }
}
```

**Test 31: USMCA Partial Content (Non-Qualified)**
```json
{
    "test_id": "TEST-031",
    "category": "usmca_automotive",
    "scenario": "Automotive with 65% RVC does NOT qualify for USMCA",
    "input": {
        "hs_code": "8703.23.00.40",
        "origin_country": "MX",
        "value": 25000,
        "regional_value_content": 65,
        "usmca_qualified": false,
        "duties_applied": [
            {"code": "99038187", "name": "Section 232 Steel", "rate": 0.25, "amount": 6250},
            {"code": "99030801", "name": "Section 232 Automotive", "rate": 0.25, "amount": 6250}
        ]
    },
    "expected_outcome": {
        "applicable_exclusions": [],
        "status": "FAILS USMCA qualification (needs ≥75% RVC). Full Section 232 duties apply.",
        "total_duty_before": 12500,
        "total_duty_after": 12500,
        "savings": 0,
        "broker_notes": "Even though origin is Mexico, USMCA benefits only apply if RVC ≥75%. Verify actual calculation methodology (net cost vs transaction value)."
    }
}
```

---

#### Category D: De Minimis & Entry Type

**Test 32: Section 321 Eliminated for China/HK**
```json
{
    "test_id": "TEST-032",
    "category": "section_321",
    "scenario": "De minimis elimination for China (Sept 2024)",
    "input": {
        "hs_code": "6109.10.00.40",
        "origin_country": "CN",
        "value": 750,
        "entry_type": "Section_321",
        "duties_applied": [
            {"code": "99038803", "name": "Section 301 - List 1", "rate": 0.25, "amount": 187.50}
        ]
    },
    "expected_outcome": {
        "applicable_exclusions": [],
        "status": "Section 321 does NOT exempt China/HK/Macau goods from Section 301 (as of Sept 2024)",
        "total_duty_before": 187.50,
        "total_duty_after": 187.50,
        "savings": 0,
        "broker_notes": "CRITICAL: Section 321 de minimis ($800) no longer exempts CN/HK/MO from Section 301. All shipments are dutiable."
    }
}
```

**Test 33: Section 321 Still Applies to Non-China**
```json
{
    "test_id": "TEST-033",
    "category": "section_321",
    "scenario": "De minimis still works for non-China origins",
    "input": {
        "hs_code": "6109.10.00.40",
        "origin_country": "VN",
        "value": 750,
        "entry_type": "Section_321",
        "duties_applied": []
    },
    "expected_outcome": {
        "applicable_exclusions": ["SECTION_321"],
        "status": "Section 321 de minimis exemption applies (value < $800, no quota restrictions)",
        "total_duty_before": 0,
        "total_duty_after": 0,
        "savings": 0,
        "broker_notes": "Section 321 still applies to Vietnam and other countries (only eliminated for CN/HK/MO)."
    }
}
```

---

#### Category E: Chapter 98 Provisions

**Test 34: 9802 Assembly Operations**
```json
{
    "test_id": "TEST-034",
    "category": "chapter_98",
    "scenario": "9802.00.80 assembly with US-origin components",
    "input": {
        "hs_code": "8473.30.51.00",
        "origin_country": "MX",
        "value": 5000,
        "us_component_value": 3000,
        "foreign_value_added": 2000,
        "entry_type": "9802.00.80",
        "duties_applied": [
            {"code": "99038803", "name": "Section 301", "rate": 0.25, "amount": 500}
        ]
    },
    "expected_outcome": {
        "applicable_exclusions": [],
        "status": "9802.00.80: Section 301 applies ONLY to foreign value added ($2,000)",
        "total_duty_before": 1250,
        "total_duty_after": 500,
        "savings": 750,
        "broker_notes": "Under 9802.00.80, duties apply only to foreign value added. US component value ($3,000) is duty-free."
    }
}
```

**Test 35: 9801 Temporary Export**
```json
{
    "test_id": "TEST-035",
    "category": "chapter_98",
    "scenario": "9801 temporary export return (duty-free)",
    "input": {
        "hs_code": "8471.30.01.00",
        "origin_country": "US",
        "value": 10000,
        "entry_type": "9801.00.10",
        "temporarily_exported_from_us": true,
        "duties_applied": []
    },
    "expected_outcome": {
        "applicable_exclusions": ["9801"],
        "status": "9801: US goods returned without having been advanced in value or improved abroad are duty-free",
        "total_duty_before": 0,
        "total_duty_after": 0,
        "savings": 0,
        "broker_notes": "9801 requires proof of US origin and evidence that goods were not improved/advanced in value abroad."
    }
}
```

---

#### Category F: Time-Sensitive Exclusions

**Test 36: Expired Product Exclusion**
```json
{
    "test_id": "TEST-036",
    "category": "expiration_validation",
    "scenario": "Product exclusion expired (quantity exhausted)",
    "input": {
        "hs_code": "7318.15.50.60",
        "origin_country": "CN",
        "value": 5000,
        "exclusion_request_id": "DOC-EXCLUSION-12345",
        "exclusion_expiration": "2025-03-15",
        "entry_date": "2025-06-01",
        "duties_applied": [
            {"code": "99038187", "name": "Section 232 Steel", "rate": 0.25, "amount": 1250}
        ]
    },
    "expected_outcome": {
        "applicable_exclusions": [],
        "status": "Product exclusion EXPIRED on 2025-03-15. Full Section 232 duties apply.",
        "total_duty_before": 1250,
        "total_duty_after": 1250,
        "savings": 0,
        "broker_notes": "CRITICAL: Verify exclusion validity dates. Commerce exclusions are valid for 1 year or until quantity exhausted. No new exclusions granted after Feb 10, 2025."
    }
}
```

**Test 37: Quantity-Limited Exclusion Exceeded**
```json
{
    "test_id": "TEST-037",
    "category": "quantity_limits",
    "scenario": "Product exclusion quantity limit exceeded",
    "input": {
        "hs_code": "7318.15.50.60",
        "origin_country": "CN",
        "value": 5000,
        "exclusion_request_id": "DOC-EXCLUSION-12345",
        "exclusion_quantity_limit": 100000,
        "cumulative_imports_ytd": 105000,
        "duties_applied": [
            {"code": "99038187", "name": "Section 232 Steel", "rate": 0.25, "amount": 1250}
        ]
    },
    "expected_outcome": {
        "applicable_exclusions": [],
        "status": "Exclusion quantity limit exhausted (105,000 lbs imported vs 100,000 lb limit). Duties apply.",
        "total_duty_before": 1250,
        "total_duty_after": 1250,
        "savings": 0,
        "broker_notes": "Product exclusions have both time AND quantity limits. Must track cumulative imports against approved quantity."
    }
}
```

---

#### Category G: Complex Multi-Material Products

**Test 38: Mixed Steel/Aluminum Content**
```json
{
    "test_id": "TEST-038",
    "category": "multi_material",
    "scenario": "Product contains both steel (60%) and aluminum (30%)",
    "input": {
        "hs_code": "8703.23.00.40",
        "origin_country": "JP",
        "value": 30000,
        "steel_content": 60,
        "steel_origin": "US",
        "aluminum_content": 30,
        "aluminum_origin": "CA",
        "duties_applied": [
            {"code": "99038187", "name": "Section 232 Steel", "rate": 0.25, "amount": 4500},
            {"code": "99038502", "name": "Section 232 Aluminum", "rate": 0.10, "amount": 900}
        ]
    },
    "expected_outcome": {
        "applicable_exclusions": ["9903.81.92", "9903.01.26"],
        "status": "Steel portion exempt (US-melted). Aluminum portion exempt (Canada USMCA).",
        "total_duty_before": 5400,
        "total_duty_after": 0,
        "savings": 5400,
        "steel_component_duty": 0,
        "aluminum_component_duty": 0,
        "broker_notes": "Multi-material products: Apply exclusions independently to each material component."
    }
}
```

**Test 39: Steel Content Below De Minimis (2.5%)**
```json
{
    "test_id": "TEST-039",
    "category": "de_minimis_content",
    "scenario": "Steel content is 2% (below de minimis threshold)",
    "input": {
        "hs_code": "8471.30.01.00",
        "origin_country": "CN",
        "value": 2000,
        "steel_content": 2,
        "duties_applied": []
    },
    "expected_outcome": {
        "applicable_exclusions": [],
        "status": "Steel content ≤2.5% qualifies for de minimis exemption from Section 232 Steel",
        "total_duty_before": 0,
        "total_duty_after": 0,
        "savings": 0,
        "broker_notes": "Section 232 has de minimis thresholds: Steel ≤2.5%, Aluminum ≤10%. Below threshold = no Section 232 applies."
    }
}
```

---

#### Category H: EU/JP/KR MFN Threshold Logic

**Test 40: EU with MFN = 5% (Reciprocal Applies)**
```json
{
    "test_id": "TEST-040",
    "category": "ieepa_reciprocal_threshold",
    "scenario": "EU product with MFN 5% < 15% threshold",
    "input": {
        "hs_code": "6403.99.60.30",
        "origin_country": "IT",
        "value": 5000,
        "column_1_mfn_rate": 5,
        "duties_applied": [
            {"code": "99030124", "name": "IEEPA Reciprocal - EU", "rate": 0.10, "amount": 500}
        ]
    },
    "expected_outcome": {
        "applicable_exclusions": [],
        "status": "MFN (5%) < 15%, so reciprocal = 15% - 5% = 10%. Applies correctly.",
        "total_duty_before": 500,
        "total_duty_after": 500,
        "savings": 0,
        "broker_notes": "EU/JP/KR threshold logic: If MFN ≥15%, reciprocal = 0%. If MFN <15%, reciprocal = (15% - MFN)."
    }
}
```

**Test 41: Japan with MFN = 20% (Reciprocal Exempt)**
```json
{
    "test_id": "TEST-041",
    "category": "ieepa_reciprocal_threshold",
    "scenario": "Japanese product with MFN 20% ≥ 15% threshold",
    "input": {
        "hs_code": "8703.23.00.40",
        "origin_country": "JP",
        "value": 30000,
        "column_1_mfn_rate": 20,
        "duties_applied": [
            {"code": "99030124", "name": "IEEPA Reciprocal - Japan", "rate": 0.0, "amount": 0}
        ]
    },
    "expected_outcome": {
        "applicable_exclusions": [],
        "status": "MFN (20%) ≥15%, so reciprocal rate = 0% (exempt). No IEEPA Reciprocal applies.",
        "total_duty_before": 0,
        "total_duty_after": 0,
        "savings": 0,
        "broker_notes": "High-MFN products from EU/JP/KR automatically exempt from IEEPA Reciprocal."
    }
}
```

---

#### Category I: Informational Materials Exemption

**Test 42: Publications Exempt from IEEPA**
```json
{
    "test_id": "TEST-042",
    "category": "informational_materials",
    "scenario": "Books/publications exempt from IEEPA tariffs",
    "input": {
        "hs_code": "4901.99.00.40",
        "origin_country": "CN",
        "value": 1000,
        "material_type": "printed_books",
        "duties_applied": [
            {"code": "99030125", "name": "IEEPA Reciprocal - China", "rate": 0.10, "amount": 100},
            {"code": "99030122", "name": "IEEPA Fentanyl - China", "rate": 0.20, "amount": 200}
        ]
    },
    "expected_outcome": {
        "applicable_exclusions": ["9903.01.21"],
        "status": "Informational materials (books, films, CDs, artworks) are exempt from IEEPA tariffs",
        "total_duty_before": 300,
        "total_duty_after": 0,
        "savings": 300,
        "broker_notes": "9903.01.21 exempts publications, films, posters, phonograph records, photographs, microfilms, tapes, CDs, artworks, and news wire feeds from IEEPA."
    }
}
```

---

### Summary of New Test Coverage

| Category | Test IDs | Focus Area |
|----------|----------|-----------|
| **Authority Hierarchy** | 26-27 | Stacking precedence, mutual exclusivity |
| **Specificity Levels** | 28-29 | Headline vs product vs product-country rates |
| **USMCA RVC** | 30-31 | Regional value content thresholds |
| **De Minimis/Entry Type** | 32-33 | Section 321 elimination for China |
| **Chapter 98** | 34-35 | Assembly operations, temporary exports |
| **Time Limits** | 36-37 | Expiration dates, quantity limits |
| **Multi-Material** | 38-39 | Mixed content, de minimis thresholds |
| **MFN Threshold** | 40-41 | EU/JP/KR 15% threshold logic |
| **Informational Materials** | 42 | IEEPA exemption for publications |

**Total New Tests:** 17
**New Total Test Suite:** 42 comprehensive scenarios

---

## Implementation Priority

### Phase 1: Critical Refactoring (Week 1-2)
1. ✅ Implement authority hierarchy engine
2. ✅ Add hierarchical rate selection (headline → product → product-country)
3. ✅ Create TariffCalculationEngine class

### Phase 2: Enhanced Testing (Week 3)
4. ✅ Add 17 new test scenarios to test_validator
5. ✅ Implement automated validation checks
6. ✅ Add broker notes comparison

### Phase 3: Advanced Features (Week 4)
7. ✅ Add scenario comparison tool
8. ✅ Implement import-weighted validation
9. ✅ Create YAML configuration export/import

---

## Files to Create/Modify

### New Files:
1. `/static/tariff_configuration.yaml` - Hierarchical config like Yale
2. `/static/exclusion_test_cases_extended.json` - Add 17 new tests
3. `/static/js/tariff_engine.js` - New calculation engine
4. `/templates/scenario_comparison.html` - New comparison tool

### Modified Files:
1. `/templates/exclusion_tester.html` - Refactor to use new engine
2. `/templates/test_validator.html` - Add extended test suite
3. `/app.py` - Add scenario comparison endpoints
4. `/stacking_logic.py` - Align with authority hierarchy

---

## References

- **Budget Lab Yale Repository:** https://github.com/Budget-Lab-Yale/Tariff-ETRs
- **CBP Section 232 FAQs:** https://www.cbp.gov/trade/programs-administration/entry-summary/232-tariffs-aluminum-and-steel-faqs
- **USTR Section 301:** https://ustr.gov/issue-areas/enforcement/section-301-investigations
- **Federal Register (IEEPA):** https://www.federalregister.gov/
- **USMCA Text:** https://ustr.gov/trade-agreements/free-trade-agreements/united-states-mexico-canada-agreement

---

**Next Steps:**
1. Review and approve refactoring recommendations
2. Prioritize implementation phases
3. Create extended test scenario JSON file
4. Begin Phase 1 development
