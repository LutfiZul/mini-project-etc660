import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import base64
import os

# Set page layout configuration
st.set_page_config(page_title="Nexus Shield Dashboard", page_icon="🚗", layout="wide")

# --- INITIALIZE AUTHENTICATION STATE ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_logged_in' not in st.session_state:
    st.session_state.user_logged_in = ""

# --- FUNCTION TO CONVERT LOCAL IMAGE TO BASE64 ---
def get_base64_of_local_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

# Convert Background.jpeg to base64 string
bin_str = get_base64_of_local_image("Background.jpeg")

# --- INJECT CUSTOM CSS FOR DARKENED BACKGROUND ---
if bin_str:
    page_bg_img = f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), url("data:image/jpeg;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    [data-testid="stHeader"] {{
        background: rgba(0,0,0,0);
    }}
    /* Style for compact parking grid blocks */
    .parking-block {{
        padding: 10px;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
        font-size: 14px;
        margin-bottom: 10px;
        color: white;
    }}
    .avail-block {{ background-color: rgba(40, 167, 69, 0.2); border: 1px solid #28a745; }}
    .occu-block {{ background-color: rgba(220, 53, 69, 0.2); border: 1px solid #dc3545; }}
    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)

# Firebase Configuration Setup
FIREBASE_URL = "https://smart-parking-blockchain-default-rtdb.asia-southeast1.firebasedatabase.app/BlockchainLedger.json"
TELEMETRY_URL = "https://smart-parking-blockchain-default-rtdb.asia-southeast1.firebasedatabase.app/LiveTelemetry.json"
FIREBASE_AUTH = "KtYk6rkMY0IHHO6711hEZfqYZTLuFPHepzBopnIB"

if 'last_block_count' not in st.session_state:
    st.session_state.last_block_count = 0

# Data Retrieval Functions
def fetch_all_data():
    params = {"auth": FIREBASE_AUTH}
    try:
        response = requests.get(FIREBASE_URL, params=params)
        if response.status_code == 200 and response.json():
            return response.json()
        return None
    except Exception as e:
        return None

def fetch_live_telemetry():
    params = {"auth": FIREBASE_AUTH}
    try:
        response = requests.get(TELEMETRY_URL, params=params)
        if response.status_code == 200 and response.json():
            return response.json()
        return None
    except Exception as e:
        return None

def parse_slot_status(payload_str):
    status = "UNKNOWN"
    if "Slot:" in payload_str:
        parts = payload_str.split('|')
        for part in parts:
            if "Slot:" in part:
                status = part.split(':')[1].strip()
    return status

# Fetch Data
data_json = fetch_all_data()
live_telemetry = fetch_live_telemetry()

# --- SIDEBAR AUTHENTICATION INTERFACE (UPPER LEFT) ---
st.sidebar.markdown("## 🔒 Nexus Shield Auth")

if not st.session_state.authenticated:
    st.sidebar.info("Please sign in to access the Secure Blockchain Ledger Logs.")
    user_select = st.sidebar.selectbox("Security Personnel", ["Lutfi", "Thia", "Raziq"])
    input_password = st.sidebar.text_input("Access Password", type="password", placeholder="Enter credentials")
    
    if st.sidebar.button("Authenticate Identity", use_container_width=True):
        if input_password == "nexus2026":
            st.session_state.authenticated = True
            st.session_state.user_logged_in = user_select
            st.sidebar.success(f"Welcome back, Operator {user_select}!")
            time.sleep(0.5)
            st.rerun()
        else:
            st.sidebar.error("Invalid Security Token Password!")
else:
    st.sidebar.success(f"🟢 Authenticated: {st.session_state.user_logged_in}")
    if st.sidebar.button("Log Out 🔓", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user_logged_in = ""
        st.rerun()


# --- MAIN UI DISPLAY ---
st.title("🛡️ Nexus Shield - Smart Parking Dashboard")
st.markdown("---")

# --- PUBLIC SECTION: ACCESSIBLE TO EVERYONE ---
st.subheader("📊 Live Parking Status Grid (P1 - P50)")

if live_telemetry and "status" in live_telemetry:
    p1_status = live_telemetry["status"]
else:
    p1_status = "AVAIL"

# 1. Base simulated occupied slots (Excluding P1 entirely)
simulated_occu_slots = {2, 5, 12, 18, 24, 35, 42}

# 2. Dynamic check for Live Slot 1
if p1_status == "OCCU":
    active_occupied_set = simulated_occu_slots.union({1})
else:
    active_occupied_set = simulated_occu_slots

# Calculate counters based on the active set
total_occupied = len(active_occupied_set)
total_available = 50 - total_occupied

# Summary Dashboard Metrics
m_col1, m_col2, m_col3 = st.columns(3)
with m_col1:
    st.metric("Total Capacity", "50 Slots")
with m_col2:
    st.metric("Occupied Lots", f"{total_occupied} Slots")
with m_col3:
    st.metric("Available Lots", f"{total_available} Slots")

st.markdown("<br>", unsafe_allow_html=True)

# 🏢 GENERATE 5x10 GRID LAYOUT
cols_per_row = 10
for row_idx in range(0, 50, cols_per_row):
    grid_cols = st.columns(cols_per_row)
    for col_idx in range(cols_per_row):
        slot_number = row_idx + col_idx + 1
        
        label = "P1 (LIVE)" if slot_number == 1 else f"P{slot_number}"
            
        with grid_cols[col_idx]:
            if slot_number in active_occupied_set:
                st.markdown(f"<div class='parking-block occu-block'>🔴 {label}<br>OCCUPIED</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='parking-block avail-block'>🟢 {label}<br>AVAILABLE</div>", unsafe_allow_html=True)

st.markdown("---")

# --- CONDITIONAL DISPLAY SECTION ---
if st.session_state.authenticated:
    # --- PRIVATE ADMIN VIEW: BLOCKCHAIN AUDIT LOGS ---
    st.subheader("📜 Secure Blockchain Ledger Audits")
    
    if data_json:
        blocks_list = []
        if isinstance(data_json, list):
            for idx, block_content in enumerate(data_json):
                if block_content: 
                    block_content['node_name'] = f"Block_{idx}"
                    blocks_list.append(block_content)
        elif isinstance(data_json, dict):
            for block_id, block_content in data_json.items():
                if isinstance(block_content, dict):
                    block_content['node_name'] = block_id
                    blocks_list.append(block_content)

        if blocks_list:
            blocks_list = sorted(blocks_list, key=lambda x: x.get('index', 0), reverse=True)
            current_block_count = len(blocks_list)

            if current_block_count > st.session_state.last_block_count and st.session_state.last_block_count != 0:
                st.toast(f"🔔 New Block Minted! Total Blocks: {current_block_count}", icon="ℹ️")
            st.session_state.last_block_count = current_block_count

            table_data = []
            for b in blocks_list:
                ms = b.get('timestamp_realtime', 0)
                if ms:
                    utc_time = datetime.fromtimestamp(ms / 1000.0)
                    myt_time = utc_time + timedelta(hours=8)
                    t_time = myt_time.strftime('%d/%m/%Y %I:%M:%S %p')
                else:
                    t_time = "N/A"
                
                table_data.append({
                    "Parent Node": b.get('node_name'),
                    "Block Index": b.get('index'),
                    "Timestamp (MY)": t_time,
                    "Transaction Type": b.get('tx_type'),
                    "Data Payload": b.get('data'),
                    "Current Hash": b.get('current_hash', '')[:20] + "...",
                    "Previous Hash": b.get('previous_hash', '')[:20] + "..."
                })
                
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Ledger tree contains no block elements.")
    else:
        st.info("Connecting to secure blockchain cluster nodes...")
else:
    st.warning("🔒 Restricted Console Area. Please authenticate identity parameters via the sidebar menu to unlock cryptographic network transaction histories.")

# 4. BACKGROUND REFRESH CONTROLLER
time.sleep(2)
st.rerun()
