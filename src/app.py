import streamlit as st
import pandas as pd
import numpy as np
import requests
import uuid
import altair as alt
import textwrap
import json
import time

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Bangalore Prime | AI Estate",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded" 
)

# --- 2. PREMIUM CSS THEME (FIXED SIDEBAR & TOGGLE) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    /* GLOBAL THEME */
    .stApp {
        background: radial-gradient(circle at 50% 10%, #0f0c29 0%, #302b63 50%, #24243e 100%);
        font-family: 'Outfit', sans-serif;
        color: #f0f0f0;
    }
    
    /* =========================================
       SIDEBAR VISIBILITY & TOGGLE BUTTON FIX
       ========================================= */
    
    /* 1. Sidebar Background & Position */
    section[data-testid="stSidebar"] {
        background-color: #02020a !important; /* Deep solid black-blue */
        border-right: 1px solid rgba(0, 210, 255, 0.3); /* Neon border */
        box-shadow: 5px 0 20px rgba(0,0,0,0.5);
        z-index: 99999 !important; /* Ensure it floats above everything */
    }
    
    /* 2. Push Sidebar Content Down */
    section[data-testid="stSidebar"] .block-container {
        padding-top: 6rem !important; 
    }
    
    /* 3. Force Header/Toolbar to be Transparent (Instead of Hidden) */
    header[data-testid="stHeader"] {
        background: transparent !important;
        z-index: 999 !important;
    }
    
    /* 4. FIX THE TOGGLE BUTTON (The Arrow >) */
    [data-testid="stSidebarCollapsedControl"] {
        display: block !important;
        color: #ffffff !important;
        background-color: rgba(255, 255, 255, 0.1) !important;
        border-radius: 5px;
        margin-top: 10px;
        margin-left: 10px;
        z-index: 100000 !important; /* Ensure clickable */
    }
    
    /* 5. Force White Text in Sidebar */
    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    /* 6. Style Sidebar Inputs */
    section[data-testid="stSidebar"] input {
        background-color: #1a1a2e !important;
        border: 1px solid #444 !important;
        color: white !important;
    }

    /* =========================================
       MAIN UI ELEMENT STYLING
       ========================================= */

    /* CHAT INPUT */
    .stChatInput textarea {
        background-color: rgba(0, 0, 0, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        color: white !important;
        backdrop-filter: blur(10px);
        border-radius: 12px;
    }
    
    /* MAIN AREA PADDING */
    .main .block-container { 
        padding-top: 2rem; 
        padding-bottom: 7rem; 
        max-width: 95% !important;
    }
    
    /* PROPERTY CARD */
    .listing-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        margin-bottom: 25px;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        overflow: hidden;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .listing-card:hover {
        transform: translateY(-5px);
        border-color: #00d2ff;
        box-shadow: 0 15px 50px rgba(0, 210, 255, 0.15);
    }
    
    .card-top {
        background: linear-gradient(90deg, rgba(0,0,0,0.3), transparent);
        padding: 15px 20px;
        display: flex; justify-content: space-between; align-items: center;
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    .card-loc { color: #00d2ff; font-size: 0.8rem; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase; }
    .card-price { color: #fff; font-size: 1.2rem; font-weight: 800; text-shadow: 0 0 10px rgba(0,0,0,0.5); }
    .card-content { padding: 20px; }
    .card-title {
        color: #fff; font-size: 1.2rem; font-weight: 600; margin-bottom: 12px;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block;
    }
    .badge-row { display: flex; gap: 8px; margin-bottom: 15px; align-items: center; flex-wrap: wrap; }
    .spec-badge { 
        background: rgba(255, 255, 255, 0.1); color: #ddd; 
        padding: 5px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 500; border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .metric-grid {
        display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;
        background: rgba(0,0,0,0.2); padding: 12px; border-radius: 12px;
    }
    .metric-item { text-align: center; }
    .metric-num { font-weight: 800; font-size: 1.1rem; margin-bottom: 2px; display: block; line-height: 1;}
    .metric-lbl { color: #aaa; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1px; }
    .bar-track { width: 100%; height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px; margin-top: 6px; overflow: hidden; }
    .bar-fill { height: 100%; border-radius: 2px; }
    .card-actions { border-top: 1px solid rgba(255,255,255,0.08); padding: 0; }
    .action-btn {
        padding: 14px; text-align: center; text-decoration: none; color: #fff; 
        font-size: 0.9rem; font-weight: 600; transition: 0.3s; display: block; width: 100%; background: rgba(0, 210, 255, 0.05);
    }
    .action-btn:hover { background: rgba(0, 210, 255, 0.2); color: #fff; text-shadow: 0 0 8px rgba(0,210,255,0.8); box-shadow: inset 0 0 20px rgba(0,210,255,0.1); }
    
    /* HIDE FOOTER ONLY */
    footer {visibility: hidden;}
    
    </style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "System Online. Connected to Real Estate Intelligence Grid."}]

# ==========================================
#        SIDEBAR: NETWORK & SCORING
# ==========================================
with st.sidebar:
    st.markdown("### 🌐 Network Settings")
    
    target_ip = st.text_input("Backend IP Address", value="127.0.0.1", help="Use 'localhost' or specific IP")
    API_URL = f"http://{target_ip}:8000"
    
    if st.button("Ping Server"):
        try:
            r = requests.get(f"{API_URL}/docs", timeout=5)
            if r.status_code == 200:
                st.success(f"✅ Connected to {target_ip}")
            else:
                st.warning("⚠️ Server reachable but returned error.")
        except:
            st.error("❌ Connection Failed. Check IP.")

    st.markdown("---")
    st.markdown("### 🧠 Scoring Matrix")
    
    # Card 1: Recommendation Score
    st.markdown("""
    <div style="background: rgba(0, 210, 255, 0.1); padding: 15px; border-radius: 12px; border: 1px solid rgba(0, 210, 255, 0.3); margin-bottom: 15px;">
        <div style="display:flex; align-items:center; margin-bottom:8px;">
            <span style="font-size:1.2rem; margin-right:8px;">💎</span>
            <h4 style="color: #00d2ff !important; margin:0; font-size: 1rem; font-weight:800;">REC. SCORE</h4>
        </div>
        <p style="font-size: 0.85rem; color: #e0e0e0 !important; margin: 0; line-height: 1.4;">
            <b>The Master Metric.</b><br>
            A 50/50 balance between <i>Lifestyle Comfort</i> and <i>Financial Potential</i>. High scores (>85) indicate a rare "Unicorn" property.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Card 2: Livability Score
    st.markdown("""
    <div style="background: rgba(255, 255, 255, 0.08); padding: 15px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.2); margin-bottom: 15px;">
        <div style="display:flex; align-items:center; margin-bottom:8px;">
            <span style="font-size:1.2rem; margin-right:8px;">🌱</span>
            <h4 style="color: #ffffff !important; margin:0; font-size: 1rem; font-weight:800;">LIVABILITY</h4>
        </div>
        <p style="font-size: 0.85rem; color: #e0e0e0 !important; margin: 0; line-height: 1.4;">
            <b>Focus: Space & Comfort</b><br>
            Rewards large <b>Carpet Areas</b>, high room counts (3-4 BHK), and premium zones (South/Central). Penalizes small, cramped units.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Card 3: Investment Score
    st.markdown("""
    <div style="background: rgba(241, 196, 15, 0.1); padding: 15px; border-radius: 12px; border: 1px solid rgba(241, 196, 15, 0.3); margin-bottom: 15px;">
        <div style="display:flex; align-items:center; margin-bottom:8px;">
            <span style="font-size:1.2rem; margin-right:8px;">📈</span>
            <h4 style="color: #f1c40f !important; margin:0; font-size: 1rem; font-weight:800;">INVESTMENT</h4>
        </div>
        <p style="font-size: 0.85rem; color: #e0e0e0 !important; margin: 0; line-height: 1.4;">
            <b>Focus: ROI & Growth</b><br>
            Rewards high-growth Tech Zones (East/North), <b>Low Price/Sqft</b>, and highly liquid assets (2-3 BHKs). Penalizes overpricing.
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- 4. HELPER FUNCTIONS ---
def clean_bhk_string(bhk_data):
    if not bhk_data or str(bhk_data) == "nan": return "Plot / Land"
    s = str(bhk_data).replace("[", "").replace("]", "").replace("'", "")
    if not s.strip(): return "Plot / Land"
    return f"{s} BHK"

def get_color(score):
    if score >= 85: return "#00d2ff"
    if score >= 70: return "#f1c40f"
    return "#ff0055"

def query_backend_api(query):
    payload = {"user_id": st.session_state.user_id, "query": query, "top_k": 10}
    try:
        response = requests.post(f"{API_URL}/query", json=payload, timeout=90)
        if response.status_code == 200:
            return response.json()
        return {"answer": f"⚠️ Server Error: {response.status_code}", "retrieved": []}
    except requests.exceptions.ReadTimeout:
        return {"answer": "⚠️ Server took too long to respond (>90s). The AI is thinking hard!", "retrieved": []}
    except requests.exceptions.ConnectionError:
        return {"answer": f"⚠️ Cannot connect to {API_URL}. Is the backend running?", "retrieved": []}
    except Exception as e:
        return {"answer": f"⚠️ Error: {str(e)}", "retrieved": []}

def render_listing_card(item):
    meta = item.get("metadata", {})
    score = item.get("final_score", 0)
    title = meta.get("title", "Unknown Property")
    price_val = meta.get("exact_price", 0)
    try:
        price_float = float(price_val)
        price = f"₹{price_float/10000000:.2f} Cr" if price_float >= 10000000 else f"₹{price_float/100000:.2f} L"
    except:
        price = "Price on Request"
    
    locality = meta.get("locality", "Bangalore")
    sqft = f"{meta.get('area', 'N/A')} sqft"
    bhk = clean_bhk_string(meta.get("bhk_list"))
    url = meta.get("url", "#")
    
    rec_score = round(score, 1)
    liv_score = round(meta.get("livability_score", 0), 1)
    inv_score = round(meta.get("investment_score", 0), 1)
    c_rec = get_color(rec_score)
    c_inv = get_color(inv_score)

    html = f"""
<div class="listing-card">
    <div class="card-top">
        <div class="card-loc">📍 {locality}</div>
        <div class="card-price">{price}</div>
    </div>
    <div class="card-content">
        <div class="card-title" title="{title}">{title}</div>
        <div class="badge-row">
            <div class="spec-badge">🛏️ {bhk}</div>
            <div class="spec-badge">📐 {sqft}</div>
        </div>
        <div class="metric-grid">
            <div class="metric-item">
                <span class="metric-num" style="color:{c_rec}">{rec_score}</span>
                <span class="metric-lbl">REC. SCORE</span>
                <div class="bar-track"><div class="bar-fill" style="width:{min(rec_score, 100)}%; background:{c_rec};"></div></div>
            </div>
            <div class="metric-item">
                <span class="metric-num" style="color:#fff">{liv_score}</span>
                <span class="metric-lbl">LIVABILITY</span>
                <div class="bar-track"><div class="bar-fill" style="width:{min(liv_score, 100)}%; background:#fff;"></div></div>
            </div>
            <div class="metric-item">
                <span class="metric-num" style="color:{c_inv}">{inv_score}</span>
                <span class="metric-lbl">INVESTMENT</span>
                <div class="bar-track"><div class="bar-fill" style="width:{min(inv_score, 100)}%; background:{c_inv};"></div></div>
            </div>
        </div>
    </div>
    <div class="card-actions">
        <a href="{url}" target="_blank" class="action-btn">View Listing</a>
    </div>
</div>
    """
    return textwrap.dedent(html).replace("\n", " ")

# --- 5. UI LAYOUT ---

st.markdown("""
    <div style='text-align: center; margin-bottom: 40px; padding-top: 20px;'>
        <h1 style='font-size: 3rem; margin-bottom: 0; text-shadow: 0 0 20px rgba(0,210,255,0.5);'>
            BANGALORE <span style='color:#00d2ff'>PRIME</span>
        </h1>
        <p style='color: #888; font-size: 1rem; letter-spacing: 2px; text-transform: uppercase;'>
            Powered by Google Gemini & ChromaDB
        </p>
    </div>
""", unsafe_allow_html=True)

# DISPLAY CHAT HISTORY
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"): st.write(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.write(msg["content"])
            
            if "retrieved_data" in msg:
                items = msg["retrieved_data"]
                if items:
                    chart_data = []
                    for i in items:
                        meta = i.get("metadata", {})
                        try:
                            p_val = float(meta.get("exact_price", 0))
                        except:
                            p_val = 0
                        chart_data.append({
                            "title": meta.get("title", "Property"),
                            "price": p_val,
                            "score": i.get("final_score", 0)
                        })
                    
                    if chart_data:
                        df_chart = pd.DataFrame(chart_data)
                        with st.expander("📊 Market Scatter Plot", expanded=True):
                             chart = alt.Chart(df_chart).mark_circle(size=120).encode(
                                x=alt.X('price', axis=alt.Axis(title='Price (INR)', format='~s')),
                                y=alt.Y('score', scale=alt.Scale(domain=[40, 100]), axis=alt.Axis(title='Rec. Score')),
                                color=alt.Color('score', scale=alt.Scale(scheme='viridis'), legend=None),
                                tooltip=['title', 'price', 'score']
                            ).interactive().properties(height=320)
                             st.altair_chart(chart, use_container_width=True)

                    st.markdown("<br>", unsafe_allow_html=True)
                    cols = st.columns(2)
                    for idx, item in enumerate(items):
                        with cols[idx % 2]:
                            st.markdown(render_listing_card(item), unsafe_allow_html=True)

# QUICK ACTIONS
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    st.markdown("### ⚡ Quick Actions")
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("📉 Cheapest Options"):
        st.session_state.messages.append({"role": "user", "content": "Find the cheapest properties matching my last search"})
        st.rerun()
    if c2.button("🚀 High Investment"):
        st.session_state.messages.append({"role": "user", "content": "Show properties with the highest investment score"})
        st.rerun()
    if c3.button("🏙️ Whitefield Areas"):
        st.session_state.messages.append({"role": "user", "content": "Show me 3 BHK apartments in Whitefield"})
        st.rerun()
    if c4.button("🔄 Start Over"):
        st.session_state.messages = [{"role": "assistant", "content": "Ready. Tell me what you are looking for."}]
        st.rerun()

# --- 6. MAIN LOGIC LOOP ---
if prompt := st.chat_input("Ask about location, budget (e.g., '2 BHK in Indiranagar under 1.5 Cr')..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    user_query = st.session_state.messages[-1]["content"]
    with st.spinner("Connecting to Neural Grid... (This may take a moment)"):
        api_response = query_backend_api(user_query)
        ai_text = api_response.get("answer", "No response text.")
        retrieved_items = api_response.get("retrieved", [])
        msg_payload = {"role": "assistant", "content": ai_text}
        if retrieved_items:
            msg_payload["retrieved_data"] = retrieved_items
        st.session_state.messages.append(msg_payload)
        st.rerun()