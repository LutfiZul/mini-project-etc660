import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time
import base64
import os

# Set page layout configuration
st.set_page_config(page_title="Nexus Shield Dashboard", page_icon="🚗", layout="wide")

# --- FUNCTION TO CONVERT LOCAL IMAGE TO BASE64 ---
def get_base64_of_local_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

# Convert Background.jpeg to base64 string
bin_str = get_base64_of_local_image("Background.jpeg")

# --- INJECT CUSTOM CSS FOR BACKGROUND ---
if bin_str:
    page_bg_img = f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: url("data:image/jpeg;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    /* Make headers and background containers legible over custom images */
    [data-testid="stHeader"] {{
        background: rgba(0,0,0,0);
    }}
    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)

st.title("🛡️ Nexus Shield - Smart Parking Blockchain Dashboard")
st.subheader("Real-Time Blockchain Ledger & Parking Status Monitoring")

# Firebase Configuration Setup
FIREBASE_URL = "https://smart-parking-blockchain-default-rtdb.asia-southeast1.firebasedatabase.app/BlockchainLedger.json"
FIREBASE_AUTH = "KtYk6rkMY0IHHO6711hEZfqYZTLuFPHepzBopnIB"

# Initialize session state to store the last known block index count
if 'last_block_count' not in st.session_state:
    st.session_state.last_block_count = 0

# Function to pull ALL data from Firebase without any filters
def fetch_all_data():
    # Pass auth inside params just like MIT App Inventor URL setup
    params = {
        "auth": FIREBASE_AUTH
    }
    try:
        response = requests.get(FIREBASE_URL, params=params)
        if response.status_code == 200 and response.json():
            return response.json()
        return None
    except Exception as e:
        return None

# Function to parse data payload string (Extracts CardUID, Slot, PIR)
def parse_slot_status(payload_str):
    status = "UNKNOWN"
    if "Slot:" in payload_str:
        parts = payload_str.split('|')
        for part in parts:
            if "Slot:" in part:
                status = part.split(':')[1].strip()
    return status

# Fetch all historical and live data from Firebase
data_json = fetch_all_data()

if data_json:
    # 1. ORGANIZE JSON DATA INTO A PYTHON LIST
    blocks_list = []
    
    # Handle both list and dict structures from Firebase safely
    if isinstance(data_json, list):
        for idx, block_content in enumerate(data_json):
            if block_content: # Skip null entries if any
                block_content['node_name'] = f"Block_{idx}"
                blocks_list.append(block_content)
    elif isinstance(data_json, dict):
        for block_id, block_content in data_json.items():
            if isinstance(block_content, dict):
                block_content['node_name'] = block_id
                blocks_list.append(block_content)

    if blocks_list:
        # Sort blocks by index descending so the latest block is always at the top
        blocks_list = sorted(blocks_list, key=lambda x: x.get('index', 0), reverse=True)
        
        latest_block = blocks_list[0]
        existing_block = blocks_list[1] if len(blocks_list) > 1 else latest_block
        
        current_block_count = len(blocks_list)

        # Smart Toast Alert: Triggers only when the database size increases
        if current_block_count > st.session_state.last_block_count and st.session_state.last_block_count != 0:
            st.toast(f"🔔 New Block Minted! Total Blocks: {current_block_count}", icon="ℹ️")
        st.session_state.last_block_count = current_block_count

        # 2. DISPLAY STATUS METRICS SIDE-BY-SIDE
        col1, col2 = st.columns(2)
        
        latest_status = parse_slot_status(latest_block.get('data', ''))
        existing_status = parse_slot_status(existing_block.get('data', ''))

        with col1:
            st.subheader(f"🔄 Current Existing Status ({existing_block.get('node_name')})")
            if existing_status == "AVAIL":
                st.success("🟢 SLOT P1: AVAILABLE")
            elif existing_status == "OCCU":
                st.error("🔴 SLOT P1: OCCUPIED")
            else:
                st.warning(f"🟡 STATUS: {existing_status}")
                
        with col2:
            st.subheader(f"⚡ Latest Updated Status ({latest_block.get('node_name')})")
            if latest_status == "AVAIL":
                st.success("🟢 SLOT P1: AVAILABLE")
            elif latest_status == "OCCU":
                st.error("🔴 SLOT P1: OCCUPIED")
            else:
                st.warning(f"🟡 STATUS: {latest_status}")

        st.markdown("---")
        
        # 3. BLOCKCHAIN LEDGER AUDIT TRAIL DATA GRID (SHOW ALL)
        st.subheader(f"📜 Complete Blockchain Ledger Logs ({current_block_count} Blocks)")
        table_data = []
        for b in blocks_list:
            ms = b.get('timestamp_realtime', 0)
            t_time = datetime.fromtimestamp(ms / 1000.0).strftime('%d/%m/%Y %I:%M:%S %p') if ms else "N/A"
            
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
        st.info("Database path is empty. Please check your Firebase node structure.")
else:
    st.info("Awaiting entry logs... Check your database credentials or network connection status.")

# 4. BACKGROUND REFRESH CONTROLLER
time.sleep(2)
st.rerun()
