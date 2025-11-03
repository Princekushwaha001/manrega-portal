
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import base64

API_BASE_URL = "http://localhost:8000"

import os
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="MGNREGA Data Portal | मनरेगा डेटा पोर्टल",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Educational tooltips dictionary
TOOLTIPS = {
    "families_employed": {
        "en": "Number of families who received work under MGNREGA this month",
        "hi": "इस महीने मनरेगा के तहत जिन परिवारों को काम मिला",
        "simple": "कितने परिवारों को काम मिला"
    },
    "avg_wage": {
        "en": "Average money paid per day to each worker",
        "hi": "प्रति दिन प्रति मजदूर को मिलने वाली औसत राशि",
        "simple": "रोज़ कितने पैसे मिलते हैं"
    },
    "avg_days": {
        "en": "Average number of days of work provided per family",
        "hi": "प्रति परिवार को दिए गए औसत कार्य दिवस",
        "simple": "कितने दिन काम मिला"
    },
    "total_expenditure": {
        "en": "Total money spent on MGNREGA in this district",
        "hi": "इस जिले में मनरेगा पर कुल खर्च की गई राशि",
        "simple": "कुल कितना पैसा खर्च हुआ"
    },
    "women_participation": {
        "en": "Percentage of total work done by women workers. Target is 50% as per MGNREGA guidelines",
        "hi": "कुल काम में महिला मजदूरों की भागीदारी का प्रतिशत। मनरेगा दिशानिर्देशों के अनुसार लक्ष्य 50% है",
        "simple": "महिलाओं को कितना काम मिला (लक्ष्य: 50%)"
    },
    "completion_rate": {
        "en": "Percentage of works completed out of total works started. Higher is better",
        "hi": "शुरू किए गए कुल कार्यों में से पूरे किए गए कार्यों का प्रतिशत। अधिक बेहतर है",
        "simple": "कितने काम पूरे हुए (जो शुरू किए थे)"
    },
    "mgnrega_about": {
        "en": "MGNREGA guarantees 100 days of wage employment per year to every rural household whose adult members volunteer for unskilled manual work",
        "hi": "मनरेगा हर ग्रामीण परिवार को साल में 100 दिन के वेतन रोजगार की गारंटी देता है जिसके वयस्क सदस्य अकुशल शारीरिक काम के लिए स्वेच्छा से आते हैं",
        "simple": "गांव के हर परिवार को साल में 100 दिन काम की गारंटी"
    }
}

st.markdown("""
<style>
    :root {
        --india-saffron: #FF9933;
        --india-white: #FFFFFF;
        --india-green: #138808;
        --gov-blue: #034EA2;
        --gov-dark-blue: #1e3a5f;
        --gov-light-blue: #F0F4F8;
        --gov-accent: #FF6B35;
    }

    /* Remove Streamlit default spacing at bottom */
    .main .block-container {
        padding-bottom: 0rem !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Government Header with NIC branding */
    .gov-header {
        background: linear-gradient(90deg, var(--india-saffron) 0%, var(--india-white) 50%, var(--india-green) 100%);
        padding: 3px;
        margin: -70px -100px 20px -100px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* White Header Content (Original) */
    .gov-header-content {
        background: white;
        padding: 15px 40px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    /* Blue Header Content (NEW - For Blue Background) */
    .gov-header-content-blue {
        background: linear-gradient(135deg, #034EA2 0%, #0056b3 100%);
        padding: 20px 40px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }

    .gov-title-section {
        display: flex;
        align-items: center;
        gap: 20px;
    }

    /* Default Title Colors (for white background) */
    .gov-title h1 {
        color: var(--gov-dark-blue);
        font-size: 22px;
        margin: 0;
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    .gov-title h2 {
        color: #666;
        font-size: 15px;
        margin: 5px 0 0 0;
        font-weight: 400;
    }

    .gov-subtitle {
        color: var(--india-green);
        font-size: 13px;
        margin: 3px 0 0 0;
        font-weight: 500;
    }

    /* Title Colors for Blue Background (NEW) */
    .gov-header-content-blue .gov-title h1 {
        color: white;
        font-size: 22px;
        margin: 0;
        font-weight: 700;
        letter-spacing: -0.5px;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
    }

    .gov-header-content-blue .gov-title h2 {
        color: rgba(255, 255, 255, 0.95);
        font-size: 15px;
        margin: 5px 0 0 0;
        font-weight: 400;
    }

    .gov-subtitle-white {
        color: rgba(255, 255, 255, 0.9);
        font-size: 13px;
        margin: 3px 0 0 0;
        font-weight: 500;
    }

    /* NIC Footer - Fixed to bottom with no gap */
    .nic-footer {
        background: var(--gov-dark-blue);
        color: white;
        padding: 40px 50px 30px 50px;
        margin: 50px -100px 0 -100px;
        width: calc(100% + 200px);
    }

    .footer-content {
        display: flex;
        justify-content: space-between;
        align-items: start;
        max-width: 1400px;
        margin: 0 auto;
        gap: 60px;
    }

    .footer-section {
        flex: 1;
        min-width: 250px;
    }

    .footer-section h4 {
        color: var(--india-saffron);
        font-size: 16px;
        margin-bottom: 20px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .footer-section ul {
        list-style: none;
        padding: 0;
        margin: 0;
    }

    .footer-section li {
        margin-bottom: 12px;
        font-size: 14px;
        line-height: 1.6;
        color: rgba(255, 255, 255, 0.9);
    }

    .footer-section a {
        color: rgba(255, 255, 255, 0.9);
        text-decoration: none;
        transition: color 0.3s;
    }

    .footer-section a:hover {
        color: var(--india-saffron);
        text-decoration: underline;
    }

    .footer-bottom {
        text-align: center;
        margin-top: 30px;
        padding-top: 25px;
        border-top: 1px solid rgba(255, 255, 255, 0.15);
    }

    .footer-bottom p {
        font-size: 13px;
        line-height: 1.8;
        color: rgba(255, 255, 255, 0.9);
        margin: 0;
    }

    /* Selection Panel */
    .selection-panel {
        background: var(--gov-light-blue);
        padding: 25px;
        border-radius: 8px;
        border-left: 4px solid var(--gov-blue);
        margin: 20px 0;
    }

    .selection-title {
        color: var(--gov-blue);
        font-size: 20px;
        font-weight: 600;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* District Header matching official portal */
    .district-header {
        background: var(--gov-dark-blue);
        color: white;
        padding: 25px;
        border-radius: 0;
        margin: 20px -100px 20px -100px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    .district-header h2 {
        margin: 0;
        font-size: 26px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .district-header p {
        margin: 8px 0 0 0;
        font-size: 14px;
        opacity: 0.9;
    }

    /* Info/Help icon styling */
    .info-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 18px;
        height: 18px;
        border-radius: 50%;
        background: var(--gov-blue);
        color: white;
        font-size: 12px;
        font-weight: bold;
        cursor: help;
        margin-left: 5px;
        transition: all 0.3s;
    }

    .info-icon:hover {
        background: var(--india-green);
        transform: scale(1.2);
    }

    /* Stat boxes with tooltips */
    .stat-box {
        background: white;
        padding: 20px;
        border-radius: 8px;
        border-left: 4px solid var(--gov-blue);
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.3s;
    }

    .stat-box:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transform: translateY(-3px);
    }

    .stat-value {
        color: var(--gov-blue);
        font-size: 28px;
        font-weight: 700;
        line-height: 1;
        margin: 10px 0;
    }

    /* Info cards */
    .info-card {
        background: #FFF9E6;
        border-left: 4px solid #FFC107;
        padding: 15px 20px;
        border-radius: 6px;
        margin: 15px 0;
    }

    .info-card-title {
        color: #F57C00;
        font-weight: 600;
        font-size: 14px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .info-card-text {
        color: #666;
        font-size: 13px;
        line-height: 1.6;
    }

    /* Help section */
    .help-box {
        background: #E8F5E9;
        border-left: 4px solid var(--india-green);
        padding: 15px 20px;
        border-radius: 6px;
        margin: 15px 0;
    }

    .help-box-title {
        color: var(--india-green);
        font-weight: 600;
        font-size: 14px;
        margin-bottom: 8px;
    }

    .help-box-text {
        color: #666;
        font-size: 13px;
        line-height: 1.6;
    }

    /* Data cards */
    .data-card {
        background: white;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin: 15px 0;
    }

    /* Progress bars */
    .stProgress > div > div > div {
        background-color: var(--india-green);
    }

    /* Buttons */
    .stButton > button {
        background: var(--gov-blue);
        color: white;
        border: none;
        padding: 10px 30px;
        font-weight: 600;
        border-radius: 6px;
        transition: all 0.3s;
    }

    .stButton > button:hover {
        background: var(--gov-dark-blue);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: var(--gov-light-blue);
        padding: 10px;
        border-radius: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        background: white;
        padding: 10px 20px;
        border-radius: 6px;
        color: var(--gov-blue);
        font-weight: 500;
        border: 1px solid #e0e0e0;
    }

    .stTabs [aria-selected="true"] {
        background: var(--gov-blue);
        color: white;
        border: 1px solid var(--gov-blue);
    }
</style>
""", unsafe_allow_html=True)


# Helper functions
@st.cache_data(ttl=3600)
def fetch_states():
    try:
        response = requests.get(f"{API_BASE_URL}/api/states", timeout=10)
        if response.status_code == 200:
            return response.json()["states"]
        return []
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []


@st.cache_data(ttl=3600)
def fetch_districts(state_name):
    try:
        response = requests.get(f"{API_BASE_URL}/api/districts/{state_name}", timeout=10)
        if response.status_code == 200:
            return response.json()["districts"]
        return []
    except:
        return []


@st.cache_data(ttl=1800)
def fetch_district_summary(state_name, district_name):
    try:
        response = requests.get(f"{API_BASE_URL}/api/summary/{state_name}/{district_name}", timeout=15)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


@st.cache_data(ttl=1800)
def fetch_district_data(state_name, district_name, fin_year=None):
    try:
        params = {"fin_year": fin_year} if fin_year else {}
        response = requests.get(
            f"{API_BASE_URL}/api/data/{state_name}/{district_name}",
            params=params,
            timeout=15
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


def format_currency(amount):
    if amount >= 10000000:
        return f"₹{amount / 10000000:.2f} Crore"
    elif amount >= 100000:
        return f"₹{amount / 100000:.2f} Lakh"
    else:
        return f"₹{amount:,.0f}"


def format_number(num):
    if num >= 10000000:
        return f"{num / 10000000:.2f} Cr"
    elif num >= 100000:
        return f"{num / 100000:.2f} L"
    elif num >= 1000:
        return f"{num / 1000:.2f} K"
    else:
        return f"{num:,.0f}"


def create_tooltip_html(key, show_simple=True):
    """Create tooltip HTML with info icon"""
    tooltip = TOOLTIPS.get(key, {})
    en_text = tooltip.get("en", "")
    hi_text = tooltip.get("hi", "")
    simple_text = tooltip.get("simple", "")

    tooltip_text = f"{simple_text}\n\n{hi_text}\n\n{en_text}" if show_simple else f"{hi_text}\n\n{en_text}"

    return f'<span class="info-icon" title="{tooltip_text}">ℹ️</span>'


def get_base64_image(image_path):
    """Convert local image to base64 for HTML embedding"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        print(f"Error: Image not found at {image_path}")
        return None


def main():
    # Load logo image and convert to base64
    logo_base64 = get_base64_image("mgnrega_logo.jpg")

    if logo_base64:
        logo_src = f'data:image/jpeg;base64,{logo_base64}'
    else:
        # Fallback to online image if local file not found
        logo_src = 'https://nrega.nic.in/Netnrega/img/logo.png'

    # Government Header with Blue Background and Logo on Right
    st.markdown(f"""
    <div class='gov-header'>
        <div class='gov-header-content-blue'>
            <div class='gov-title-section'>
                <div style='font-size: 50px;'>🏛️</div>
                <div class='gov-title'>
                    <h1>MAHATMA GANDHI NATIONAL RURAL EMPLOYMENT GUARANTEE SCHEME</h1>
                    <h2>ग्रामीण विकास मंत्रालय | Ministry of Rural Development</h2>
                    <p class='gov-subtitle-white'>Government of India | भारत सरकार</p>
                </div>
            </div>
            <div style='text-align: right;'>
                <img src='{logo_src}' 
                     alt='MGNREGA Logo' 
                     style='width: 120px; height: 120px; object-fit: contain; background: white; padding: 10px; border-radius: 8px;'>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)



    # Check backend
    try:
        health_check = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if health_check.status_code != 200:
            st.error("⚠️ Backend server not responding")
            return
    except:
        st.error("❌ Cannot connect to backend")
        st.code("cd backend && python -m uvicorn main:app --reload --port 8000", language="bash")
        return

    # Session state
    if 'state_selection' not in st.session_state:
        st.session_state.state_selection = None
    if 'district_selection' not in st.session_state:
        st.session_state.district_selection = None

    # About MGNREGA info card
    st.markdown(f"""
    <div class='info-card'>
        <div class='info-card-title'>
            💡 What is MGNREGA? | मनरेगा क्या है?
        </div>
        <div class='info-card-text'>
            {TOOLTIPS['mgnrega_about']['simple']}<br><br>
            <strong>Hindi:</strong> {TOOLTIPS['mgnrega_about']['hi']}<br><br>
            <strong>English:</strong> {TOOLTIPS['mgnrega_about']['en']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Selection Panel
    st.markdown("""
    <div class='selection-panel'>
        <div class='selection-title'>
            📍 Select Your District | अपना जिला चुनें
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Selection dropdowns
    col1, col2, col3 = st.columns([4, 4, 1])

    with col1:
        states = fetch_states()
        if states:
            state_names = ["-- Select State / राज्य चुनें --"] + [s["name"] for s in states]
            current_index = 0
            if st.session_state.state_selection in state_names:
                current_index = state_names.index(st.session_state.state_selection)

            selected_state = st.selectbox(
                "🗺️ State / राज्य",
                state_names,
                index=current_index,
                key="state_selector",
                label_visibility="collapsed"
            )

            if selected_state != st.session_state.state_selection:
                st.session_state.state_selection = selected_state
                st.session_state.district_selection = None
                st.rerun()

    with col2:
        if selected_state and selected_state != "-- Select State / राज्य चुनें --":
            with st.spinner("Loading districts..."):
                districts = fetch_districts(selected_state)

            if districts:
                district_names = ["-- Select District / जिला चुनें --"] + [d["name"] for d in districts]
                current_index = 0
                if st.session_state.district_selection in district_names:
                    current_index = district_names.index(st.session_state.district_selection)

                selected_district = st.selectbox(
                    "🏘️ District / जिला",
                    district_names,
                    index=current_index,
                    key="district_selector",
                    label_visibility="collapsed"
                )

                if selected_district != st.session_state.district_selection:
                    st.session_state.district_selection = selected_district
                    st.rerun()
            else:
                st.selectbox("🏘️ District", ["No districts"], disabled=True, label_visibility="collapsed")
                selected_district = None
        else:
            st.selectbox("🏘️ District", ["Select state first"], disabled=True, label_visibility="collapsed")
            selected_district = None

    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄", help="Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Display data or welcome screen
    if (selected_state and selected_state != "-- Select State / राज्य चुनें --" and
            selected_district and selected_district != "-- Select District / जिला चुनें --"):
        show_district_data(selected_state, selected_district, "2024-2025")
    else:
        show_welcome_screen()

    # NIC Footer (matching official portal)
    show_nic_footer()


def show_welcome_screen():
    """Welcome screen with light saffron background"""
    st.markdown("<br><br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style='background: #FFF4E6; border: 1px solid #FFD699; border-radius: 8px; padding: 40px; text-align: center; box-shadow: 0 2px 8px rgba(255, 153, 51, 0.1);'>
            <h2 style='color: #034EA2; margin-bottom: 20px; display: flex; align-items: center; justify-content: center; gap: 10px;'>
                🙏 <span>Welcome | स्वागत है</span>
            </h2>
            <p style='font-size: 18px; color: #666; line-height: 1.8;'>
                Select your <strong style='color: #FF9933;'>State and District</strong> from above to see<br>
                your district's MGNREGA performance<br><br>
                ऊपर से अपना <strong style='color: #FF9933;'>राज्य और जिला</strong> चुनें<br>
                अपने जिले का मनरेगा प्रदर्शन देखने के लिए
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Rest of your three cards remain the same...

    # Three equal cards with green background like middle box
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style='background: #E8F5E9; border-left: 4px solid #138808; padding: 25px; border-radius: 8px; min-height: 380px; display: flex; flex-direction: column;'>
            <h3 style='color: #034EA2; margin: 0 0 10px 0; display: flex; align-items: center; gap: 10px; font-size: 20px;'>
                📊 What You'll See
            </h3>
            <h4 style='color: #138808; margin: 0 0 20px 0; font-size: 16px;'>
                आप क्या देखेंगे
            </h4>
            <ul style='color: #666; line-height: 2.2; font-size: 14px; flex-grow: 1; margin: 0; padding-left: 20px;'>
                <li><strong>Families Employed</strong><br><span style='color: #138808;'>कितने परिवारों को काम मिला</span></li>
                <li><strong>Daily Wage</strong><br><span style='color: #138808;'>रोज़ की कमाई कितनी है</span></li>
                <li><strong>Work Days</strong><br><span style='color: #138808;'>कितने दिन काम मिला</span></li>
                <li><strong>Women Participation</strong><br><span style='color: #138808;'>महिलाओं की भागीदारी</span></li>
                <li><strong>Work Progress</strong><br><span style='color: #138808;'>काम की प्रगति</span></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style='background: #E8F5E9; border-left: 4px solid #138808; padding: 25px; border-radius: 8px; min-height: 380px; display: flex; flex-direction: column;'>
            <h3 style='color: #138808; margin: 0 0 10px 0; display: flex; align-items: center; gap: 10px; font-size: 20px;'>
                ✅ How to Use
            </h3>
            <h4 style='color: #138808; margin: 0 0 20px 0; font-size: 16px;'>
                कैसे उपयोग करें
            </h4>
            <ol style='color: #666; line-height: 2.2; font-size: 14px; flex-grow: 1; margin: 0; padding-left: 25px;'>
                <li><strong>Select State</strong><br><span style='color: #138808;'>अपना राज्य चुनें</span></li>
                <li><strong>Select District</strong><br><span style='color: #138808;'>अपना जिला चुनें</span></li>
                <li><strong>Data loads automatically</strong><br><span style='color: #138808;'>जानकारी अपने आप दिखेगी</span></li>
                <li><strong>View charts</strong><br><span style='color: #138808;'>Charts देखें</span></li>
                <li><strong>Download report</strong><br><span style='color: #138808;'>Report download करें</span></li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style='background: #E8F5E9; border-left: 4px solid #138808; padding: 25px; border-radius: 8px; min-height: 380px; display: flex; flex-direction: column;'>
            <h3 style='color: #FF6B35; margin: 0 0 10px 0; display: flex; align-items: center; gap: 10px; font-size: 20px;'>
                📞 Need Help?
            </h3>
            <h4 style='color: #FF6B35; margin: 0 0 20px 0; font-size: 16px;'>
                मदद चाहिए?
            </h4>
            <ul style='color: #666; line-height: 2.2; font-size: 14px; list-style: none; padding: 0; flex-grow: 1; margin: 0;'>
                <li style='margin-bottom: 15px;'>
                    <strong>📞 Helpline</strong><br>
                    <span style='color: #138808;'>हेल्पलाइन: 1800-345-6789</span>
                </li>
                <li style='margin-bottom: 15px;'>
                    <strong>🌐 Website</strong><br>
                    <span style='color: #138808;'>वेबसाइट: nrega.nic.in</span>
                </li>
                <li style='margin-bottom: 15px;'>
                    <strong>📧 Email</strong><br>
                    <span style='color: #138808;'>ईमेल: jsit-mord@nic.in</span>
                </li>
                <li style='margin-bottom: 15px;'>
                    <strong>⏰ Availability</strong><br>
                    <span style='color: #138808;'>उपलब्धता: 24x7</span><br>
                </li>
            </ul>
        </div>
        """, unsafe_allow_html=True)


def show_district_data(state_name, district_name, fin_year):
    """Display district data with educational tooltips"""

    with st.spinner("🔄 Loading data..."):
        summary = fetch_district_summary(state_name, district_name)
        detailed_data = fetch_district_data(state_name, district_name, fin_year)

    if not summary or not detailed_data:
        st.error(f"❌ No data available for {district_name}, {state_name}")
        return

    # District Header
    st.markdown(f"""
    <div class='district-header'>
        <h2>📍 {district_name}, {state_name}</h2>
        <p>Latest Data: {summary['latest_month']} {summary['latest_year']} | Financial Year: {fin_year}</p>
    </div>
    """, unsafe_allow_html=True)

    # Key Performance Indicators with Tooltips
    st.markdown("### 📊 Key Indicators | मुख्य संकेतक")

    # Help text explaining the section
    st.markdown("""
    <div class='help-box'>
        <div class='help-box-title'>💡 Hover over the ℹ️ icon to understand what each number means</div>
        <div class='help-box-text'>
            प्रत्येक संख्या का अर्थ समझने के लिए ℹ️ आइकन पर माउस रखें
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    metrics = [
        {
            "col": col1,
            "icon": "👨‍👩‍👧‍👦",
            "label_en": "Families Employed",
            "label_hi": "परिवारों को रोजगार",
            "value": format_number(summary['total_households']),
            "tooltip_key": "families_employed",
            "description": "रोज़गार पाने वाले परिवार"
        },
        {
            "col": col2,
            "icon": "💰",
            "label_en": "Avg. Daily Wage",
            "label_hi": "औसत दैनिक मजदूरी",
            "value": f"₹{summary['avg_wage_rate']}",
            "tooltip_key": "avg_wage",
            "description": "प्रति दिन की कमाई"
        },
        {
            "col": col3,
            "icon": "📅",
            "label_en": "Avg. Work Days",
            "label_hi": "औसत कार्य दिवस",
            "value": f"{summary['avg_days_employment']} days",
            "tooltip_key": "avg_days",
            "description": "कितने दिन काम मिला"
        },
        {
            "col": col4,
            "icon": "💸",
            "label_en": "Total Expenditure",
            "label_hi": "कुल खर्च",
            "value": format_currency(summary['total_expenditure']),
            "tooltip_key": "total_expenditure",
            "description": "कुल पैसा खर्च हुआ"
        }
    ]

    for metric in metrics:
        with metric["col"]:
            tooltip = TOOLTIPS.get(metric["tooltip_key"], {})

            # Create expandable section with tooltip
            with st.expander(f"{metric['icon']} {metric['label_hi']}", expanded=True):
                st.markdown(f"""
                <div style='text-align: center;'>
                    <div class='stat-value'>{metric['value']}</div>
                    <div style='font-size: 12px; color: #999; margin-top: 5px;'>{metric['label_en']}</div>
                </div>
                """, unsafe_allow_html=True)

                st.caption(f"**{tooltip.get('simple', '')}**")
                with st.container():
                    st.markdown(f"**Hindi:** {tooltip.get('hi', '')}", help=tooltip.get('en', ''))

    st.markdown("<br>", unsafe_allow_html=True)

    # Participation Metrics with detailed tooltips
    st.markdown("### 👥 Participation | भागीदारी")

    col1, col2 = st.columns(2)

    with col1:
        women_tooltip = TOOLTIPS["women_participation"]
        st.markdown(f"""
        <div class='data-card'>
            <h4 style='color: #034EA2; margin-bottom: 10px;'>
                👩 Women Participation | महिला भागीदारी
                <span class='info-icon' title='{women_tooltip["simple"]}'>ℹ️</span>
            </h4>
        </div>
        """, unsafe_allow_html=True)

        progress_val = min(summary['women_participation_pct'] / 100, 1.0)
        st.progress(progress_val, text=f"{summary['women_participation_pct']:.1f}%")
        st.caption(f"**{women_tooltip['simple']}**")

        with st.expander("📖 Learn More / और जानें"):
            st.markdown(f"**Hindi:** {women_tooltip['hi']}")
            st.markdown(f"**English:** {women_tooltip['en']}")

    with col2:
        completion_tooltip = TOOLTIPS["completion_rate"]
        st.markdown(f"""
        <div class='data-card'>
            <h4 style='color: #138808; margin-bottom: 10px;'>
                ✅ Work Completion | कार्य पूर्णता
                <span class='info-icon' title='{completion_tooltip["simple"]}'>ℹ️</span>
            </h4>
        </div>
        """, unsafe_allow_html=True)

        progress_val = min(summary['completion_rate'] / 100, 1.0)
        st.progress(progress_val, text=f"{summary['completion_rate']:.1f}%")
        st.caption(f"**{completion_tooltip['simple']}**")

        with st.expander("📖 Learn More / और जानें"):
            st.markdown(f"**Hindi:** {completion_tooltip['hi']}")
            st.markdown(f"**English:** {completion_tooltip['en']}")
            st.markdown(f"Completed: {summary['completed_works']} | Ongoing: {summary['ongoing_works']}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts and data
    df = pd.DataFrame(detailed_data['data'])

    if not df.empty:
        st.markdown("### 📈 Detailed Analysis | विस्तृत विश्लेषण")

        tab1, tab2 = st.tabs(["📊 Monthly Trends | मासिक रुझान", "📋 Data Table | डेटा तालिका"])

        with tab1:
            fig = px.line(
                df, x='month', y='households_worked',
                title='Monthly Employment Trend | मासिक रोज़गार रुझान',
                markers=True
            )
            fig.update_traces(line_color='#034EA2', line_width=3, marker_size=8)
            fig.update_layout(height=400, paper_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)

            st.caption(
                "**What this shows:** Number of families who got work each month | यह दिखाता है: हर महीने कितने परिवारों को काम मिला")

        with tab2:
            st.markdown("#### 📋 Monthly Data | मासिक डेटा")

            display_df = df[['month', 'households_worked', 'avg_wage_rate', 'avg_days_employment']].copy()
            display_df.columns = ['Month\nमहीना', 'Families\nपरिवार', 'Wage\nमज़दूरी', 'Days\nदिन']

            st.dataframe(display_df, use_container_width=True, hide_index=True)

            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Download Report | रिपोर्ट डाउनलोड करें",
                csv,
                f"mgnrega_{district_name}_{fin_year}.csv",
                "text/csv",
                use_container_width=True
            )




def show_nic_footer():
    """NIC-branded footer matching official MGNREGA portal"""
    st.markdown(f"""
    <div class='nic-footer'>
        <div class='footer-content'>
            <div class='footer-section'>
                <h4>OUR POLICIES</h4>
                <ul>
                    <li><a href='https://nrega.nic.in' target='_blank'>Policies</a></li>
                    <li><a href='#'>Privacy Policy</a></li>
                    <li><a href='#'>Terms & Conditions</a></li>
                    <li><a href='#'>Accessibility Statement</a></li>
                    <li><a href='#'>Disclaimer</a></li>
                </ul>
            </div>
            <div class='footer-section'>
                <h4>LINKS</h4>
                <ul>
                    <li><a href='https://nrega.nic.in' target='_blank'>Help</a></li>
                    <li><a href='#'>Contact Us</a></li>
                    <li><a href='#'>Feedback</a></li>
                    <li><a href='#'>Most Often Used Services</a></li>
                    <li><a href='#'>Site Map</a></li>
                </ul>
            </div>
            <div class='footer-section'>
                <h4>CONTACT</h4>
                <ul>
                    <li>📍 <strong>Ministry of Rural Development</strong></li>
                    <li>Govt. of India, Krishi Bhavan</li>
                    <li>Dr. Rajendra Prasad Road</li>
                    <li>New Delhi - 110001, INDIA</li>
                    <li style='margin-top: 15px;'>📞 011-23384707</li>
                    <li>📧 jsit-mord[at]nic[dot]in</li>
                </ul>
            </div>
        </div>
        <div class='footer-bottom'>
            <p>
                Website content is owned & managed by the <strong>Ministry of Rural Development</strong>, Government of India<br>
                Site is designed, developed, hosted and maintained by <strong>National Informatics Centre (NIC)</strong><br>
                © {datetime.now().year} Government of India. All Rights Reserved.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
