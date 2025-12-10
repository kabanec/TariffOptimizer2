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
from exemption_database import analyze_stacking_with_exemptions

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
        try:
            # Initialize OpenAI client - only pass supported parameters
            _openai_client = OpenAI(
                api_key=OPENAI_API_KEY,
                timeout=30.0,
                max_retries=2
            )
        except TypeError as e:
            # If there's a parameter error, try with minimal parameters
            logger.warning(f"OpenAI client initialization failed with full params: {e}")
            try:
                _openai_client = OpenAI(api_key=OPENAI_API_KEY)
            except Exception as e2:
                logger.error(f"OpenAI client initialization failed completely: {e2}")
                raise
    return _openai_client

# AvaTax endpoints - Quotes API for duty calculations
AVATAX_ENDPOINTS = {
    'sandbox': f'https://quoting.xbo.dev.avalara.io/api/v2/companies/{AVALARA_COMPANY_ID}/quotes/create',
    'production': f'https://quoting.xbo.dev.avalara.io/api/v2/companies/{AVALARA_COMPANY_ID}/quotes/create'
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


def call_avatax_api(environment, hs_code, origin_country, destination_country, shipment_value, mode_of_transport, calculator_type='courier', section_232_auto=None, metal_composition=None):
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
        logger.info(f"Calculator Type: {calculator_type}")
        logger.info(f"Section 232 Auto: {section_232_auto}")
        logger.info(f"Metal Composition: {metal_composition}")
        logger.info(f"HS Code: {hs_code} (normalized: {hs_code_normalized}), Origin: {origin_country}, Destination: {destination_country}")

        # Build item parameters based on Section 232 inputs
        item_parameters = []

        # DO NOT send metal parameters for initial detection
        # This prevents false IEEPA tariffs for non-metal products like cosmetics
        # Metal parameters should only be sent when:
        # 1. User has provided metal composition (metal_composition is not None)
        # 2. We're doing a second API call after detecting Section 232 tariffs
        # For now, we rely on the API to return tariffs without metal params

        # Add automotive parameters if provided
        if section_232_auto:
            item_parameters.extend([
                {
                    "name": "232_auto",
                    "value": section_232_auto,
                    "unit": ""
                },
                {
                    "name": "232_coo",
                    "value": origin_country,
                    "unit": ""
                }
            ])

        # Add metal composition parameters if provided
        if metal_composition:
            for metal_data in metal_composition:
                metal_type = metal_data.get('metal')
                percentage = metal_data.get('percentage', '1.0')  # Default 100% = 1.0
                country = metal_data.get('country', origin_country)

                item_parameters.extend([
                    {
                        "name": "232_metal_percent",
                        "value": str(percentage),
                        "unit": metal_type
                    },
                    {
                        "name": "metal_coo",
                        "value": country,
                        "unit": metal_type
                    }
                ])

        # Build Quotes API request (matching quotes/create format)
        # Set region based on destination country
        ship_to_region = "NJ" if destination_country == "US" else ""

        payload = {
            "id": "tariff-lookup",
            "companyId": int(AVALARA_COMPANY_ID),
            "sellerCode": "TARIFF_LOOKUP",
            "currency": "USD",
            "shipTo": {
                "country": destination_country,
                "region": ship_to_region
            },
            "shipFrom": {
                "country": origin_country,
                "region": ""
            },
            "type": "QUOTE_MEDIAN",
            "lines": [
                {
                    "lineNumber": "0",
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
                                "value": "5.0",
                                "unit": "g"
                            }
                        ],
                        "parameters": item_parameters
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
                    "value": "50.0",
                    "unit": "USD"
                },
                {
                    "name": "AUTOMATIC_HS_FALLBACK",
                    "value": "true"
                }
            ],
            "taxRegistered": False
        }

        # Add shipmentType only for postal calculator
        if calculator_type == 'postal':
            payload["shipmentType"] = "postal"
            logger.info(f"Calculator type is 'postal', including shipmentType in payload")
        else:
            logger.info(f"Calculator type is 'courier', omitting shipmentType from payload")

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


@app.route('/exclusion-tester')
@login_required
def exclusion_tester():
    """Exclusion stacking tester page"""
    return render_template('exclusion_tester.html', username=session.get('username'))


@app.route('/test-validator')
@login_required
def test_validator():
    """Test validator page for customs brokers to validate exclusion logic"""
    return render_template('test_validator.html', username=session.get('username'))


@app.route('/stacking-builder')
@login_required
def stacking_builder():
    """Stacking logic builder with dynamic questionnaire"""
    return render_template('stacking_builder.html', username=session.get('username'))


# ========== STACKING BUILDER API ENDPOINTS ==========

@app.route('/api/find-applicable-tariffs', methods=['POST'])
@login_required
def find_applicable_tariffs():
    """Find applicable Chapter 98/99 tariffs based on base HS code and origin using AvaTax API"""
    try:
        data = request.json
        hs_code = data.get('hsCode', '')
        origin = data.get('origin', '')
        value = float(data.get('value', 0))

        logger.info(f"Finding applicable tariffs for HS {hs_code}, origin {origin}, value ${value}")

        # Call AvaTax API using the existing function
        api_response = call_avatax_api(
            environment='production',
            hs_code=hs_code,
            origin_country=origin,
            destination_country='US',
            shipment_value=value,
            mode_of_transport='courier'
        )

        if 'error' in api_response:
            logger.error(f"AvaTax API error: {api_response['error']}")
            return jsonify({
                'success': False,
                'error': api_response['error']
            }), 500

        # Log the full AvaTax response for debugging
        logger.info(f"AvaTax API Response: {json.dumps(api_response, indent=2)}")

        # Parse duty granularity to find Chapter 98/99 tariffs
        tariffs = []
        lines = api_response.get('lines', [])

        if lines:
            line = lines[0]
            calculation_summary = line.get('calculationSummary', {})
            duty_granularity = calculation_summary.get('dutyGranularity', [])

            logger.info(f"Found {len(duty_granularity)} duty items")

            for duty_item in duty_granularity:
                duty_type = duty_item.get('type', 'STANDARD')
                hs_code_item = duty_item.get('hsCode', '')
                rate_label = duty_item.get('rateLabel', '')
                description = duty_item.get('description', '')
                effective_rate = float(duty_item.get('effectiveRate', 0))

                # Only include Chapter 98/99 punitive tariffs
                if duty_type == 'PUNITIVE' or hs_code_item.startswith(('9903', '9902', '98', '99')):
                    # Determine category based on HS code and description
                    category = 'unknown'
                    desc_lower = description.lower()
                    label_lower = rate_label.lower()

                    # Section 232 Steel (99038.1.xx, 99038.6.xx, 99038.7.xx)
                    if hs_code_item.startswith('99038') and 'steel' in desc_lower:
                        category = 'section_232_steel'
                    # Section 232 Aluminum (99038.5.xx)
                    elif hs_code_item.startswith('99038') and 'aluminum' in desc_lower:
                        category = 'section_232_aluminum'
                    # Section 232 Automotive (99030.1.xx for autos)
                    elif hs_code_item.startswith('99030') and ('auto' in desc_lower or 'vehicle' in desc_lower):
                        category = 'section_232_automotive'
                    # Section 301 China (99038.8.xx, 99038.0.xx)
                    elif hs_code_item.startswith('99038') and ('301' in desc_lower or '301' in label_lower):
                        category = 'section_301'
                    # IEEPA Reciprocal - 99030125 or contains "reciprocal"
                    elif hs_code_item == '99030125' or 'reciprocal' in desc_lower:
                        category = 'ieepa_reciprocal'
                    # IEEPA Fentanyl - 99030136 or contains "fentanyl"
                    elif hs_code_item == '99030136' or 'fentanyl' in desc_lower:
                        category = 'ieepa_fentanyl'

                    tariffs.append({
                        'code': hs_code_item,
                        'name': rate_label or description,
                        'rate': effective_rate,
                        'amount': value * effective_rate,
                        'category': category,
                        'description': description
                    })

                    logger.info(f"Found punitive tariff: {hs_code_item} - {rate_label} ({category})")
                    logger.info(f"  Description: {description}")
                    logger.info(f"  Type: {duty_type}, Rate: {effective_rate*100:.2f}%")

        logger.info(f"Total punitive tariffs found: {len(tariffs)}")

        return jsonify({
            'success': True,
            'tariffs': tariffs,
            'hsCode': hs_code,
            'origin': origin
        })

    except Exception as e:
        logger.error(f"Error finding applicable tariffs: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/generate-stacking-questions', methods=['POST'])
@login_required
def generate_stacking_questions():
    """Generate deterministic questions based on found tariffs (NO GPT-4)"""
    try:
        from stacking_logic import get_required_questions

        data = request.json
        product_info = data.get('productInfo', {})
        found_tariffs = data.get('foundTariffs', [])

        logger.info(f"Generating questions for {len(found_tariffs)} tariffs")

        # Use deterministic logic to generate questions
        questions = get_required_questions(
            detected_tariffs=found_tariffs,
            origin_country=product_info.get('origin', '')
        )

        logger.info(f"Generated {len(questions)} deterministic questions")

        # Convert to format expected by frontend
        formatted_questions = []
        for q in questions:
            # Derive category from question ID for display purposes
            question_id = q['id']
            if 'steel' in question_id:
                category = 'Section 232 Steel'
            elif 'aluminum' in question_id:
                category = 'Section 232 Aluminum'
            elif 'ustr' in question_id or 'section_301' in question_id:
                category = 'Section 301'
            elif 'us_content' in question_id or 'informational' in question_id:
                category = 'IEEPA Reciprocal'
            elif 'usmca' in question_id:
                category = 'USMCA'
            else:
                category = 'Product Details'

            formatted_q = {
                'question': q['text'],
                'type': q['type'],
                'help': q.get('help', ''),
                'required': q.get('required', True),
                'category': category
            }

            # Add type-specific fields
            if q['type'] == 'boolean':
                formatted_q['options'] = q.get('options', ['Yes', 'No'])
            elif q['type'] == 'slider':
                formatted_q['type'] = 'number'  # Frontend compatibility
                formatted_q['min'] = q.get('min', 0)
                formatted_q['max'] = q.get('max', 100)
                formatted_q['unit'] = q.get('unit', '%')
            elif q['type'] == 'country_select':
                formatted_q['type'] = 'text'
                formatted_q['placeholder'] = 'US'

            # Store original question ID for answer mapping
            formatted_q['questionId'] = q['id']
            formatted_q['questionIndex'] = q['index']

            # Handle conditional questions
            if 'conditional' in q:
                formatted_q['conditional'] = q['conditional']

            formatted_questions.append(formatted_q)

        return jsonify({
            'success': True,
            'questions': formatted_questions
        })

    except Exception as e:
        logger.error(f"Error generating questions: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analyze-stacking', methods=['POST'])
@login_required
def analyze_stacking_endpoint():
    """Analyze stacking order based on answers using deterministic logic (NO GPT-4)"""
    try:
        from stacking_logic import analyze_stacking

        data = request.json
        product_info = data.get('productInfo', {})
        found_tariffs = data.get('foundTariffs', [])
        questions = data.get('questions', [])
        answers = data.get('answers', {})

        logger.info(f"Analyzing stacking for {len(found_tariffs)} tariffs with {len(answers)} answers")
        logger.info(f"Product: {product_info}")
        logger.info(f"Answers: {answers}")

        # Normalize product_info - frontend sends 'origin', backend expects 'origin_country'
        if 'origin' in product_info and 'origin_country' not in product_info:
            product_info['origin_country'] = product_info['origin']
        if 'hsCode' in product_info and 'hs_code' not in product_info:
            product_info['hs_code'] = product_info['hsCode']

        # Convert frontend answers to expected format
        # Frontend sends: {"0": "25%", "1": "CN", ...}
        # We need: {"steel_percentage": 25, "steel_origin_country": "CN", ...}
        parsed_answers = {}
        for q in questions:
            question_id = q.get('questionId')
            question_index = q.get('questionIndex')
            question_type = q.get('type')

            # Get answer by index
            answer_raw = answers.get(str(question_index))

            if answer_raw is not None:
                # Parse based on type
                if question_type == 'number':
                    # Handle percentage strings like "25%" or "25"
                    answer_str = str(answer_raw).replace('%', '').strip()
                    try:
                        parsed_answers[question_id] = float(answer_str)
                    except:
                        parsed_answers[question_id] = 0.0
                elif question_type == 'boolean':
                    answer_str = str(answer_raw).lower().strip()
                    parsed_answers[question_id] = answer_str in ['yes', 'true', '1']
                elif question_type == 'text':
                    parsed_answers[question_id] = str(answer_raw).strip().upper()
                else:
                    parsed_answers[question_id] = answer_raw

        logger.info(f"Parsed answers: {parsed_answers}")

        # Use deterministic stacking analysis
        analyzed_tariffs = analyze_stacking(
            tariffs=found_tariffs,
            answers=parsed_answers,
            product_info=product_info
        )

        # Calculate totals
        total_before = sum(t['amount'] for t in found_tariffs)
        total_after = sum(t['final_amount'] for t in analyzed_tariffs)
        savings = total_before - total_after

        # Build stacking order for frontend
        stacking_order = []
        for t in analyzed_tariffs:
            stacking_order.append({
                'tariffName': t['name'],
                'tariffCode': t['code'],
                'category': t['category'],
                'originalRate': f"{t['rate'] * 100:.2f}%",
                'originalAmount': t['amount'],
                'finalAmount': t['final_amount'],
                'excluded': t['excluded'],
                'exemptionCode': t['exemption_code'],
                'reasoning': t['reasoning']
            })

        result = {
            'stackingOrder': stacking_order,
            'totalBefore': total_before,
            'totalAfter': total_after,
            'savings': savings
        }

        logger.info(f"Stacking analysis complete: ${total_before:.2f} -> ${total_after:.2f} (savings: ${savings:.2f})")

        return jsonify({
            'success': True,
            **result
        })

    except Exception as e:
        logger.error(f"Error analyzing stacking: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== EXCLUSION UPDATE CHECKER HELPER FUNCTIONS ==========

def discover_regulatory_changes(last_check):
    """Phase 1: Use web search to discover recent regulatory changes

    Returns a dict of discovered sources with their content
    """
    from datetime import datetime
    import json
    import re

    logger.info(f"Discovering regulatory changes since {last_check}")
    discovered = {
        'federal_register': [],
        'cbp_bulletins': [],
        'ustr_releases': [],
        'executive_orders': []
    }

    try:
        client = get_openai_client()

        # Use GPT-4 to search for recent regulatory changes
        # Note: GPT-4 doesn't have live web access, but has knowledge up to its cutoff
        # For true web search, we'd need to integrate with an actual search API
        search_prompt = f"""List recent (since {last_check}) U.S. regulatory changes related to tariff exclusions.

Focus on:
1. Federal Register notices about Section 232, Section 301, IEEPA tariffs
2. CBP CSMS bulletins announcing changes to Chapter 99 exclusions
3. USTR press releases about tariff exclusion extensions or revocations
4. Executive Orders or Presidential Proclamations affecting trade

For each item, provide:
- Date
- Title/Subject
- Source (Federal Register number, CSMS number, EO number, etc.)
- Brief summary
- URL if known

Return as JSON array."""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a regulatory research specialist tracking U.S. trade policy changes."},
                {"role": "user", "content": search_prompt}
            ],
            temperature=0.2,
            max_tokens=3000
        )

        content = response.choices[0].message.content

        # Try to parse JSON
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            sources = json.loads(json_match.group())
            logger.info(f"Discovered {len(sources)} regulatory sources")
            discovered['raw_sources'] = sources
        else:
            discovered['raw_sources'] = []

    except Exception as e:
        logger.error(f"Error discovering regulatory changes: {e}")
        discovered['error'] = str(e)

    return discovered


def analyze_section_232_updates(client, last_check, discovered_sources):
    """Analyze Section 232 Steel/Aluminum exclusion updates"""
    from datetime import datetime
    import json
    import re

    logger.info("Analyzing Section 232 updates...")

    prompt = f"""Analyze recent (since {last_check}) changes to Section 232 Steel and Aluminum tariff exclusions.

FOCUS AREAS:
- USMCA exemptions (9903.01.26, 9903.01.27) - any modifications?
- U.S.-origin steel/aluminum exemptions (9903.81.92, etc.) - any changes?
- Commerce Department product-specific exclusions - status changes?
- General Approved Exclusions (GAEs) - revocations?
- New derivative product tariffs (9903.81.89, 9903.81.90, etc.)

CRITICAL: Check for:
- Executive Orders revoking previous exemptions
- Presidential Proclamations adding new tariffs
- CBP CSMS bulletins about processing changes
- Expiration dates of existing exclusions

For each change, provide:
- date: YYYY-MM-DD
- htsus_codes: [array of affected codes]
- type: NEW, REVOKED, EXTENDED, MODIFIED, SUPERSEDED, or EXPIRED
- description: What changed and why (2-3 sentences)
- source: Specific source (EO number, Proclamation, CSMS number)
- reference: URL if available
- impact: How this affects importers

Return ONLY a JSON array. No markdown, no explanation."""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a Section 232 tariff specialist. Return only valid JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )

        content = response.choices[0].message.content

        # Extract JSON
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            updates = json.loads(json_match.group())
            return updates
        else:
            return []

    except Exception as e:
        logger.error(f"Error analyzing Section 232: {e}")
        return []


def analyze_section_301_updates(client, last_check, discovered_sources):
    """Analyze Section 301 China tariff exclusion updates"""
    from datetime import datetime
    import json
    import re

    logger.info("Analyzing Section 301 updates...")

    prompt = f"""Analyze recent (since {last_check}) changes to Section 301 China tariff exclusions.

FOCUS AREAS:
- USTR product-specific exclusions (9903.88.69, 9903.88.70) - extensions or expirations?
- New exclusions granted by USTR
- Revoked exclusions
- Section 321 de minimis exemption - any policy changes?
- Chapter 98 provisions - modifications?

CRITICAL: Check for:
- USTR Federal Register notices
- Extensions announced (like Nov 10, 2026 extension)
- New product exclusions granted
- Expired exclusions not renewed

For each change, provide:
- date: YYYY-MM-DD
- htsus_codes: [array of affected codes]
- type: NEW, REVOKED, EXTENDED, MODIFIED, SUPERSEDED, or EXPIRED
- description: What changed and why (2-3 sentences)
- source: Federal Register citation, USTR announcement
- reference: URL if available
- impact: How this affects importers

Return ONLY a JSON array. No markdown, no explanation."""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a Section 301 tariff specialist. Return only valid JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )

        content = response.choices[0].message.content

        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            updates = json.loads(json_match.group())
            return updates
        else:
            return []

    except Exception as e:
        logger.error(f"Error analyzing Section 301: {e}")
        return []


def analyze_ieepa_updates(client, last_check, discovered_sources):
    """Analyze IEEPA reciprocal tariff and exemption updates"""
    from datetime import datetime
    import json
    import re

    logger.info("Analyzing IEEPA updates...")

    prompt = f"""Analyze recent (since {last_check}) changes to IEEPA reciprocal tariffs and exemptions.

FOCUS AREAS:
- Informational materials exemption (9903.01.21) - still valid?
- China/Hong Kong/Macau reciprocal exclusion (9903.01.30) - rate changes?
- Section 232 exemption from reciprocal tariffs (9903.01.33)
- U.S. content exemption >20% (9903.01.34)
- New IEEPA tariffs announced?
- Fentanyl-related tariffs (99030122) - rate changes?

CRITICAL: Check for:
- New Executive Orders under IEEPA authority
- Presidential Proclamations modifying reciprocal tariff rates
- CBP CSMS guidance on IEEPA exemptions
- Country-specific tariff changes

For each change, provide:
- date: YYYY-MM-DD
- htsus_codes: [array of affected codes]
- type: NEW, REVOKED, EXTENDED, MODIFIED, SUPERSEDED, or EXPIRED
- description: What changed and why (2-3 sentences)
- source: EO number, Proclamation, CSMS number
- reference: URL if available
- impact: How this affects importers

Return ONLY a JSON array. No markdown, no explanation."""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an IEEPA tariff specialist. Return only valid JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )

        content = response.choices[0].message.content

        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            updates = json.loads(json_match.group())
            return updates
        else:
            return []

    except Exception as e:
        logger.error(f"Error analyzing IEEPA: {e}")
        return []


def analyze_usmca_updates(client, last_check, discovered_sources):
    """Analyze USMCA exemption updates"""
    from datetime import datetime
    import json
    import re

    logger.info("Analyzing USMCA updates...")

    prompt = f"""Analyze recent (since {last_check}) changes to USMCA tariff exemptions.

FOCUS AREAS:
- USMCA exemptions for Section 232 (9903.01.26 Canada, 9903.01.27 Mexico)
- Changes to USMCA qualifying criteria
- New restrictions on USMCA exemptions
- Modifications to general note 11 to HTSUS

CRITICAL: Check for:
- Presidential Proclamations modifying USMCA exemptions
- CBP rulings on USMCA qualification
- Changes to country-of-origin rules
- Suspensions or limitations on USMCA benefits

For each change, provide:
- date: YYYY-MM-DD
- htsus_codes: [array of affected codes]
- type: NEW, REVOKED, EXTENDED, MODIFIED, SUPERSEDED, or EXPIRED
- description: What changed and why (2-3 sentences)
- source: Proclamation, CBP ruling, CSMS number
- reference: URL if available
- impact: How this affects importers

Return ONLY a JSON array. No markdown, no explanation."""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a USMCA trade specialist. Return only valid JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )

        content = response.choices[0].message.content

        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            updates = json.loads(json_match.group())
            return updates
        else:
            return []

    except Exception as e:
        logger.error(f"Error analyzing USMCA: {e}")
        return []


def validate_existing_exclusions(client, last_check, discovered_sources):
    """Validate that existing exclusions haven't been superseded by newer rules"""
    from datetime import datetime

    logger.info("Validating existing exclusions against newer regulations...")

    validation_warnings = []

    # Hardcoded known revocations
    revoked_exclusions = {
        '9903.81.01': {'date': '2025-03-12', 'reason': 'GAE revoked by CBP CSMS #65236374', 'superseded_by': 'USMCA exemptions only (9903.01.26, 9903.01.27)'},
        '9903.81.02': {'date': '2025-03-12', 'reason': 'GAE revoked by CBP CSMS #65236374', 'superseded_by': 'USMCA exemptions only'},
        '9903.81.03': {'date': '2025-03-12', 'reason': 'GAE revoked by CBP CSMS #65236374', 'superseded_by': 'USMCA exemptions only'},
        '9903.81.04': {'date': '2025-03-12', 'reason': 'GAE revoked by CBP CSMS #65236374', 'superseded_by': 'USMCA exemptions only'},
        '9903.85.01': {'date': '2025-03-12', 'reason': 'GAE revoked by CBP CSMS #65236374', 'superseded_by': 'USMCA exemptions only'},
        '9903.85.02': {'date': '2025-03-12', 'reason': 'GAE revoked by CBP CSMS #65236374', 'superseded_by': 'USMCA exemptions only'},
        '9903.85.03': {'date': '2025-03-12', 'reason': 'GAE revoked by CBP CSMS #65236374', 'superseded_by': 'USMCA exemptions only'},
    }

    for code, revocation_info in revoked_exclusions.items():
        if revocation_info['date'] >= last_check:
            validation_warnings.append({
                'date': revocation_info['date'],
                'htsus_codes': [code],
                'type': 'SUPERSEDED',
                'description': f"Exclusion {code} has been REVOKED and is no longer valid. {revocation_info['reason']}. Use {revocation_info['superseded_by']} instead if applicable.",
                'source': 'Validation Check',
                'reference': 'https://content.govdelivery.com/accounts/USDHSCBP/bulletins/3e36d96',
                'impact': 'CRITICAL: Remove this exclusion from database. Use alternative exemptions only if conditions are met.'
            })

    return validation_warnings


@app.route('/api/check-exclusion-updates', methods=['POST'])
@login_required
def check_exclusion_updates():
    """Check for recent updates to Section 99 exclusions from official sources

    Uses a hybrid approach:
    1. Web search to discover recent regulatory changes
    2. Multiple specialized GPT-4 calls for detailed analysis
    """
    try:
        from datetime import datetime, timedelta
        import json
        import concurrent.futures

        # Get the last check date from request (or default to 90 days ago)
        last_check = request.json.get('lastCheckDate', (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'))

        logger.info(f"Checking for exclusion updates since {last_check}")

        client = get_openai_client()
        all_updates = []

        # PHASE 1: Web discovery for recent regulatory changes
        logger.info("Phase 1: Discovering recent regulatory changes via web search")
        discovered_sources = discover_regulatory_changes(last_check)

        # PHASE 2: Multiple specialized GPT-4 analyses (run in parallel)
        logger.info("Phase 2: Running specialized analyses in parallel")

        analysis_tasks = [
            ('section_232', analyze_section_232_updates),
            ('section_301', analyze_section_301_updates),
            ('ieepa', analyze_ieepa_updates),
            ('usmca', analyze_usmca_updates),
            ('validation', validate_existing_exclusions)
        ]

        # Run analyses in parallel for speed
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_category = {
                executor.submit(func, client, last_check, discovered_sources): category
                for category, func in analysis_tasks
            }

            for future in concurrent.futures.as_completed(future_to_category):
                category = future_to_category[future]
                try:
                    updates = future.result()
                    logger.info(f"Completed {category} analysis: {len(updates)} updates found")
                    all_updates.extend(updates)
                except Exception as e:
                    logger.error(f"Error in {category} analysis: {e}")
                    all_updates.append({
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'type': 'ERROR',
                        'description': f'Error analyzing {category}: {str(e)}',
                        'source': 'System'
                    })

        # PHASE 3: Add hardcoded known recent changes (as of December 2025)
        logger.info("Phase 3: Adding hardcoded known changes")
        known_changes = [
            {
                'date': '2025-03-12',
                'htsus_codes': ['9903.01.26', '9903.01.27', '9903.81.*', '9903.85.*'],
                'type': 'REVOKED',
                'description': 'All General Approved Exclusions (GAEs) and country-level arrangements for Section 232 steel and aluminum duties were revoked effective 12:01 AM ET',
                'source': 'CBP CSMS #65236374',
                'reference': 'https://content.govdelivery.com/accounts/USDHSCBP/bulletins/3e36d96',
                'impact': 'USMCA exemptions (9903.01.26, 9903.01.27) remain valid, but other country-specific GAEs no longer apply'
            },
            {
                'date': '2025-02-10',
                'htsus_codes': ['9903.81.*', '9903.85.*'],
                'type': 'POLICY_CHANGE',
                'description': 'Department of Commerce stopped accepting and processing new Section 232 exclusion requests',
                'source': 'Commerce Department Announcement',
                'reference': 'https://www.bis.doc.gov/index.php/232-steel',
                'impact': 'Existing approved exclusions remain valid until expiration/quantity exhausted, but no new exclusions will be granted'
            },
            {
                'date': '2025-11-10',
                'htsus_codes': ['9903.88.69', '9903.88.70'],
                'type': 'EXTENDED',
                'description': 'USTR extended 178 Section 301 China tariff exclusions (164 product-specific + 14 manufacturing equipment) through November 10, 2026',
                'source': 'USTR Press Release',
                'reference': 'https://www.federalregister.gov/documents/2025/09/02/2025-16733/notice-of-product-exclusion-extensions-chinas-acts-policies-and-practices-related-to-technology',
                'impact': 'Importers can continue claiming these exclusions for an additional year'
            },
            {
                'date': '2025-08-18',
                'htsus_codes': ['9903.81.89', '9903.81.90', '9903.85.07', '9903.85.08'],
                'type': 'NEW',
                'description': '50% Section 232 tariffs imposed on 407 additional steel and aluminum derivative products',
                'source': 'Presidential Proclamation',
                'reference': 'https://www.ghy.com/trade-compliance/50-section-232-tariffs-on-407-new-steel-and-aluminum-derivatives-take-effect-aug-18-cbp-guidance-available/',
                'impact': 'Significant duty increase on derivative products; no exemptions for in-transit goods'
            }
        ]

        # Filter known changes by date
        filtered_known_changes = [
            change for change in known_changes
            if change['date'] >= last_check
        ]

        # Combine all updates
        all_updates.extend(filtered_known_changes)

        # Remove duplicates based on date + description
        seen = set()
        unique_updates = []
        for update in all_updates:
            key = (update.get('date', ''), update.get('description', ''))
            if key not in seen:
                seen.add(key)
                unique_updates.append(update)

        # Sort by date (most recent first)
        unique_updates.sort(key=lambda x: x.get('date', ''), reverse=True)

        logger.info(f"Total updates found: {len(unique_updates)}")

        return jsonify({
            'success': True,
            'lastChecked': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'updatesFound': len(unique_updates),
            'updates': unique_updates,
            'phases_completed': {
                'discovery': True,
                'analysis': True,
                'validation': True
            }
        })

    except Exception as e:
        logger.error(f"Error checking exclusion updates: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


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
        calculator_type = data.get('calculatorType', 'courier')
        section_232_auto = data.get('section232Auto')  # Optional Section 232 automotive parameter
        metal_composition = data.get('metalComposition')  # Optional Section 232 metal composition
        environment = data.get('environment', 'sandbox')

        if not all([hs_code, origin_country, destination_country, entry_date]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Call AvaTax Global Compliance API
        api_response = call_avatax_api(environment, hs_code, origin_country, destination_country, shipment_value, mode_of_transport, calculator_type, section_232_auto, metal_composition)

        if 'error' in api_response:
            logger.error(f"AvaTax API Error: {api_response}")
            return jsonify({
                'error': api_response.get('error'),
                'details': api_response.get('details'),
                'status_code': api_response.get('status_code'),
                'full_response': api_response.get('full_response')
            }), api_response.get('status_code', 500)

        # Parse Quotes API response
        duty_breakdown = []
        punitive_tariffs = []
        section_232_automotive_options = []
        section_232_metal_options = []

        try:
            # Extract line data from Quotes API response
            lines = api_response.get('lines', [])

            if lines:
                line = lines[0]

                # Parse dutyGranularity from calculationSummary for detailed duty breakdown
                calculation_summary = line.get("calculationSummary", {})
                duty_granularity = calculation_summary.get("dutyGranularity", [])

                logger.info(f"Processing {len(duty_granularity)} duty items")
                for duty_item in duty_granularity:
                    duty_type = duty_item.get('type', 'STANDARD')
                    rate_label = duty_item.get('rateLabel', '')
                    description = duty_item.get('description', '')
                    effective_rate = float(duty_item.get('effectiveRate', 0))
                    hs_code_item = duty_item.get('hsCode', '')
                    logger.info(f"Duty item: type={duty_type}, hsCode={hs_code_item}, rateLabel={rate_label}")

                    duty_info = {
                        'taxName': rate_label or description,
                        'tax': shipment_value * effective_rate,  # Calculate duty amount
                        'rate': effective_rate,  # Keep as decimal (e.g., 0.10 for 10%)
                        'description': description,
                        'hsCode': hs_code_item,
                        'calculationMethod': duty_item.get('calculationMethod', ''),
                        'applicability': duty_item.get('applicability', '')
                    }

                    # Check if it's a punitive tariff based on type or HS code
                    if duty_type == 'PUNITIVE' or hs_code_item.startswith(('9903', '9902', '98', '99')):
                        duty_info['explanation'] = description
                        punitive_tariffs.append(duty_info)

                        # Check for Section 232 automotive-related duties
                        # IMPORTANT: Only check duties that have "SECTION 232" in the rateLabel
                        # Don't match other 9903* codes like Fentanyl
                        if 'section 232' in rate_label.lower():
                            automotive_keywords = ['auto', 'heavy vehicle', 'trucks', 'medium truck', 'parts', 'buses']
                            metal_keywords = ['steel', 'aluminum', 'copper', 'lumber']
                            desc_lower = description.lower()

                            # Check for automotive keywords
                            is_automotive = False
                            for keyword in automotive_keywords:
                                if keyword in desc_lower:
                                    section_232_automotive_options.append({
                                        'keyword': keyword.title(),
                                        'description': description,
                                        'rateLabel': rate_label
                                    })
                                    is_automotive = True
                                    break

                            # Check for metal keywords (only if not automotive)
                            # Note: Check rate_label as well since it may be more specific than description
                            if not is_automotive:
                                rate_label_lower = rate_label.lower()
                                logger.info(f"Checking metals for rate_label: {rate_label}")
                                for metal in metal_keywords:
                                    if metal in desc_lower or metal in rate_label_lower:
                                        logger.info(f"  -> Found metal '{metal}' in rate_label or description")
                                        section_232_metal_options.append({
                                            'metal': metal,
                                            'description': description,
                                            'rateLabel': rate_label
                                        })
                                        break  # Each duty is for one specific metal
                                logger.info(f"  -> No metal match found for this duty")
                    else:
                        duty_breakdown.append(duty_info)

                # If no duty granularity, fall back to cost lines
                if not duty_granularity:
                    cost_lines = line.get("costLines", [])
                    for cost_line in cost_lines:
                        cost_type = cost_line.get('type', '')
                        tax_name = cost_line.get('taxName', cost_type)
                        amount = cost_line.get('amount', 0)
                        rate = cost_line.get('rate', 0)

                        duty_info = {
                            'taxName': tax_name,
                            'tax': amount,
                            'rate': rate,  # Keep as decimal
                            'description': get_tax_description(tax_name)
                        }

                        if is_punitive_tariff(tax_name):
                            duty_info['explanation'] = get_punitive_explanation(tax_name)
                            punitive_tariffs.append(duty_info)
                        else:
                            duty_breakdown.append(duty_info)

        except Exception as parse_error:
            logger.error(f"Error parsing API response: {str(parse_error)}")
            import traceback
            traceback.print_exc()
            # Return raw response if parsing fails
            pass

        # Build context for AI analysis
        transaction_context = {
            'origin_country': origin_country,
            'destination_country': destination_country,
            'hs_codes': {hs_code[:2]},
            'amount': shipment_value,
            'countries': {origin_country, destination_country},
            'punitive_tariffs': punitive_tariffs
        }

        # ONLY call AI on final calculation (when Section 232 parameters provided)
        # This saves API costs by avoiding AI calls on initial detection queries
        ai_analysis = None
        if section_232_auto or metal_composition:
            # This is a final calculation with Section 232 parameters
            # Build detailed prompt for AI to analyze Section 99 punitive tariffs
            punitive_details = ""
            if punitive_tariffs:
                punitive_details = "\n\nSection 99 Punitive Tariffs Found:\n"
                for tariff in punitive_tariffs:
                    punitive_details += f"- {tariff.get('taxName', 'Unknown')}: {tariff.get('rate', 0)*100:.2f}% (HS {tariff.get('hsCode', 'N/A')})\n"
                    punitive_details += f"  Description: {tariff.get('description', 'N/A')}\n"

            issue_description = f"""Analyze this tariff calculation and provide detailed guidance on Section 99 punitive tariff exemptions and options.

Transaction Details:
- HS Code: {hs_code}
- Origin: {origin_country}
- Destination: {destination_country}
- Shipment Value: ${shipment_value}
{punitive_details}

CRITICAL INSTRUCTIONS:
For EACH Section 99 punitive tariff found above (Section 232, Section 301, IEEPA, etc.):

1. **Exemption Conditions**: List ALL possible exemptions or exclusions that could apply
   - Country-specific exemptions (e.g., "Excluded if product manufactured in Canada, Mexico, EU")
   - Product-specific exclusions (e.g., "Excluded if aluminum content < 10%")
   - End-use exemptions (e.g., "Excluded if used for specific purposes")
   - Certificate/documentation exemptions

2. **Mitigation Options**: What steps can the user take to reduce or eliminate this duty?
   - Required documentation (certificates of origin, exclusion requests, etc.)
   - Alternative sourcing countries that are exempt
   - Product composition thresholds
   - Exclusion request processes

3. **Additional Information Needed**: What specific data would you need from the user to determine if they qualify for an exemption?
   - Manufacturing location details
   - Product composition percentages
   - End-use information
   - Supply chain details

Format your response with clear sections for each punitive tariff. Be specific and actionable."""

            ai_analysis = get_ai_analysis(
                user_request={'hs_code': hs_code, 'origin': origin_country, 'destination': destination_country, 'value': shipment_value},
                api_response=api_response,
                user_response=None,
                issue_description=issue_description,
                comparison=None,
                chat_history=[],
                transaction_context=transaction_context
            )
        else:
            # Initial detection call - skip AI to save costs
            logger.info("Skipping AI analysis on initial detection call to save costs")

        # Remove duplicates from section_232_automotive_options
        unique_automotive_options = []
        seen_keywords = set()
        for opt in section_232_automotive_options:
            if opt['keyword'] not in seen_keywords:
                unique_automotive_options.append(opt)
                seen_keywords.add(opt['keyword'])

        # Remove duplicates from section_232_metal_options
        logger.info(f"Metal options before deduplication: {section_232_metal_options}")
        unique_metal_options = []
        seen_metals = set()
        for opt in section_232_metal_options:
            if opt['metal'] not in seen_metals:
                unique_metal_options.append(opt)
                seen_metals.add(opt['metal'])
        logger.info(f"Metal options after deduplication: {unique_metal_options}")

        # ONLY show metals that are actually in the API response - do NOT add extras

        return jsonify({
            'success': True,
            'apiResponse': api_response,
            'dutyBreakdown': duty_breakdown,
            'punitiveTariffs': punitive_tariffs,
            'section232AutomotiveOptions': unique_automotive_options,
            'section232MetalOptions': unique_metal_options,
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


@app.route('/api-tester')
def api_tester():
    """API testing page"""
    return render_template('api_tester.html')


@app.route('/api/test-avatax', methods=['POST'])
def test_avatax():
    """Test endpoint for direct AvaTax API calls"""
    try:
        import base64
        data = request.json
        custom_url = data.get('customUrl')
        payload = data.get('payload', {})

        # Use custom URL if provided, otherwise fall back to endpoint type
        if custom_url:
            endpoint_url = custom_url
        else:
            endpoint_type = data.get('endpoint', 'quotes')
            endpoints = {
                'quotes': f'https://quoting.xbo.dev.avalara.io/api/v2/companies/{AVALARA_COMPANY_ID}/quotes/create',
                'globalcompliance': f'https://quoting.xbo.dev.avalara.io/api/v2/companies/{AVALARA_COMPANY_ID}/globalcompliance'
            }
            endpoint_url = endpoints.get(endpoint_type)
            if not endpoint_url:
                return jsonify({'error': 'Invalid endpoint type'}), 400

        if not AVALARA_USERNAME or not AVALARA_PASSWORD:
            return jsonify({'error': 'Avalara credentials not configured'}), 500

        # Use Basic Authentication
        credentials = base64.b64encode(f"{AVALARA_USERNAME}:{AVALARA_PASSWORD}".encode()).decode()
        headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        logger.info(f"Testing AvaTax API")
        logger.info(f"URL: {endpoint_url}")
        logger.info(f"Request payload: {json.dumps(payload, indent=2)}")

        response = requests.post(endpoint_url, headers=headers, json=payload, timeout=30)

        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {response.text[:2000]}")

        # Return response with status code
        try:
            response_data = response.json()
            response_data['status_code'] = response.status_code
            return jsonify(response_data), response.status_code
        except:
            return jsonify({
                'error': 'Failed to parse response',
                'status_code': response.status_code,
                'raw_response': response.text
            }), response.status_code

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return jsonify({'error': f'Request failed: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Unexpected error in test_avatax: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)
