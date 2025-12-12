#!/usr/bin/env python3
"""
Deterministic Tariff Stacking Logic
Based on STACKING_LOGIC_RESEARCH.md decision trees

This module implements CBP-compliant tariff stacking analysis without GPT-4.
All logic is deterministic and based on formal decision trees.
"""

import logging

logger = logging.getLogger(__name__)

# CBP Stacking Order (CRITICAL - do not change)
#
# IMPORTANT DISTINCTION:
# - REPORTING ORDER (per CSMS #65829726): "301, Fentanyl, Reciprocal, 232/201"
#   This is how tariffs are LISTED on entry forms
#
# - EVALUATION ORDER (below): Determines which tariffs APPLY
#   Section 232 must be evaluated BEFORE IEEPA Reciprocal because:
#   * Exemption 9903.01.33: Section 232 materials are EXEMPT from IEEPA Reciprocal
#   * To calculate the exempt portion, Section 232 must be evaluated first
#   * Then IEEPA Reciprocal applies ONLY to non-232 portion
#
# Updated December 2025 based on current CBP guidance and Federal Register notices
# CRITICAL: HTS code-based Section 232 tariffs MUST be checked BEFORE material composition
# If a product is classified under automotive/buses HTS codes, material-based 232 tariffs do NOT apply
STACKING_ORDER = {
    'section_301': 1,              # FIRST: Section 301 (China tariffs)
    'ieepa_fentanyl': 2,           # SECOND: IEEPA Fentanyl
    'section_232_automotive': 3,   # THIRD: Section 232 Automotive (HTS code-based, mutually exclusive with material tariffs)
    'section_232_buses': 4,        # FOURTH: Section 232 Buses (HTS code-based, mutually exclusive with material tariffs)
    'section_232_steel': 5,        # FIFTH: Section 232 Steel (ONLY if NOT automotive/buses)
    'section_232_aluminum': 6,     # SIXTH: Section 232 Aluminum (ONLY if NOT automotive/buses)
    'section_232_copper': 7,       # SEVENTH: Section 232 Copper (ONLY if NOT automotive/buses)
    'section_232_lumber': 8,       # EIGHTH: Section 232 Lumber/Softwood (ONLY if NOT automotive/buses)
    'ieepa_reciprocal': 9          # NINTH: IEEPA Reciprocal (applies to NON-232 portion only, exemption 9903.01.33)
}


def get_required_questions(detected_tariffs, origin_country):
    """
    Generate static list of questions based on detected tariffs.
    NO GPT-4 - this is deterministic based on tariff categories.

    Args:
        detected_tariffs: List of tariff dicts with 'category' field
        origin_country: ISO 2-letter country code

    Returns:
        List of question dicts with id, text, type, required fields
    """
    questions = []
    question_index = 0

    # Track which categories we've detected
    categories = {t['category'] for t in detected_tariffs}

    # Section 232 Steel Questions
    if 'section_232_steel' in categories:
        if origin_country in ['CA', 'MX']:
            questions.append({
                'id': 'usmca_qualified',
                'index': question_index,
                'text': 'Does this product qualify for USMCA (United States-Mexico-Canada Agreement)?',
                'type': 'boolean',
                'options': ['Yes', 'No'],
                'required': True,
                'help': 'USMCA-qualified products from Canada/Mexico are exempt from Section 232 tariffs'
            })
            question_index += 1
        else:
            questions.append({
                'id': 'steel_percentage',
                'index': question_index,
                'text': 'What percentage of the product (by value) is steel?',
                'type': 'slider',
                'min': 0,
                'max': 100,
                'unit': '%',
                'required': True,
                'help': 'Section 232 Steel tariff applies only to the steel portion of the product'
            })
            question_index += 1

            questions.append({
                'id': 'steel_origin_country',
                'index': question_index,
                'text': 'What is the country of origin for the steel content?',
                'type': 'country_select',
                'required': True,
                'help': 'If steel was melted and poured in the United States, it may be exempt'
            })
            question_index += 1

            # Conditional question - will only show if user selects US
            questions.append({
                'id': 'steel_melted_poured_us',
                'index': question_index,
                'text': 'Was the steel melted AND poured in the United States?',
                'type': 'boolean',
                'options': ['Yes', 'No'],
                'required': True,
                'conditional': {
                    'depends_on': 'steel_origin_country',
                    'value': 'US'
                },
                'help': 'Exemption code 9903.81.92 applies if steel was both melted and poured in the US'
            })
            question_index += 1

    # Section 232 Aluminum Questions
    if 'section_232_aluminum' in categories:
        if origin_country in ['CA', 'MX']:
            # Only ask if we haven't already asked for steel
            if 'usmca_qualified' not in [q['id'] for q in questions]:
                questions.append({
                    'id': 'usmca_qualified',
                    'index': question_index,
                    'text': 'Does this product qualify for USMCA (United States-Mexico-Canada Agreement)?',
                    'type': 'boolean',
                    'options': ['Yes', 'No'],
                    'required': True,
                    'help': 'USMCA-qualified products from Canada/Mexico are exempt from Section 232 tariffs'
                })
                question_index += 1
        else:
            questions.append({
                'id': 'aluminum_percentage',
                'index': question_index,
                'text': 'What percentage of the product (by value) is aluminum?',
                'type': 'slider',
                'min': 0,
                'max': 100,
                'unit': '%',
                'required': True,
                'help': 'Section 232 Aluminum tariff applies only to the aluminum portion of the product'
            })
            question_index += 1

            questions.append({
                'id': 'aluminum_origin_country',
                'index': question_index,
                'text': 'What is the country of origin for the aluminum content?',
                'type': 'country_select',
                'required': True,
                'help': 'If aluminum was smelted and cast in the United States, it may be exempt'
            })
            question_index += 1

            questions.append({
                'id': 'aluminum_smelted_cast_us',
                'index': question_index,
                'text': 'Was the aluminum smelted AND cast in the United States?',
                'type': 'boolean',
                'options': ['Yes', 'No'],
                'required': True,
                'conditional': {
                    'depends_on': 'aluminum_origin_country',
                    'value': 'US'
                },
                'help': 'Aluminum smelted and cast in the US is exempt from Section 232 tariffs'
            })
            question_index += 1

    # Section 301 Questions (only for China/Hong Kong/Macau)
    if 'section_301' in categories and origin_country in ['CN', 'HK', 'MO']:
        questions.append({
            'id': 'ustr_product_exclusion',
            'index': question_index,
            'text': 'Does this product match one of the 164 USTR product-specific exclusions?',
            'type': 'boolean',
            'options': ['Yes', 'No'],
            'required': True,
            'help': 'Check USTR Federal Register notices for detailed exclusion descriptions. Exemption code: 9903.88.69'
        })
        question_index += 1

        questions.append({
            'id': 'ustr_manufacturing_equipment',
            'index': question_index,
            'text': 'Is this product classified as manufacturing equipment under the 14 USTR exclusions?',
            'type': 'boolean',
            'options': ['Yes', 'No'],
            'required': True,
            'help': 'Manufacturing equipment may qualify for exemption. Exemption code: 9903.88.70'
        })
        question_index += 1

    # IEEPA Reciprocal Questions
    # Per CSMS #65829726: Applies to all countries (effective Aug 7, 2025)
    # China/HK/MO continue at 10% under 9903.01.25
    if 'ieepa_reciprocal' in categories:
        # Skip Column 2 countries - they're automatically exempt
        column_2_countries = ['BY', 'CU', 'KP', 'RU']
        if origin_country not in column_2_countries:
            # Special question for EU, Japan, South Korea - need Column 1 (MFN) rate
            eu_countries = ['AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR',
                            'DE', 'GR', 'HU', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL',
                            'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE']
            special_calculation_countries = eu_countries + ['JP', 'KR']

            if origin_country in special_calculation_countries:
                questions.append({
                    'id': 'column_1_duty_rate',
                    'index': question_index,
                    'text': f'What is the Column 1 (MFN) duty rate for this HTS code?',
                    'type': 'slider',
                    'min': 0,
                    'max': 50,
                    'unit': '%',
                    'required': True,
                    'help': f'For {origin_country} products: If Column 1 rate ≥15%, no reciprocal tariff applies. If <15%, reciprocal rate = 15% - Column 1 rate. This ensures total duty = max(Column 1 rate, 15%).'
                })
                question_index += 1

            questions.append({
                'id': 'is_humanitarian_donation',
                'index': question_index,
                'text': 'Is this a humanitarian donation (food, clothing, medicine)?',
                'type': 'boolean',
                'options': ['Yes', 'No'],
                'required': True,
                'help': 'Humanitarian donations are exempt from IEEPA Reciprocal tariff (exemption code: 9903.01.30)'
            })
            question_index += 1

            questions.append({
                'id': 'us_content_percentage',
                'index': question_index,
                'text': 'What percentage of the product value is U.S. content?',
                'type': 'slider',
                'min': 0,
                'max': 100,
                'unit': '%',
                'required': True,
                'help': 'Products with >20% U.S. content are exempt from IEEPA Reciprocal tariff (exemption code: 9903.01.34)'
            })
            question_index += 1

            questions.append({
                'id': 'is_informational_materials',
                'index': question_index,
                'text': 'Is this product informational materials (books, films, CDs, artwork)?',
                'type': 'boolean',
                'options': ['Yes', 'No'],
                'required': True,
                'help': 'Informational materials are exempt from IEEPA Reciprocal tariff (exemption code: 9903.01.21)'
            })
            question_index += 1

    # IEEPA Fentanyl - NO QUESTIONS (always applies, no exemptions)

    return questions


def parse_answer(answer, question_type):
    """
    Parse user answer into standardized format.

    Args:
        answer: Raw answer string or value
        question_type: 'boolean', 'slider', 'country_select'

    Returns:
        Parsed value (bool, float, or string)
    """
    if question_type == 'boolean':
        answer_str = str(answer).lower().strip()
        return answer_str in ['yes', 'true', '1']

    elif question_type == 'slider':
        # Extract numeric value from string like "25%" or "25.0%"
        answer_str = str(answer).replace('%', '').strip()
        try:
            return float(answer_str)
        except:
            return 0.0

    elif question_type == 'country_select':
        # Return uppercase country code
        return str(answer).strip().upper()

    return answer


def apply_section_232_steel_logic(tariff, answers, product_info):
    """
    Apply Section 232 Steel decision tree logic.

    Args:
        tariff: Tariff dict with code, name, rate, amount
        answers: Dict of {question_id: answer_value}
        product_info: Dict with origin_country, hs_code, value

    Returns:
        Dict with excluded (bool), exemption_code, reasoning, final_amount
    """
    origin = product_info['origin_country']
    result = {
        'excluded': False,
        'exemption_code': None,
        'reasoning': '',
        'final_amount': tariff['amount']
    }

    # Check if product has steel content
    steel_pct = answers.get('steel_percentage', 0)
    if steel_pct == 0:
        result['excluded'] = True
        result['exemption_code'] = 'N/A'
        result['reasoning'] = 'NOT APPLICABLE: Product has 0% steel composition'
        result['final_amount'] = 0
        return result

    # CA/MX USMCA logic
    if origin in ['CA', 'MX']:
        usmca_qualified = answers.get('usmca_qualified', False)
        if usmca_qualified:
            result['excluded'] = True
            result['exemption_code'] = '9903.01.26' if origin == 'CA' else '9903.01.27'
            result['reasoning'] = f'EXEMPT: USMCA-qualified product from {origin}'
            result['final_amount'] = 0
        else:
            result['reasoning'] = f'APPLIES: Product from {origin} does not qualify for USMCA exemption'

    # Other origins - check steel origin and US melting
    else:
        steel_origin = answers.get('steel_origin_country', '')

        if steel_origin == 'US':
            steel_melted_us = answers.get('steel_melted_poured_us', False)
            if steel_melted_us:
                result['excluded'] = True
                result['exemption_code'] = '9903.81.92'
                result['reasoning'] = 'EXEMPT: Steel melted and poured in the United States'
                result['final_amount'] = 0
            else:
                # Apply to steel portion only
                final_amount = product_info['value'] * (steel_pct / 100.0) * tariff['rate']
                result['reasoning'] = f'APPLIES to {steel_pct:.1f}% steel portion: Steel from US but not melted/poured in US'
                result['final_amount'] = final_amount
        else:
            # Apply to steel portion only
            final_amount = product_info['value'] * (steel_pct / 100.0) * tariff['rate']
            result['reasoning'] = f'APPLIES to {steel_pct:.1f}% steel portion: Steel from {steel_origin}'
            result['final_amount'] = final_amount

    return result


def apply_section_232_aluminum_logic(tariff, answers, product_info):
    """
    Apply Section 232 Aluminum decision tree logic.
    """
    origin = product_info['origin_country']
    result = {
        'excluded': False,
        'exemption_code': None,
        'reasoning': '',
        'final_amount': tariff['amount']
    }

    # Check if product has aluminum content
    aluminum_pct = answers.get('aluminum_percentage', 0)
    if aluminum_pct == 0:
        result['excluded'] = True
        result['exemption_code'] = 'N/A'
        result['reasoning'] = 'NOT APPLICABLE: Product has 0% aluminum composition'
        result['final_amount'] = 0
        return result

    # CA/MX USMCA logic
    if origin in ['CA', 'MX']:
        usmca_qualified = answers.get('usmca_qualified', False)
        if usmca_qualified:
            result['excluded'] = True
            result['exemption_code'] = '9903.01.26' if origin == 'CA' else '9903.01.27'
            result['reasoning'] = f'EXEMPT: USMCA-qualified product from {origin}'
            result['final_amount'] = 0
        else:
            result['reasoning'] = f'APPLIES: Product from {origin} does not qualify for USMCA exemption'

    # Other origins - check aluminum origin and US smelting
    else:
        aluminum_origin = answers.get('aluminum_origin_country', '')

        if aluminum_origin == 'US':
            aluminum_smelted_us = answers.get('aluminum_smelted_cast_us', False)
            if aluminum_smelted_us:
                result['excluded'] = True
                result['exemption_code'] = 'US_ORIGIN'
                result['reasoning'] = 'EXEMPT: Aluminum smelted and cast in the United States'
                result['final_amount'] = 0
            else:
                # Apply to aluminum portion only
                final_amount = product_info['value'] * (aluminum_pct / 100.0) * tariff['rate']
                result['reasoning'] = f'APPLIES to {aluminum_pct:.1f}% aluminum portion: Aluminum from US but not smelted/cast in US'
                result['final_amount'] = final_amount
        else:
            # Apply to aluminum portion only
            final_amount = product_info['value'] * (aluminum_pct / 100.0) * tariff['rate']
            result['reasoning'] = f'APPLIES to {aluminum_pct:.1f}% aluminum portion: Aluminum from {aluminum_origin}'
            result['final_amount'] = final_amount

    return result


def apply_section_232_copper_logic(tariff, answers, product_info):
    """
    Apply Section 232 Copper decision tree logic.
    Based on CBP guidance: 50% rate on copper derivatives
    """
    origin = product_info['origin_country']
    result = {
        'excluded': False,
        'exemption_code': None,
        'reasoning': '',
        'final_amount': tariff['amount']
    }

    # Check if product has copper content
    copper_pct = answers.get('copper_percentage', 0)
    if copper_pct == 0:
        result['excluded'] = True
        result['exemption_code'] = 'N/A'
        result['reasoning'] = 'NOT APPLICABLE: Product has 0% copper composition'
        result['final_amount'] = 0
        return result

    # CA/MX USMCA logic (if applicable for copper)
    if origin in ['CA', 'MX']:
        usmca_qualified = answers.get('usmca_qualified', False)
        if usmca_qualified:
            result['excluded'] = True
            result['exemption_code'] = '9903.01.26' if origin == 'CA' else '9903.01.27'
            result['reasoning'] = f'EXEMPT: USMCA-qualified product from {origin}'
            result['final_amount'] = 0
        else:
            # Apply to copper portion only (50% rate)
            final_amount = product_info['value'] * (copper_pct / 100.0) * tariff['rate']
            result['reasoning'] = f'APPLIES to {copper_pct:.1f}% copper portion at 50% rate'
            result['final_amount'] = final_amount
    else:
        # Apply to copper portion only (50% rate)
        final_amount = product_info['value'] * (copper_pct / 100.0) * tariff['rate']
        result['reasoning'] = f'APPLIES to {copper_pct:.1f}% copper portion at 50% rate'
        result['final_amount'] = final_amount

    return result


def apply_section_232_lumber_logic(tariff, answers, product_info):
    """
    Apply Section 232 Lumber/Softwood decision tree logic.
    Based on CBP guidance: 10% rate on softwood lumber
    """
    origin = product_info['origin_country']
    result = {
        'excluded': False,
        'exemption_code': None,
        'reasoning': '',
        'final_amount': tariff['amount']
    }

    # Check if product has lumber content
    lumber_pct = answers.get('lumber_percentage', 0)
    if lumber_pct == 0:
        result['excluded'] = True
        result['exemption_code'] = 'N/A'
        result['reasoning'] = 'NOT APPLICABLE: Product has 0% lumber composition'
        result['final_amount'] = 0
        return result

    # Lumber Section 232 does NOT have USMCA exemptions per Yale data
    # Apply to lumber portion only (10% rate)
    final_amount = product_info['value'] * (lumber_pct / 100.0) * tariff['rate']
    result['reasoning'] = f'APPLIES to {lumber_pct:.1f}% lumber portion at 10% rate'
    result['final_amount'] = final_amount

    return result


def apply_section_232_buses_logic(tariff, answers, product_info):
    """
    Apply Section 232 Buses (Heading 8702) decision tree logic.
    Based on CBP guidance: 10% rate, NO USMCA exemptions
    HTS Codes: 87021031, 87021061, 87022031, 87022061, 87023031, 87023061,
               87024031, 87024061, 87029031, 87029061
    """
    result = {
        'excluded': False,
        'exemption_code': None,
        'reasoning': '',
        'final_amount': tariff['amount']
    }

    # Buses Section 232 has NO USMCA exemptions per Yale data
    # Simply apply 10% rate to full product value
    result['reasoning'] = 'APPLIES: Section 232 Buses tariff at 10% rate (Heading 8702, no USMCA exemptions available)'
    # tariff['amount'] already calculated as value * rate, so use as-is

    return result


def apply_section_232_automotive_logic(tariff, answers, product_info):
    """
    Apply Section 232 Automotive decision tree logic.
    Based on CBP guidance: 25% base rate with auto rebate and USMCA adjustments

    Categories:
    - Passenger vehicles & light trucks (~15 HTS codes)
    - Automobile parts (90+ HTS codes)
    - Medium/Heavy duty vehicles completed (25 HTS codes)
    - MHD vehicle parts (160+ HTS codes)

    Calculations:
    1. Base rate: 25%
    2. Auto rebate: 3.75% * 33% = 1.2375 percentage points reduction
    3. Effective rate before USMCA: 25% - 1.2375% = 23.7625%
    4. USMCA exemption (CA/MX): Adjusted share = usmca_share * 40% US content
       - Canada: 91.36% * 40% = 36.54% exemption
       - Mexico: 71.45% * 40% = 28.58% exemption
    """
    origin = product_info['origin_country']
    result = {
        'excluded': False,
        'exemption_code': None,
        'reasoning': '',
        'final_amount': tariff['amount']
    }

    # Auto rebate parameters from Yale
    AUTO_REBATE_RATE = 0.0375      # 3.75%
    US_ASSEMBLY_SHARE = 0.33       # 33%
    US_AUTO_CONTENT_SHARE = 0.40   # 40%

    # USMCA shares for automotive (from Yale usmca_shares.csv)
    USMCA_SHARES = {
        'CA': 0.9136,  # 91.36%
        'MX': 0.7145   # 71.45%
    }

    # Calculate auto rebate (applies to all automotive)
    rebate = AUTO_REBATE_RATE * US_ASSEMBLY_SHARE  # 0.012375 (1.2375 percentage points)
    effective_rate = tariff['rate'] - rebate  # 0.25 - 0.012375 = 0.237625

    # CA/MX USMCA logic with adjusted share
    if origin in ['CA', 'MX']:
        usmca_qualified = answers.get('usmca_qualified', False)
        if usmca_qualified:
            # Adjusted USMCA share for automotive = usmca_share * US content (40%)
            usmca_share = USMCA_SHARES.get(origin, 0)
            adjusted_usmca_share = usmca_share * US_AUTO_CONTENT_SHARE

            # Apply exemption: rate * (1 - adjusted_share)
            final_rate_after_exemption = effective_rate * (1 - adjusted_usmca_share)
            final_amount = product_info['value'] * final_rate_after_exemption

            result['excluded'] = True  # Partially exempt
            result['exemption_code'] = '9903.01.26' if origin == 'CA' else '9903.01.27'
            result['reasoning'] = (
                f'PARTIALLY EXEMPT: USMCA-qualified automotive from {origin}. '
                f'Base rate 25% - auto rebate 1.24% = 23.76%. '
                f'USMCA adjusted exemption {adjusted_usmca_share*100:.2f}% '
                f'({usmca_share*100:.2f}% share × 40% US content). '
                f'Final effective rate: {final_rate_after_exemption*100:.2f}%'
            )
            result['final_amount'] = final_amount
            return result
        else:
            # USMCA not qualified - apply rebated rate
            final_amount = product_info['value'] * effective_rate
            result['reasoning'] = (
                f'APPLIES: Automotive from {origin} (not USMCA-qualified). '
                f'Rate: 25% - auto rebate 1.24% = {effective_rate*100:.4f}%'
            )
            result['final_amount'] = final_amount
            return result
    else:
        # Other origins - apply rebated rate only
        final_amount = product_info['value'] * effective_rate
        result['reasoning'] = (
            f'APPLIES: Automotive tariff with US assembly rebate. '
            f'Rate: 25% - 1.24% = {effective_rate*100:.4f}%'
        )
        result['final_amount'] = final_amount
        return result


def apply_section_301_logic(tariff, answers, product_info):
    """
    Apply Section 301 decision tree logic.
    """
    result = {
        'excluded': False,
        'exemption_code': None,
        'reasoning': '',
        'final_amount': tariff['amount']
    }

    # Only applies to CN/HK/MO
    origin = product_info['origin_country']
    if origin not in ['CN', 'HK', 'MO']:
        result['excluded'] = True
        result['exemption_code'] = 'N/A'
        result['reasoning'] = f'NOT APPLICABLE: Product not from China/Hong Kong/Macau (origin: {origin})'
        result['final_amount'] = 0
        return result

    # Check USTR product exclusion
    ustr_exclusion = answers.get('ustr_product_exclusion', False)
    if ustr_exclusion:
        result['excluded'] = True
        result['exemption_code'] = '9903.88.69'
        result['reasoning'] = 'EXEMPT: Product matches one of 164 USTR product-specific exclusions'
        result['final_amount'] = 0
        return result

    # Check manufacturing equipment exclusion
    manufacturing_equipment = answers.get('ustr_manufacturing_equipment', False)
    if manufacturing_equipment:
        result['excluded'] = True
        result['exemption_code'] = '9903.88.70'
        result['reasoning'] = 'EXEMPT: Product classified as manufacturing equipment'
        result['final_amount'] = 0
        return result

    # No exemptions apply
    result['reasoning'] = f'APPLIES: Product from {origin}, no USTR exclusions apply'
    return result


def apply_ieepa_reciprocal_logic(tariff, answers, product_info, section_232_results=None):
    """
    Apply IEEPA Reciprocal decision tree logic.
    CRITICAL: Applies only to NON-232 portion of product value.

    Args:
        section_232_results: Dict of {material: analysis_result} from Section 232 evaluation
                            Used to determine what percentage is exempt per 9903.01.33
    """
    result = {
        'excluded': False,
        'exemption_code': None,
        'reasoning': '',
        'final_amount': tariff['amount']
    }

    if section_232_results is None:
        section_232_results = {}

    # Check Column 2 rate countries exemption (9903.01.29)
    # Belarus, Cuba, North Korea, Russia
    origin = product_info['origin_country']
    column_2_countries = ['BY', 'CU', 'KP', 'RU']
    if origin in column_2_countries:
        result['excluded'] = True
        result['exemption_code'] = '9903.01.29'
        result['reasoning'] = f'EXEMPT: Product from Column 2 rate country ({origin})'
        result['final_amount'] = 0
        return result

    # Check humanitarian donations exemption (9903.01.30)
    is_humanitarian = answers.get('is_humanitarian_donation', False)
    if is_humanitarian:
        result['excluded'] = True
        result['exemption_code'] = '9903.01.30'
        result['reasoning'] = 'EXEMPT: Humanitarian donation (food, clothing, medicine)'
        result['final_amount'] = 0
        return result

    # EU, Japan, South Korea Special Calculation (15% threshold rule)
    # Per CSMS #65829726 and trade agreements:
    # - If Column 1 (MFN) rate >= 15%: reciprocal rate = 0%
    # - If Column 1 (MFN) rate < 15%: reciprocal rate = 15% - Column 1 rate
    # This ensures total duty = max(Column 1 rate, 15%)

    eu_countries = ['AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR',
                    'DE', 'GR', 'HU', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL',
                    'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE']

    special_calculation_countries = eu_countries + ['JP', 'KR']

    if origin in special_calculation_countries:
        # Get Column 1 (MFN) duty rate from answers
        column_1_rate = answers.get('column_1_duty_rate', None)

        if column_1_rate is None:
            # Column 1 rate not provided - cannot calculate adjusted reciprocal rate
            result['excluded'] = False
            result['exemption_code'] = None
            result['reasoning'] = (
                f'REQUIRES DATA: Product from {origin} requires Column 1 (MFN) duty rate '
                f'to calculate adjusted reciprocal tariff. '
                f'Rule: If MFN ≥15% then reciprocal=0%; if MFN <15% then reciprocal=15%-MFN. '
                f'Please provide the Column 1 duty rate for this HTS code.'
            )
            result['final_amount'] = 0
            logger.warning(f"Column 1 rate required for {origin} but not provided")
            return result

        # Calculate adjusted reciprocal rate based on 15% threshold
        if column_1_rate >= 15:
            # Column 1 rate already meets or exceeds 15%, so NO reciprocal tariff
            result['excluded'] = True
            result['exemption_code'] = 'N/A'
            result['reasoning'] = (
                f'EXEMPT: {origin} product with Column 1 (MFN) rate of {column_1_rate:.2f}% '
                f'(≥15% threshold). No reciprocal tariff applied. '
                f'Total duty = {column_1_rate:.2f}% (Column 1 only)'
            )
            result['final_amount'] = 0
            return result
        else:
            # Column 1 rate < 15%, apply adjusted reciprocal rate
            adjusted_reciprocal_rate = (15 - column_1_rate) / 100.0  # Convert to decimal

            # Apply to non-232 portion only
            final_amount = product_info['value'] * (non_232_pct / 100.0) * adjusted_reciprocal_rate

            result['reasoning'] = (
                f'APPLIES (ADJUSTED): {origin} product with Column 1 (MFN) rate {column_1_rate:.2f}%. '
                f'Adjusted reciprocal rate = 15% - {column_1_rate:.2f}% = {adjusted_reciprocal_rate*100:.2f}%. '
                f'Applied to {non_232_pct:.1f}% non-232 portion. '
                f'Total duty = {column_1_rate:.2f}% (Column 1) + {adjusted_reciprocal_rate*100:.2f}% (Reciprocal) = 15%'
            )
            result['final_amount'] = final_amount
            return result

    # Only applies to CN/HK/MO at 10% (and other countries per bulletin)
    # Note: Per bulletin, China continues at 10% under 9903.01.25

    # Calculate total Section 232-covered materials percentage
    # Based on CBP guidance: Section 232 and IEEPA Reciprocal are MUTUALLY EXCLUSIVE
    # Section 232 applies to: steel, aluminum, copper, lumber (and automotive, buses)
    # IEEPA Reciprocal applies ONLY to the non-232 portion (exemption 9903.01.33)
    #
    # CRITICAL: We use Section 232 results from earlier evaluation, NOT just material percentages
    # This ensures we only exempt what ACTUALLY got Section 232 tariffs applied
    # (e.g., automotive products don't get material-based 232, so they don't get 9903.01.33 exemption)

    steel_pct = 0
    aluminum_pct = 0
    copper_pct = 0
    lumber_pct = 0

    # Check which Section 232 tariffs actually applied (not excluded)
    if 'steel' in section_232_results and not section_232_results['steel'].get('excluded', False):
        steel_pct = answers.get('steel_percentage', 0)

    if 'aluminum' in section_232_results and not section_232_results['aluminum'].get('excluded', False):
        aluminum_pct = answers.get('aluminum_percentage', 0)

    if 'copper' in section_232_results and not section_232_results['copper'].get('excluded', False):
        copper_pct = answers.get('copper_percentage', 0)

    if 'lumber' in section_232_results and not section_232_results['lumber'].get('excluded', False):
        lumber_pct = answers.get('lumber_percentage', 0)

    total_232_material_pct = steel_pct + aluminum_pct + copper_pct + lumber_pct

    # Validation: Total material percentages cannot exceed 100%
    if total_232_material_pct > 100:
        result['excluded'] = False
        result['exemption_code'] = None
        result['reasoning'] = (
            f'ERROR: Total Section 232 material percentages exceed 100%. '
            f'Steel: {steel_pct}%, Aluminum: {aluminum_pct}%, '
            f'Copper: {copper_pct}%, Lumber: {lumber_pct}%. '
            f'Total: {total_232_material_pct}%. Please verify composition percentages.'
        )
        result['final_amount'] = 0
        logger.error(f"Material percentage validation failed: {total_232_material_pct}% > 100%")
        return result

    non_232_pct = 100 - total_232_material_pct

    if non_232_pct <= 0:
        result['excluded'] = True
        result['exemption_code'] = '9903.01.33'
        result['reasoning'] = 'EXEMPT: Product is 100% Section 232 materials (exemption 9903.01.33 - metal portion exempt)'
        result['final_amount'] = 0
        return result

    # Check US content exemption
    us_content = answers.get('us_content_percentage', 0)

    # Validation: US content percentage should be reasonable
    if us_content > 100:
        result['excluded'] = False
        result['exemption_code'] = None
        result['reasoning'] = (
            f'ERROR: US content percentage ({us_content}%) cannot exceed 100%. '
            f'Please verify the US content value.'
        )
        result['final_amount'] = 0
        logger.error(f"US content validation failed: {us_content}% > 100%")
        return result

    if us_content > 20:
        result['excluded'] = True
        result['exemption_code'] = '9903.01.34'
        result['reasoning'] = f'EXEMPT: Product has {us_content:.1f}% U.S. content (>20% threshold)'
        result['final_amount'] = 0
        return result

    # Check informational materials exemption
    is_informational = answers.get('is_informational_materials', False)
    if is_informational:
        result['excluded'] = True
        result['exemption_code'] = '9903.01.21'
        result['reasoning'] = 'EXEMPT: Product is informational materials (books, films, CDs, artwork)'
        result['final_amount'] = 0
        return result

    # Apply to non-Section 232 portion only (mutual exclusivity)
    final_amount = product_info['value'] * (non_232_pct / 100.0) * tariff['rate']
    result['reasoning'] = f'APPLIES to NON-232 portion only: {non_232_pct:.1f}% of product value (Section 232 materials {total_232_material_pct:.1f}% are mutually exclusive per exemption 9903.01.33)'
    result['final_amount'] = final_amount

    return result


def apply_ieepa_fentanyl_logic(tariff, answers, product_info):
    """
    Apply IEEPA Fentanyl decision tree logic.
    CRITICAL: Always applies to 100% of product value, NO exemptions.
    """
    result = {
        'excluded': False,
        'exemption_code': None,
        'reasoning': '',
        'final_amount': tariff['amount']
    }

    # Only applies to CN/HK/MO
    origin = product_info['origin_country']
    if origin not in ['CN', 'HK', 'MO']:
        result['excluded'] = True
        result['exemption_code'] = 'N/A'
        result['reasoning'] = f'NOT APPLICABLE: Product not from China/Hong Kong/Macau (origin: {origin})'
        result['final_amount'] = 0
        return result

    # No exemptions - always applies
    result['reasoning'] = f'APPLIES: IEEPA Fentanyl tariff on 100% of product value (no exemptions available)'
    return result


def analyze_stacking(tariffs, answers, product_info):
    """
    Main orchestration function for stacking analysis.

    Args:
        tariffs: List of detected punitive tariffs
        answers: Dict of {question_id: answer_value}
        product_info: Dict with origin_country, hs_code, value

    Returns:
        List of analyzed tariffs in CBP stacking order with reasoning
    """
    results = []

    # CRITICAL: Track if HTS code-based Section 232 tariffs apply
    # If automotive or buses applies, material-based 232 tariffs are EXCLUDED
    hts_based_232_applies = False

    # CRITICAL: Track which Section 232 tariffs actually applied (not excluded)
    # This is needed for IEEPA Reciprocal exemption 9903.01.33 calculation
    section_232_results = {}  # {category: analysis_result}

    # Sort tariffs by CBP stacking order
    sorted_tariffs = sorted(
        tariffs,
        key=lambda t: STACKING_ORDER.get(t['category'], 999)
    )

    for tariff in sorted_tariffs:
        category = tariff['category']

        logger.info(f"Analyzing {category}: {tariff['name']}")

        # Apply category-specific logic
        if category == 'section_232_automotive':
            analysis = apply_section_232_automotive_logic(tariff, answers, product_info)
            # If automotive tariff applies (not excluded), mark HTS-based 232 as active
            if not analysis.get('excluded', False):
                hts_based_232_applies = True
                logger.info("  → Automotive Section 232 applies - material-based 232 tariffs will be excluded")

        elif category == 'section_232_buses':
            analysis = apply_section_232_buses_logic(tariff, answers, product_info)
            # If buses tariff applies (not excluded), mark HTS-based 232 as active
            if not analysis.get('excluded', False):
                hts_based_232_applies = True
                logger.info("  → Buses Section 232 applies - material-based 232 tariffs will be excluded")

        elif category == 'section_232_steel':
            # MUTUAL EXCLUSIVITY: If automotive/buses applies, skip material-based tariffs
            if hts_based_232_applies:
                analysis = {
                    'excluded': True,
                    'exemption_code': 'N/A',
                    'reasoning': 'NOT APPLICABLE: Product already covered under Section 232 Automotive/Buses HTS code classification. Material composition tariffs do not apply when HTS-based 232 tariff applies.',
                    'final_amount': 0
                }
                logger.info("  → EXCLUDED due to HTS-based Section 232 priority")
            else:
                analysis = apply_section_232_steel_logic(tariff, answers, product_info)
                section_232_results['steel'] = analysis

        elif category == 'section_232_aluminum':
            # MUTUAL EXCLUSIVITY: If automotive/buses applies, skip material-based tariffs
            if hts_based_232_applies:
                analysis = {
                    'excluded': True,
                    'exemption_code': 'N/A',
                    'reasoning': 'NOT APPLICABLE: Product already covered under Section 232 Automotive/Buses HTS code classification. Material composition tariffs do not apply when HTS-based 232 tariff applies.',
                    'final_amount': 0
                }
                logger.info("  → EXCLUDED due to HTS-based Section 232 priority")
            else:
                analysis = apply_section_232_aluminum_logic(tariff, answers, product_info)
                section_232_results['aluminum'] = analysis

        elif category == 'section_232_copper':
            # MUTUAL EXCLUSIVITY: If automotive/buses applies, skip material-based tariffs
            if hts_based_232_applies:
                analysis = {
                    'excluded': True,
                    'exemption_code': 'N/A',
                    'reasoning': 'NOT APPLICABLE: Product already covered under Section 232 Automotive/Buses HTS code classification. Material composition tariffs do not apply when HTS-based 232 tariff applies.',
                    'final_amount': 0
                }
                logger.info("  → EXCLUDED due to HTS-based Section 232 priority")
            else:
                analysis = apply_section_232_copper_logic(tariff, answers, product_info)
                section_232_results['copper'] = analysis

        elif category == 'section_232_lumber':
            # MUTUAL EXCLUSIVITY: If automotive/buses applies, skip material-based tariffs
            if hts_based_232_applies:
                analysis = {
                    'excluded': True,
                    'exemption_code': 'N/A',
                    'reasoning': 'NOT APPLICABLE: Product already covered under Section 232 Automotive/Buses HTS code classification. Material composition tariffs do not apply when HTS-based 232 tariff applies.',
                    'final_amount': 0
                }
                logger.info("  → EXCLUDED due to HTS-based Section 232 priority")
            else:
                analysis = apply_section_232_lumber_logic(tariff, answers, product_info)
                section_232_results['lumber'] = analysis

        elif category == 'section_301':
            analysis = apply_section_301_logic(tariff, answers, product_info)

        elif category == 'ieepa_reciprocal':
            # Pass Section 232 results for exemption 9903.01.33 calculation
            analysis = apply_ieepa_reciprocal_logic(tariff, answers, product_info, section_232_results)

        elif category == 'ieepa_fentanyl':
            analysis = apply_ieepa_fentanyl_logic(tariff, answers, product_info)

        else:
            # Unknown category - apply as-is
            analysis = {
                'excluded': False,
                'exemption_code': None,
                'reasoning': f'APPLIES: {tariff["name"]} (category: {category})',
                'final_amount': tariff['amount']
            }

        # Combine tariff info with analysis
        result = {
            **tariff,  # code, name, rate, amount, category, description
            **analysis  # excluded, exemption_code, reasoning, final_amount
        }

        results.append(result)

        logger.info(f"  Result: {analysis['reasoning']}")

    return results
