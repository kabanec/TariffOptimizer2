"""
Exemption Database - Centralized source of truth for Section 99 tariff exclusions
This database is used by both the exclusion tester and the stacking builder
"""

# Section 232 Steel Exemptions
SECTION_232_STEEL_EXEMPTIONS = [
    {
        'code': '9903.01.26',
        'name': 'USMCA Exemption: Canada Origin',
        'description': 'Goods that originate in Canada under USMCA qualify for exemption from Section 232 steel duties. Note: All General Approved Exclusions (GAEs) were revoked effective March 12, 2025.',
        'applies_to_hs_codes': ['99038104', '99038106', '99038111', '99038112', '99038119', '99038186', '99038187'],
        'effect': 'EXEMPT',
        'conditions': {
            'origin_countries': ['CA'],
            'requires_usmca': True
        },
        'source': 'USMCA general note 11 to HTSUS; CBP CSMS guidance',
        'reference': 'https://www.cbp.gov/trade/programs-administration/entry-summary/232-tariffs-aluminum-and-steel-faqs'
    },
    {
        'code': '9903.01.27',
        'name': 'USMCA Exemption: Mexico Origin',
        'description': 'Goods that originate in Mexico under USMCA qualify for exemption from Section 232 steel duties. Note: All General Approved Exclusions (GAEs) were revoked effective March 12, 2025.',
        'applies_to_hs_codes': ['99038104', '99038106', '99038111', '99038112', '99038119', '99038186', '99038187'],
        'effect': 'EXEMPT',
        'conditions': {
            'origin_countries': ['MX'],
            'requires_usmca': True
        },
        'source': 'USMCA general note 11 to HTSUS; CBP CSMS guidance',
        'reference': 'https://www.cbp.gov/trade/programs-administration/entry-summary/232-tariffs-aluminum-and-steel-faqs'
    },
    {
        'code': '9903.81.92',
        'name': 'U.S.-Origin Steel Exemption',
        'description': 'Derivative steel articles made from steel melted and poured in the United States qualify for 0% tariff rate.',
        'applies_to_hs_codes': ['99038106', '99038111', '99038112', '99038119', '99038186', '99038187'],
        'effect': 'EXEMPT',
        'conditions': {
            'us_origin': True,
            'melted_and_poured_in_us': True
        },
        'source': 'Presidential Proclamation 9980; CBP Section 232 Steel FAQs',
        'reference': 'https://www.cbp.gov/trade/programs-administration/entry-summary/232-tariffs-aluminum-and-steel-faqs'
    },
    {
        'code': 'PRODUCT_EXCLUSION_STEEL',
        'name': 'Commerce Product-Specific Exclusion',
        'description': 'Time-limited product exclusion granted by U.S. Department of Commerce (valid 1 year or until quantity exhausted). NOTE: Commerce is no longer processing new exclusion requests as of Feb 10, 2025.',
        'applies_to_hs_codes': ['99038104', '99038106', '99038111', '99038112', '99038119', '99038186', '99038187'],
        'effect': 'EXEMPT',
        'conditions': {
            'requires_exclusion_approval': True,
            'requires_ior_match': True,
            'quantity_limited': True
        },
        'source': 'CBP Active Section 232 Product Exclusions list (updated weekly)',
        'reference': 'https://www.cbp.gov/trade/programs-administration/entry-summary/section-232-exclusions'
    }
]

# Section 232 Aluminum Exemptions
SECTION_232_ALUMINUM_EXEMPTIONS = [
    {
        'code': '9903.01.26',
        'name': 'USMCA Exemption: Canada Origin',
        'description': 'Goods that originate in Canada under USMCA qualify for exemption from Section 232 aluminum duties. Note: All General Approved Exclusions (GAEs) were revoked effective March 12, 2025.',
        'applies_to_hs_codes': ['99038502', '99038504', '99038507', '99038508', '99038509'],
        'effect': 'EXEMPT',
        'conditions': {
            'origin_countries': ['CA'],
            'requires_usmca': True
        },
        'source': 'USMCA general note 11 to HTSUS; CBP CSMS guidance',
        'reference': 'https://www.cbp.gov/trade/programs-administration/entry-summary/232-tariffs-aluminum-and-steel-faqs'
    },
    {
        'code': '9903.01.27',
        'name': 'USMCA Exemption: Mexico Origin',
        'description': 'Goods that originate in Mexico under USMCA qualify for exemption from Section 232 aluminum duties. Note: All General Approved Exclusions (GAEs) were revoked effective March 12, 2025.',
        'applies_to_hs_codes': ['99038502', '99038504', '99038507', '99038508', '99038509'],
        'effect': 'EXEMPT',
        'conditions': {
            'origin_countries': ['MX'],
            'requires_usmca': True
        },
        'source': 'USMCA general note 11 to HTSUS; CBP CSMS guidance',
        'reference': 'https://www.cbp.gov/trade/programs-administration/entry-summary/232-tariffs-aluminum-and-steel-faqs'
    },
    {
        'code': 'US_ORIGIN_ALUMINUM',
        'name': 'U.S.-Origin Aluminum Exemption',
        'description': 'Derivative aluminum articles made exclusively from aluminum smelted and cast in the United States qualify for exemption from Section 232 duties.',
        'applies_to_hs_codes': ['99038504', '99038507', '99038508', '99038509'],
        'effect': 'EXEMPT',
        'conditions': {
            'us_origin': True,
            'smelted_and_cast_in_us': True
        },
        'source': 'CBP Section 232 FAQs; Presidential Proclamation',
        'reference': 'https://www.cbp.gov/trade/programs-administration/entry-summary/232-tariffs-aluminum-and-steel-faqs'
    },
    {
        'code': 'PRODUCT_EXCLUSION_AL',
        'name': 'Commerce Product-Specific Exclusion',
        'description': 'Time-limited product exclusion granted by U.S. Department of Commerce (valid 1 year or until quantity exhausted). NOTE: Commerce is no longer processing new exclusion requests as of Feb 10, 2025.',
        'applies_to_hs_codes': ['99038502', '99038504', '99038507', '99038508', '99038509'],
        'effect': 'EXEMPT',
        'conditions': {
            'requires_exclusion_approval': True,
            'requires_ior_match': True,
            'quantity_limited': True
        },
        'source': 'CBP Active Section 232 Product Exclusions list (updated weekly)',
        'reference': 'https://www.cbp.gov/trade/programs-administration/entry-summary/section-232-exclusions'
    }
]

# Section 301 China Exemptions
SECTION_301_EXEMPTIONS = [
    {
        'code': '9903.88.69',
        'name': 'USTR Product-Specific Exclusion (164 products)',
        'description': '164 product-specific exclusions covering certain industrial equipment, EVs, batteries, critical minerals, semiconductors and solar cells. Extended through November 10, 2026.',
        'applies_to_hs_codes': ['99038803', '99038804', '99038809', '99038815'],
        'effect': 'EXEMPT',
        'conditions': {
            'requires_product_match': True,
            'must_match_detailed_description': True,
            'origin_countries': ['CN', 'HK', 'MO']
        },
        'source': 'USTR Federal Register Notice; U.S. note 20(vvv) to subchapter III of chapter 99',
        'reference': 'https://www.federalregister.gov/documents/2025/09/02/2025-16733/notice-of-product-exclusion-extensions-chinas-acts-policies-and-practices-related-to-technology',
        'valid_until': '2026-11-10'
    },
    {
        'code': '9903.88.70',
        'name': 'USTR Manufacturing Equipment Exclusion (14 products)',
        'description': '14 exclusions for manufacturing equipment related to solar manufacturing and other technologies. Extended through November 10, 2026.',
        'applies_to_hs_codes': ['99038803', '99038804', '99038809', '99038815'],
        'effect': 'EXEMPT',
        'conditions': {
            'requires_product_match': True,
            'must_match_detailed_description': True,
            'manufacturing_equipment': True,
            'origin_countries': ['CN', 'HK', 'MO']
        },
        'source': 'USTR Federal Register Notice; U.S. note 20(www) to subchapter III of chapter 99',
        'reference': 'https://www.federalregister.gov/documents/2025/09/02/2025-16733/notice-of-product-exclusion-extensions-chinas-acts-policies-and-practices-related-to-technology',
        'valid_until': '2026-11-10'
    },
    {
        'code': 'SECTION_321_ELIMINATED',
        'name': 'De Minimis Exemption (Section 321) - ELIMINATED for CN/HK/MO',
        'description': 'IMPORTANT: As of September 2024, Section 321 de minimis exemption NO LONGER APPLIES to goods from China, Hong Kong, or Macau. These goods are now subject to Section 301 duties regardless of shipment value.',
        'applies_to_hs_codes': [],
        'effect': 'NO_EXEMPTION',
        'conditions': {
            'eliminated_for_china_hk_macau': True,
            'effective_date': '2024-09-01'
        },
        'source': 'CBP Section 321 Modification',
        'reference': 'https://www.cbp.gov/trade/programs-administration/entry-summary/section-321'
    }
]

# IEEPA Exemptions
IEEPA_EXEMPTIONS = [
    {
        'code': '9903.01.34',
        'name': 'U.S. Content Exemption (>20%)',
        'description': 'Products with greater than 20% U.S. content by value are exempt from IEEPA Reciprocal Tariff.',
        'applies_to_hs_codes': ['99030125'],  # IEEPA Reciprocal code
        'effect': 'EXEMPT',
        'conditions': {
            'us_content_percentage': '>20',
            'origin_countries': ['CN', 'HK', 'MO']
        },
        'source': 'Presidential Proclamation; CBP guidance',
        'reference': 'https://www.cbp.gov/trade/remedies/ieepa'
    },
    {
        'code': '9903.01.21',
        'name': 'Informational Materials Exemption',
        'description': 'Informational materials (books, films, CDs, posters, artwork) are exempt from IEEPA tariffs.',
        'applies_to_hs_codes': ['99030125', '99030136'],
        'effect': 'EXEMPT',
        'conditions': {
            'informational_materials': True,
            'origin_countries': ['CN', 'HK', 'MO']
        },
        'source': 'Presidential Proclamation; CBP guidance',
        'reference': 'https://www.cbp.gov/trade/remedies/ieepa'
    },
    {
        'code': '9903.01.33',
        'name': 'Section 232 Exempts IEEPA Reciprocal',
        'description': 'If Section 232 tariffs apply, IEEPA Reciprocal (9903.01.25) is automatically exempt.',
        'applies_to_hs_codes': ['99030125'],
        'effect': 'EXEMPT',
        'conditions': {
            'section_232_applies': True
        },
        'source': 'CBP Stacking Guidance',
        'reference': 'https://www.cbp.gov/trade/remedies/ieepa'
    }
]

# CBP Stacking Order Rules
CBP_STACKING_RULES = {
    'order': [
        'section_232_steel',
        'section_232_aluminum',
        'section_232_automotive',
        'section_301',
        'ieepa_reciprocal',
        'ieepa_fentanyl'
    ],
    'rules': [
        {
            'rule': 'Section 232 tariffs stack BEFORE Section 301',
            'priority': 1
        },
        {
            'rule': 'IEEPA Reciprocal tariffs stack AFTER Section 232 and Section 301',
            'priority': 2
        },
        {
            'rule': 'IEEPA Fentanyl tariffs stack last',
            'priority': 3
        },
        {
            'rule': 'Section 232 exempts from IEEPA Reciprocal (9903.01.33)',
            'exemption': True,
            'trigger': 'section_232_applies',
            'exempts': 'ieepa_reciprocal'
        },
        {
            'rule': 'USMCA exemptions (9903.01.26, 9903.01.27) eliminate Section 232 duties',
            'exemption': True,
            'trigger': 'usmca_qualifies',
            'exempts': 'section_232'
        },
        {
            'rule': 'U.S. content >20% (9903.01.34) eliminates IEEPA Reciprocal',
            'exemption': True,
            'trigger': 'us_content_gt_20',
            'exempts': 'ieepa_reciprocal'
        }
    ]
}


def get_exemptions_for_category(category):
    """Get all exemptions for a specific tariff category"""
    category_lower = category.lower()

    if 'section_232_steel' in category_lower or 'steel' in category_lower:
        return SECTION_232_STEEL_EXEMPTIONS
    elif 'section_232_aluminum' in category_lower or 'aluminum' in category_lower:
        return SECTION_232_ALUMINUM_EXEMPTIONS
    elif 'section_301' in category_lower:
        return SECTION_301_EXEMPTIONS
    elif 'ieepa' in category_lower:
        return IEEPA_EXEMPTIONS
    else:
        return []


def check_exemption_applies(exemption, product_info, answers):
    """
    Check if an exemption applies based on product info and user answers

    Args:
        exemption: Exemption dict from database
        product_info: Dict with hsCode, origin, value
        answers: Dict of user answers to questions

    Returns:
        bool: True if exemption applies
    """
    conditions = exemption.get('conditions', {})
    origin = product_info.get('origin', '')

    # Check origin country conditions
    if 'origin_countries' in conditions:
        allowed_origins = conditions['origin_countries']
        if origin not in allowed_origins:
            return False

    # Check USMCA qualification
    if conditions.get('requires_usmca'):
        # Look for USMCA answer in user responses
        usmca_qualified = any(
            'usmca' in str(answer).lower() and 'yes' in str(answer).lower()
            for answer in answers.values()
        )
        if not usmca_qualified:
            return False

    # Check US origin/melting conditions
    if conditions.get('melted_and_poured_in_us'):
        us_melted = any(
            ('melted' in str(answer).lower() or 'poured' in str(answer).lower() or 'origin' in str(answer).lower())
            and ('us' in str(answer).lower() or 'united states' in str(answer).lower())
            for answer in answers.values()
        )
        if not us_melted:
            return False

    # Check US content percentage
    if 'us_content_percentage' in conditions:
        required_percent = float(conditions['us_content_percentage'].replace('>', '').replace('<', ''))
        # Look for percentage in answers
        for answer in answers.values():
            if isinstance(answer, (int, float)):
                if answer > required_percent:
                    return True
            elif '%' in str(answer):
                try:
                    percent = float(str(answer).replace('%', '').strip())
                    if percent > required_percent:
                        return True
                except:
                    pass
        return False

    # If we got here, exemption applies
    return True


def analyze_stacking_with_exemptions(product_info, found_tariffs, questions, answers):
    """
    Analyze stacking order and apply exemptions using the database

    Args:
        product_info: Dict with hsCode, origin, value
        found_tariffs: List of tariff dicts with code, name, rate, amount, category
        questions: List of question dicts
        answers: Dict of answers keyed by question index

    Returns:
        Dict with stackingOrder, totalBefore, totalAfter, savings, cbpGuidance
    """
    stacking_order = []
    total_before = sum(t['amount'] for t in found_tariffs)

    # Check Section 232 applies (for IEEPA exemption rule)
    section_232_applies = any('section_232' in t['category'].lower() for t in found_tariffs)

    # Process each tariff in CBP stacking order
    for tariff in sorted(found_tariffs, key=lambda t: CBP_STACKING_RULES['order'].index(t['category']) if t['category'] in CBP_STACKING_RULES['order'] else 999):

        # Get applicable exemptions for this tariff category
        exemptions = get_exemptions_for_category(tariff['category'])

        # Check if any exemption applies
        excluded = False
        exemption_code = None
        reasoning = f"Applies: {tariff['name']}"

        # Special rule: Section 232 exempts IEEPA Reciprocal
        if 'ieepa_reciprocal' in tariff['category'].lower() and section_232_applies:
            excluded = True
            exemption_code = '9903.01.33'
            reasoning = "EXEMPT: Section 232 tariffs apply, which automatically exempts IEEPA Reciprocal (9903.01.33)"

        # Check database exemptions
        if not excluded:
            for exemption in exemptions:
                if check_exemption_applies(exemption, product_info, answers):
                    excluded = True
                    exemption_code = exemption['code']
                    reasoning = f"EXEMPT: {exemption['name']} - {exemption['description'][:100]}"
                    break

        stacking_order.append({
            'code': tariff['code'],
            'name': tariff['name'],
            'rate': tariff['rate'],
            'amount': tariff['amount'],
            'category': tariff['category'],
            'excluded': excluded,
            'exemption_code': exemption_code,
            'reasoning': reasoning
        })

    # Calculate total after exemptions
    total_after = sum(t['amount'] for t in stacking_order if not t['excluded'])
    savings = total_before - total_after

    # Generate CBP guidance summary
    cbp_guidance = f"Stacking Order: {' → '.join(CBP_STACKING_RULES['order'][:len(found_tariffs)])}. "
    cbp_guidance += f"Applied {len([t for t in stacking_order if t['excluded']])} exemptions. "
    if section_232_applies:
        cbp_guidance += "Section 232 exempts IEEPA Reciprocal per 9903.01.33. "

    return {
        'stackingOrder': stacking_order,
        'totalBefore': total_before,
        'totalAfter': total_after,
        'savings': savings,
        'cbpGuidance': cbp_guidance
    }
