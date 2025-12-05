from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response
from flask_cors import CORS
from functools import wraps
import os
import json
import logging
import requests
import secrets
import uuid
from datetime import timedelta, datetime
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)
CORS(app)

# Load API keys and credentials
# For AvaTax Global Compliance API (matching sample code)
AVALARA_USERNAME = os.getenv('AVALARA_USERNAME')
AVALARA_PASSWORD = os.getenv('AVALARA_PASSWORD')
AVALARA_COMPANY_ID = os.getenv('AVALARA_COMPANY_ID', '2000099295')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AUTH_USER = os.getenv('AUTH_USER', 'Admin')
AUTH_PASS = os.getenv('AUTH_PASS', 'Secret_6681940')

# Debug logging for credentials (without exposing sensitive data)
logger.info(f"AVALARA_USERNAME loaded: {bool(AVALARA_USERNAME)}")
logger.info(f"AVALARA_PASSWORD loaded: {bool(AVALARA_PASSWORD)}")
logger.info(f"AVALARA_COMPANY_ID: {AVALARA_COMPANY_ID}")

# Initialize OpenAI client lazily
_openai_client = None

def get_openai_client():
    """Get or create OpenAI client instance"""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=OPENAI_API_KEY)
    return _openai_client

# AvaTax endpoints - Quotes API for duty calculations
AVATAX_ENDPOINTS = {
    'sandbox': f'https://quoting-sbx.xbo.avalara.com/api/v2/companies/{AVALARA_COMPANY_ID}/quotes/create',
    'production': f'https://quoting.xbo.avalara.com/api/v2/companies/{AVALARA_COMPANY_ID}/quotes/create'
}

# Learnings storage
LEARNINGS_FILE = Path('learnings.json')
MAX_LEARNINGS = 30

# Knowledge base paths
KB_PATH = Path('knowledge_base')
KB_DE_MINIMIS = KB_PATH / 'de_minimis_values.json'
KB_EXECUTIVE_ORDERS = KB_PATH / 'executive_orders.json'
KB_DUTY_RULES = KB_PATH / 'duty_rules.json'
KB_TARIFF_RANGES = KB_PATH / 'tariff_ranges.json'
KB_TARIFF_2025 = KB_PATH / 'recent_tariff_updates.json'

# Cache for knowledge base data
_kb_cache = {}


# HTTP Basic Auth decorator (for API endpoints)
def auth_required(f):
    """HTTP Basic Authentication decorator for API endpoints"""
    @wraps(f)
    def decorated(*args, **kwargs):
        request_id = str(uuid.uuid4())
        auth = request.authorization
        logger.debug(f"[{request_id}] Authorization header: {auth}")
        if not auth:
            logger.error(f"[{request_id}] No authorization header provided")
            return Response('Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
        if auth.username != AUTH_USER or auth.password != AUTH_PASS:
            logger.error(f"[{request_id}] Invalid credentials: username={auth.username}")
            return Response('Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
        logger.debug(f"[{request_id}] Authentication successful")
        return f(*args, **kwargs)
    return decorated


# Session-based auth decorator (for web pages)
def login_required(f):
    """Session-based authentication decorator for web pages"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def check_auth(username, password):
    """Check username and password"""
    return username == AUTH_USER and password == AUTH_PASS


def load_kb_file(file_path):
    """Load knowledge base file with caching"""
    if file_path in _kb_cache:
        return _kb_cache[file_path]

    try:
        if Path(file_path).exists():
            with open(file_path, 'r') as f:
                data = json.load(f)
                _kb_cache[file_path] = data
                return data
    except Exception as e:
        logger.error(f"Error loading KB file {file_path}: {e}")
    return None


def load_learnings():
    """Load learnings from file"""
    try:
        if LEARNINGS_FILE.exists():
            with open(LEARNINGS_FILE, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Error loading learnings: {e}")
        return []


def save_learnings(learnings):
    """Save learnings to file"""
    try:
        learnings = learnings[-MAX_LEARNINGS:]
        with open(LEARNINGS_FILE, 'w') as f:
            json.dump(learnings, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving learnings: {e}")


def extract_transaction_context(user_request, api_response):
    """Extract key context from transaction for RAG lookup"""
    context = {
        'countries': set(),
        'hs_codes': set(),
        'amount': 0,
        'origin_country': None,
        'destination_country': None,
        'incoterm': None
    }

    addresses = user_request.get('addresses', {})
    if 'ShipFrom' in addresses or 'shipFrom' in addresses:
        ship_from = addresses.get('ShipFrom', addresses.get('shipFrom', {}))
        origin = ship_from.get('country', '').upper()
        if origin:
            context['origin_country'] = origin
            context['countries'].add(origin)

    if 'ShipTo' in addresses or 'shipTo' in addresses:
        ship_to = addresses.get('ShipTo', addresses.get('shipTo', {}))
        dest = ship_to.get('country', '').upper()
        if dest:
            context['destination_country'] = dest
            context['countries'].add(dest)

    lines = user_request.get('lines', [])
    for line in lines:
        hs_code = line.get('hsCode')
        if hs_code:
            context['hs_codes'].add(hs_code[:2])
        amount = line.get('amount', 0)
        context['amount'] += amount

    delivery_terms = user_request.get('deliveryTerms')
    if delivery_terms:
        context['incoterm'] = delivery_terms

    return context


def build_rag_context(transaction_context, issue_description):
    """Build compact knowledge base context for the AI"""
    context_parts = []

    de_minimis = load_kb_file(KB_DE_MINIMIS)
    exec_orders = load_kb_file(KB_EXECUTIVE_ORDERS)
    duty_rules = load_kb_file(KB_DUTY_RULES)
    tariff_ranges = load_kb_file(KB_TARIFF_RANGES)
    recent_updates = load_kb_file(KB_TARIFF_2025)

    if recent_updates:
        eo_14324 = recent_updates.get('executive_orders', {}).get('eo_14324', {})
        if eo_14324:
            context_parts.append(f"**CRITICAL**: De Minimis ELIMINATED globally {eo_14324.get('effective_date')}. ALL shipments now dutiable.")

    if recent_updates and transaction_context['origin_country']:
        recip_eo = recent_updates.get('executive_orders', {}).get('reciprocal_tariffs_2025', {})
        if recip_eo:
            origin = transaction_context['origin_country']
            country_rates = recip_eo.get('country_specific_rates', {}).get('rates_by_country', {})
            reciprocal_rate = country_rates.get(origin, country_rates.get('Most other countries', '15%'))
            context_parts.append(f"**Reciprocal IEEPA Tariff ({origin})**: +{reciprocal_rate} ON TOP OF MFN/Section 301/Section 232.")

    if not context_parts:
        return ""

    return "\n\n**KNOWLEDGE BASE CONTEXT**:\n" + "\n".join(context_parts)


def get_enhanced_system_prompt():
    """Build system prompt enhanced with learnings"""
    base_prompt = """You are an expert AvaTax cross-border tax analyst. Be BRIEF and TECHNICAL - no fluff.

Your role:
- Analyze AvaTax API responses
- Identify duty/tax calculation issues
- Explain discrepancies
- Provide actionable insights on HS codes, rates, duty stacking

Focus: Duties, taxes, HS codes, tax codes, rates, summary details, country rules.

**Response format**: Use short sections with bullet points. Be direct and concise."""

    learnings = load_learnings()
    if learnings:
        recent_learnings = learnings[-10:]
        learnings_text = "\n\n**PAST LEARNINGS**:\n"
        for idx, learning in enumerate(recent_learnings, 1):
            learnings_text += f"{idx}. {learning['learning']}\n"
        base_prompt += learnings_text

    return base_prompt


def call_avatax_api(environment, hs_code, origin_country, destination_country, shipment_value, mode_of_transport):
    """Call AvaTax Global Compliance API for landed cost calculation"""
    try:
        import base64

        endpoint = AVATAX_ENDPOINTS.get(environment)
        if not endpoint:
            return {'error': 'Invalid environment specified'}

        if not AVALARA_USERNAME or not AVALARA_PASSWORD:
            return {'error': 'Avalara credentials not configured'}

        # Normalize HS code - remove dots and limit to 8 digits
        # Convert "3305.10.00.00" to "33051000"
        hs_code_normalized = hs_code.replace('.', '').replace('-', '')[:8]

        logger.info(f"Calling AvaTax Global Compliance API - Environment: {environment}")
        logger.info(f"Endpoint: {endpoint}")
        logger.info(f"HS Code: {hs_code} (normalized: {hs_code_normalized}), Origin: {origin_country}, Destination: {destination_country}")

        # Build Quotes API request (matching quotes/create format)
        payload = {
            "id": "tariff-lookup",
            "companyId": int(AVALARA_COMPANY_ID),
            "sellerCode": "TARIFF_LOOKUP",
            "currency": "USD",
            "shipTo": {
                "country": destination_country,
                "region": "CA" if destination_country == "US" else ""
            },
            "shipmentType": "postal",
            "type": "QUOTE_MEDIAN",
            "lines": [
                {
                    "lineNumber": "1",
                    "quantity": 1,
                    "item": {
                        "itemCode": "1",
                        "description": f"HS Code {hs_code}",
                        "summary": "",
                        "itemGroup": "General",
                        "classificationParameters": [
                            {
                                "name": "coo",
                                "value": origin_country
                            },
                            {
                                "name": "hs_code",
                                "value": hs_code_normalized
                            },
                            {
                                "name": "weight",
                                "value": "1.0",
                                "unit": "kg"
                            }
                        ],
                        "parameters": []
                    },
                    "preferenceProgramApplicable": False,
                    "classificationParameters": [
                        {
                            "name": "price",
                            "value": str(round(shipment_value, 2)),
                            "unit": "USD"
                        }
                    ]
                }
            ],
            "parameters": [
                {
                    "name": "shipping",
                    "value": "20.00",
                    "unit": "USD"
                },
                {
                    "name": "SPECIAL_CALC1",
                    "value": "TAX_DUTY_INCLUDED"
                }
            ],
            "taxRegistered": False,
            "b2b": True
        }

        logger.info(f"Request payload: {json.dumps(payload, indent=2)}")

        # Use Basic Authentication
        credentials = base64.b64encode(f"{AVALARA_USERNAME}:{AVALARA_PASSWORD}".encode()).decode()
        headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        logger.info(f"Authorization header present: {bool(headers.get('Authorization'))}")
        logger.info(f"Credentials length: {len(credentials) if credentials else 0}")

        response = requests.post(endpoint, headers=headers, json=payload, timeout=30)

        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {response.text[:2000]}")

        if response.status_code in [200, 201]:
            return response.json()
        else:
            try:
                error_data = response.json()
                return {
                    'error': f'AvaTax API error: {response.status_code}',
                    'details': response.text,
                    'status_code': response.status_code,
                    'full_response': error_data
                }
            except:
                return {
                    'error': f'AvaTax API error: {response.status_code}',
                    'details': response.text,
                    'status_code': response.status_code
                }

    except requests.exceptions.RequestException as e:
        logger.error(f"API request exception: {str(e)}")
        return {'error': f'API request failed: {str(e)}'}


def get_ai_analysis(user_request, api_response, user_response, issue_description, comparison, chat_history, transaction_context):
    """Get AI analysis using OpenAI with RAG context"""
    try:
        system_prompt = get_enhanced_system_prompt()
        rag_context = build_rag_context(transaction_context, issue_description)

        user_prompt = f"""**Issue**: {issue_description}

**Transaction**: {transaction_context['origin_country'] or '?'} → {transaction_context['destination_country'] or '?'}, ${transaction_context['amount']:.2f}

**API Response Summary**:
- Total Tax: ${api_response.get('totalTax', 0):.2f}
- Total Amount: ${api_response.get('totalAmount', 0):.2f}
- Lines: {len(api_response.get('lines', []))}
"""

        if rag_context:
            user_prompt += f"\n{rag_context}"

        user_prompt += """

**Provide**:
1. **Root Cause** (1-2 sentences)
2. **Key Findings** (bullet points)
3. **Action** (what to do)

Be BRIEF."""

        messages = [{"role": "system", "content": system_prompt}]
        if chat_history:
            messages.extend(chat_history[-4:])
        messages.append({"role": "user", "content": user_prompt})

        response = get_openai_client().chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=800,
            temperature=0.5
        )

        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"Error getting AI analysis: {str(e)}")
        return f"Error getting AI analysis: {str(e)}"


# ============ ROUTES ============

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if check_auth(username, password):
            session['authenticated'] = True
            session['username'] = username
            logger.info(f"User {username} logged in successfully")
            return redirect(url_for('index'))
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout and clear session"""
    username = session.get('username', 'Unknown')
    session.clear()
    logger.info(f"User {username} logged out")
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    """Main landing page - protected by authentication"""
    return render_template('index.html', username=session.get('username'))


@app.route('/health')
def health():
    """Health check endpoint for monitoring"""
    return jsonify({'status': 'healthy'}), 200


@app.route('/api/verify', methods=['POST'])
@auth_required
def verify_transaction():
    """Main endpoint to verify AvaTax transaction"""
    try:
        data = request.json
        environment = data.get('environment', 'sandbox').lower()
        user_request = data.get('userRequest')
        user_response = data.get('userResponse')
        issue_description = data.get('issueDescription', '')
        bearer_token = data.get('bearerToken') or AVATAX_BEARER_TOKEN

        if not user_request:
            return jsonify({'error': 'User request is required'}), 400

        if not bearer_token:
            return jsonify({'error': 'AvaTax bearer token is required'}), 400

        if isinstance(user_request, str):
            try:
                user_request = json.loads(user_request)
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid JSON in user request'}), 400

        if isinstance(user_request, list) and len(user_request) > 0:
            user_request = user_request[0]

        # Call AvaTax API
        api_response = call_avatax_api(environment, user_request, bearer_token)

        if 'error' in api_response:
            return jsonify({'error': api_response['error']}), 500

        # Initialize chat history
        if 'chat_history' not in session:
            session['chat_history'] = []

        # Extract transaction context for RAG
        transaction_context = extract_transaction_context(user_request, api_response)

        # Get AI analysis
        ai_analysis = get_ai_analysis(
            user_request=user_request,
            api_response=api_response,
            user_response=user_response,
            issue_description=issue_description,
            comparison=None,
            chat_history=session['chat_history'],
            transaction_context=transaction_context
        )

        # Store in chat history
        session['chat_history'].append({
            'role': 'user',
            'content': f"Issue: {issue_description}\nRequest: {json.dumps(user_request, indent=2)}"
        })
        session['chat_history'].append({
            'role': 'assistant',
            'content': ai_analysis
        })
        session.modified = True

        return jsonify({
            'apiResponse': api_response,
            'aiAnalysis': ai_analysis,
            'success': True
        })

    except Exception as e:
        logger.error(f"ERROR in verify_transaction: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/clear-session', methods=['POST'])
@auth_required
def clear_session():
    """Clear the chat history"""
    session.clear()
    return jsonify({'success': True})


@app.route('/tariff-lookup')
@login_required
def tariff_lookup():
    """Tariff lookup page"""
    return render_template('tariff_lookup.html', username=session.get('username'))


@app.route('/api/tariff-lookup', methods=['POST'])
def api_tariff_lookup():
    """API endpoint for tariff lookup - no auth required for easier testing"""
    try:
        data = request.json

        hs_code = data.get('hsCode')
        origin_country = data.get('originCountry')
        destination_country = data.get('destinationCountry')
        entry_date = data.get('entryDate')
        shipment_value = float(data.get('shipmentValue', 0))
        mode_of_transport = data.get('modeOfTransport', 'AIR')
        environment = data.get('environment', 'sandbox')

        if not all([hs_code, origin_country, destination_country, entry_date]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Call AvaTax Global Compliance API
        api_response = call_avatax_api(environment, hs_code, origin_country, destination_country, shipment_value, mode_of_transport)

        if 'error' in api_response:
            logger.error(f"AvaTax API Error: {api_response}")
            return jsonify({
                'error': api_response.get('error'),
                'details': api_response.get('details'),
                'status_code': api_response.get('status_code'),
                'full_response': api_response.get('full_response')
            }), api_response.get('status_code', 500)

        # Parse Global Compliance API response
        duty_breakdown = []
        punitive_tariffs = []

        try:
            # Extract line data from Global Compliance API response
            lines = api_response.get('globalCompliance', [{}])[0].get('quote', {}).get('lines', [])

            if lines:
                line = lines[0]
                duty_calc = line.get("calculationSummary", {}).get("dutyCalculationSummary", [])
                cost_lines = line.get("costLines", [])

                # Check if duty de minimis was applied
                duty_applied = next((d.get("value") for d in duty_calc if d.get("name") == "DUTY_DEMINIMIS_APPLIED"), "false")

                if duty_applied == "true":
                    duty_rate = 0.0
                    duty_breakdown.append({
                        'taxName': 'Duty',
                        'tax': 0.0,
                        'rate': 0.0,
                        'description': 'De Minimis exemption applied - no duty charged'
                    })
                else:
                    # Extract duty rate
                    duty_rate = next((float(d.get("value", 0)) for d in duty_calc if d.get("name") == "RATE"), 0.0)

                    # Parse cost lines for duties and taxes
                    for cost_line in cost_lines:
                        cost_type = cost_line.get('type', '')
                        tax_name = cost_line.get('taxName', cost_type)
                        amount = cost_line.get('amount', 0)
                        rate = cost_line.get('rate', 0)

                        duty_info = {
                            'taxName': tax_name,
                            'tax': amount,
                            'rate': rate * 100 if rate else duty_rate * 100,  # Convert to percentage
                            'description': get_tax_description(tax_name)
                        }

                        # Check if it's a punitive tariff (Chapter 98/99 or Section 301/232)
                        if is_punitive_tariff(tax_name):
                            duty_info['explanation'] = get_punitive_explanation(tax_name)
                            punitive_tariffs.append(duty_info)
                        else:
                            duty_breakdown.append(duty_info)

                # If no cost lines but we have duty rate, add it
                if not cost_lines and duty_rate > 0:
                    duty_breakdown.append({
                        'taxName': 'Duty',
                        'tax': shipment_value * duty_rate,
                        'rate': duty_rate * 100,
                        'description': 'Standard customs duty (MFN rate)'
                    })

        except Exception as parse_error:
            logger.error(f"Error parsing API response: {str(parse_error)}")
            # Return raw response if parsing fails
            pass

        # Build context for AI analysis
        transaction_context = {
            'origin_country': origin_country,
            'destination_country': destination_country,
            'hs_codes': {hs_code[:2]},
            'amount': shipment_value,
            'countries': {origin_country, destination_country}
        }

        # Get AI analysis
        issue_description = f"Analyze tariff calculation for HS Code {hs_code} from {origin_country} to {destination_country}"

        ai_analysis = get_ai_analysis(
            user_request={'hs_code': hs_code, 'origin': origin_country, 'destination': destination_country, 'value': shipment_value},
            api_response=api_response,
            user_response=None,
            issue_description=issue_description,
            comparison=None,
            chat_history=[],
            transaction_context=transaction_context
        )

        return jsonify({
            'success': True,
            'apiResponse': api_response,
            'dutyBreakdown': duty_breakdown,
            'punitiveTariffs': punitive_tariffs,
            'aiAnalysis': ai_analysis
        })

    except Exception as e:
        logger.error(f"Error in tariff lookup: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


def get_tax_description(tax_name):
    """Get human-readable description for tax type"""
    descriptions = {
        'Duty': 'Standard customs duty (MFN rate)',
        'Import VAT': 'Value Added Tax on imports',
        'Import Tax': 'General import tax',
        'GST': 'Goods and Services Tax',
        'Section 301': 'China tariffs under Section 301',
        'Section 232': 'Steel/Aluminum tariffs under Section 232',
        'Merchandise Processing Fee': 'MPF - US processing fee (0.3464%)',
        'Harbor Maintenance Fee': 'HMF - US harbor maintenance (0.125%)',
    }
    return descriptions.get(tax_name, 'Additional tax or duty')


def is_punitive_tariff(tax_name):
    """Check if tax is a punitive tariff"""
    punitive_keywords = ['section 301', '301', 'section 232', '232', 'chapter 98', 'chapter 99',
                         '9903', '9902', 'anti-dumping', 'countervailing', 'safeguard']
    tax_lower = tax_name.lower()
    return any(keyword in tax_lower for keyword in punitive_keywords)


def get_punitive_explanation(tax_name):
    """Get explanation for punitive tariff"""
    tax_lower = tax_name.lower()

    if 'section 301' in tax_lower or '301' in tax_lower:
        return 'Section 301 tariff imposed on Chinese imports due to unfair trade practices. Rates vary from 7.5% to 25% depending on product list.'

    if 'section 232' in tax_lower or '232' in tax_lower:
        return 'Section 232 tariff on steel (25%) or aluminum (10%) imports based on national security concerns. Applies to metal content.'

    if '9903' in tax_lower or 'chapter 99' in tax_lower:
        return 'Chapter 99 punitive tariff - additional tariff imposed through executive order or trade action.'

    if 'anti-dumping' in tax_lower:
        return 'Anti-dumping duty imposed on products sold below fair market value.'

    if 'countervailing' in tax_lower:
        return 'Countervailing duty to offset foreign government subsidies.'

    return 'Additional punitive tariff imposed through trade action or executive order.'


if __name__ == '__main__':
    app.run(debug=True, port=5001)
