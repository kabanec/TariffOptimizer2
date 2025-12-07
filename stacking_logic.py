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
STACKING_ORDER = {
    'section_232_steel': 1,
    'section_232_aluminum': 2,
    'section_232_automotive': 3,
    'section_301': 4,
    'ieepa_reciprocal': 5,
    'ieepa_fentanyl': 6
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

    # IEEPA Reciprocal Questions (only for China/Hong Kong/Macau)
    if 'ieepa_reciprocal' in categories and origin_country in ['CN', 'HK', 'MO']:
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


def apply_ieepa_reciprocal_logic(tariff, answers, product_info):
    """
    Apply IEEPA Reciprocal decision tree logic.
    CRITICAL: Applies only to NON-METAL portion of product value.
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

    # Calculate total metal percentage
    steel_pct = answers.get('steel_percentage', 0)
    aluminum_pct = answers.get('aluminum_percentage', 0)
    copper_pct = answers.get('copper_percentage', 0)
    lumber_pct = answers.get('lumber_percentage', 0)

    total_metal_pct = steel_pct + aluminum_pct + copper_pct + lumber_pct
    non_metal_pct = 100 - total_metal_pct

    if non_metal_pct <= 0:
        result['excluded'] = True
        result['exemption_code'] = 'N/A'
        result['reasoning'] = 'NOT APPLICABLE: Product is 100% metal (covered by Section 232)'
        result['final_amount'] = 0
        return result

    # Check US content exemption
    us_content = answers.get('us_content_percentage', 0)
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

    # Apply to non-metal portion only
    final_amount = product_info['value'] * (non_metal_pct / 100.0) * tariff['rate']
    result['reasoning'] = f'APPLIES to NON-METAL portion only: {non_metal_pct:.1f}% of product value (metal portion {total_metal_pct:.1f}% is subject to Section 232)'
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

    # Sort tariffs by CBP stacking order
    sorted_tariffs = sorted(
        tariffs,
        key=lambda t: STACKING_ORDER.get(t['category'], 999)
    )

    for tariff in sorted_tariffs:
        category = tariff['category']

        logger.info(f"Analyzing {category}: {tariff['name']}")

        # Apply category-specific logic
        if category == 'section_232_steel':
            analysis = apply_section_232_steel_logic(tariff, answers, product_info)

        elif category == 'section_232_aluminum':
            analysis = apply_section_232_aluminum_logic(tariff, answers, product_info)

        elif category == 'section_301':
            analysis = apply_section_301_logic(tariff, answers, product_info)

        elif category == 'ieepa_reciprocal':
            analysis = apply_ieepa_reciprocal_logic(tariff, answers, product_info)

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
