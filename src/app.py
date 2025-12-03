import streamlit as st
import pandas as pd
import numpy as np
import requests
import uuid
import altair as alt
import textwrap
import time

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Bangalore Prime | AI Estate",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed" 
)

# --- 2. PREMIUM CSS THEME ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    /* GLOBAL THEME */
    .stApp {
        background: radial-gradient(circle at 50% 10%, #0f0c29 0%, #302b63 50%, #24243e 100%);
        font-family: 'Outfit', sans-serif;
        color: #f0f0f0;
    }
    
    /* CHAT INPUT */
    .stChatInput textarea {
        background-color: rgba(0, 0, 0, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        backdrop-filter: blur(10px);
        border-radius: 15px;
    }
    
    /* REMOVE PADDING/MARGINS */
    .block-container { padding-top: 2rem; padding-bottom: 7rem; }
    
    /* --- GLASS PROPERTY CARD --- */
    .listing-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        margin-bottom: 25px;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        overflow: hidden;
    }
    .listing-card:hover {
        transform: translateY(-5px);
        border-color: #00d2ff;
        box-shadow: 0 15px 50px rgba(0, 210, 255, 0.15);
    }
    
    /* CARD HEADER */
    .card-top {
        background: linear-gradient(90deg, rgba(0,0,0,0.3), transparent);
        padding: 15px 20px;
        display: flex; justify-content: space-between; align-items: center;
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    .card-loc { 
        color: #00d2ff; font-size: 0.8rem; font-weight: 800; 
        letter-spacing: 1.5px; text-transform: uppercase; 
    }
    .card-price { 
        color: #fff; font-size: 1.2rem; font-weight: 800; 
        text-shadow: 0 0 10px rgba(0,0,0,0.5);
    }

    /* CARD BODY */
    .card-content { padding: 20px; }
    .card-title {
        color: #fff; font-size: 1.3rem; font-weight: 600; margin-bottom: 12px;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: block;
    }
    
    /* BADGES */
    .badge-row { display: flex; gap: 8px; margin-bottom: 15px; align-items: center; flex-wrap: wrap; }
    .spec-badge { 
        background: rgba(255, 255, 255, 0.1); color: #ddd; 
        padding: 5px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 500; border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* METRICS */
    .metric-grid {
        display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;
        background: rgba(0,0,0,0.2); padding: 12px; border-radius: 12px;
    }
    .metric-item { text-align: center; }
    .metric-num { font-weight: 800; font-size: 1.1rem; margin-bottom: 2px; display: block; line-height: 1;}
    .metric-lbl { color: #888; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1px; }
    .bar-track { width: 100%; height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px; margin-top: 6px; overflow: hidden; }
    .bar-fill { height: 100%; border-radius: 2px; }

    /* FOOTER BUTTONS */
    .card-actions { display: grid; grid-template-columns: 1fr 1fr; border-top: 1px solid rgba(255,255,255,0.08); }
    .action-btn {
        padding: 14px; text-align: center; text-decoration: none; color: #aaa; font-size: 0.85rem; font-weight: 600; transition: 0.3s; display: block;
    }
    .action-btn:hover { background: rgba(255,255,255,0.1); color: white; }
    .btn-glow { border-left: 1px solid rgba(255,255,255,0.08); color: #00d2ff; }
    .btn-glow:hover { background: rgba(0, 210, 255, 0.1); color: #fff; text-shadow: 0 0 8px rgba(0,210,255,0.8); }
    
    [data-testid="stToolbar"] {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. SESSION & NETWORK CONFIG ---
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "System Online. Connected to Real Estate Intelligence Grid."}]

# --- SIDEBAR FOR NETWORK ---
with st.sidebar:
    st.header("🌐 Network Settings")
    
    # Text input for IP (Using the correct IP you found)
    target_ip = st.text_input("Backend IP Address", value="172.20.10.4", help="Teammate's IP")
    
    # Global API URL
    API_URL = f"http://{target_ip}:8000"
    
    # Connection Test
    if st.button("Ping Server"):
        try:
            r = requests.get(f"{API_URL}/docs", timeout=5) # Increased timeout slightly for ping
            if r.status_code == 200:
                st.success(f"✅ Connected to {target_ip}")
            else:
                st.warning("⚠️ Server reachable but returned error.")
        except:
            st.error("❌ Connection Failed. Check IP and Firewall.")

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
    payload = {
        "user_id": st.session_state.user_id,
        "query": query,
        "top_k": 10
    }
    try:
        # --- IMPORTANT CHANGE: INCREASED TIMEOUT TO 90 SECONDS ---
        response = requests.post(f"{API_URL}/query", json=payload, timeout=90)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"answer": f"⚠️ Server Error: {response.status_code}", "retrieved": []}
    except requests.exceptions.ReadTimeout:
        return {"answer": "⚠️ Server took too long to respond (>90s). The AI is thinking hard!", "retrieved": []}
    except requests.exceptions.ConnectionError:
        return {"answer": f"⚠️ Cannot connect to {API_URL}. Check network.", "retrieved": []}
    except Exception as e:
        return {"answer": f"⚠️ Error: {str(e)}", "retrieved": []}

def render_listing_card(item):
    meta = item.get("metadata", {})
    score = item.get("final_score", 0)
    
    title = meta.get("title", "Unknown Property")
    price_val = meta.get("exact_price", 0)
    price = f"₹{price_val/10000000:.2f} Cr" if price_val > 10000000 else f"₹{price_val/100000:.2f} L"
    
    locality = meta.get("locality", "Bangalore")
    sqft = f"{meta.get('area', 'N/A')} sqft"
    bhk = clean_bhk_string(meta.get("bhk_list"))
    url = meta.get("url", "#")
    maps = meta.get("google_maps_link", "#")
    
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
        <div class="card-title">{title}</div>
        <div class="badge-row">
            <div class="spec-badge">🛏️ {bhk}</div>
            <div class="spec-badge">📐 {sqft}</div>
        </div>
        <div class="metric-grid">
            <div class="metric-item">
                <span class="metric-num" style="color:{c_rec}">{rec_score}</span>
                <span class="metric-lbl">MATCH</span>
                <div class="bar-track"><div class="bar-fill" style="width:{min(rec_score, 100)}%; background:{c_rec};"></div></div>
            </div>
            <div class="metric-item">
                <span class="metric-num" style="color:#fff">{liv_score}</span>
                <span class="metric-lbl">LIVE</span>
                <div class="bar-track"><div class="bar-fill" style="width:{min(liv_score, 100)}%; background:#fff;"></div></div>
            </div>
            <div class="metric-item">
                <span class="metric-num" style="color:{c_inv}">{inv_score}</span>
                <span class="metric-lbl">INVEST</span>
                <div class="bar-track"><div class="bar-fill" style="width:{min(inv_score, 100)}%; background:{c_inv};"></div></div>
            </div>
        </div>
    </div>
    <div class="card-actions">
        <a href="{maps}" target="_blank" class="action-btn">View Map</a>
        <a href="{url}" target="_blank" class="action-btn btn-glow">View Listing</a>
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
            AI-Powered RAG Engine
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
                    # Prepare Chart Data
                    chart_data = []
                    for i in items:
                        meta = i.get("metadata", {})
                        chart_data.append({
                            "title": meta.get("title"),
                            "price": meta.get("exact_price"),
                            "score": i.get("final_score")
                        })
                    df_chart = pd.DataFrame(chart_data)

                    # 1. SCATTER PLOT
                    with st.expander("📊 Market Scatter Plot", expanded=True):
                         chart = alt.Chart(df_chart).mark_circle(size=100).encode(
                            x=alt.X('price', axis=alt.Axis(title='Price (INR)')),
                            y=alt.Y('score', scale=alt.Scale(domain=[50, 100]), axis=alt.Axis(title='Match Score')),
                            color=alt.Color('score', scale=alt.Scale(scheme='viridis')),
                            tooltip=['title', 'price', 'score']
                        ).interactive().properties(height=300)
                         st.altair_chart(chart, use_container_width=True)

                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # 2. LISTING CARDS
                    cols = st.columns(2)
                    for idx, item in enumerate(items):
                        with cols[idx % 2]:
                            card_html = render_listing_card(item)
                            st.markdown(card_html, unsafe_allow_html=True)

# QUICK ACTIONS
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    st.markdown("### ⚡ Quick Actions")
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("📉 Cheapest"):
        st.session_state.messages.append({"role": "user", "content": "Find cheapest properties matching previous search"})
        st.rerun()
    if c2.button("🚀 High Investment"):
        st.session_state.messages.append({"role": "user", "content": "Properties with best investment score"})
        st.rerun()
    if c3.button("🏙️ Whitefield"):
        st.session_state.messages.append({"role": "user", "content": "3BHK in Whitefield"})
        st.rerun()
    if c4.button("🔄 Clear"):
        st.session_state.messages = [{"role": "assistant", "content": "Ready."}]
        st.rerun()

# --- 6. MAIN LOGIC LOOP ---
if prompt := st.chat_input("Ask about location, budget, or investment..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    user_query = st.session_state.messages[-1]["content"]
    
    with st.spinner("Connecting to Neural Grid (This may take ~30s)..."):
        # API Call
        api_response = query_backend_api(user_query)
        
        ai_text = api_response.get("answer", "No response text.")
        retrieved_items = api_response.get("retrieved", [])

        msg_payload = {
            "role": "assistant",
            "content": ai_text,
        }
        if retrieved_items:
            msg_payload["retrieved_data"] = retrieved_items
            
        st.session_state.messages.append(msg_payload)
        st.rerun()
