import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

# Set page layout configuration
st.set_page_config(page_title="Nexus Shield Dashboard", page_icon="🚗", layout="wide")

st.title("🛡️ Nexus Shield - Smart Parking Blockchain Dashboard")
st.subheader("Real-Time Blockchain Ledger & Parking Status Monitoring")

# Firebase Configuration Setup
FIREBASE_URL = "https://smart-parking-blockchain-default-rtdb.asia-southeast1.firebasedatabase.app/BlockchainLedger.json"
FIREBASE_AUTH = "KtYk6rkMY0IHHO6711hEZfqYZTLuFPHepzBopnIB"

# Initialize session state to store the last known block index
if 'last_block_index' not in st.session_state:
    st.session_state.last_block_index = -1

# Function to pull data from Firebase using secure Request Headers
def fetch_latest_data():
    headers = {
        "Authorization": f"Bearer {FIREBASE_AUTH}"
    }
    params = {
        "orderBy": '"index"',
        "limitToLast": 5
    }
    try:
        response = requests.get(FIREBASE_URL, params=params, headers=headers)
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

# Fetch current live data from Firebase database
data_json = fetch_latest_data()

if data_json:
    # 1. ORGANIZE JSON DATA INTO A PYTHON LIST
    blocks_list = []
    for block_id, block_content in data_json.items():
        # Inject the Firebase parent node name (e.g., Block_33) for UI references
        block_content['node_name'] = block_id
        blocks_list.append(block_content)
    
    # Sort blocks by index descending (latest block on top)
    blocks_list = sorted(blocks_list, key=lambda x: x['index'], reverse=True)
    
    latest_block = blocks_list[0]
    existing_block = blocks_list[1] if len(blocks_list) > 1 else latest_block
    
    current_highest_index = latest_block.get('index', 0)

    # Smart Alert: Triggers only when a brand new block index is caught
    if current_highest_index > st.session_state.last_block_index:
        st.toast(f"🔔 New Block Detected: #{current_highest_index}! Dashboard updated.", icon="ℹ️")
        st.session_state.last_block_index = current_highest_index

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
    
    # 3. BLOCKCHAIN LEDGER AUDIT TRAIL DATA GRID
    st.subheader("📜 Blockchain Ledger Logs (Audit Trail)")
    table_data = []
    for b in blocks_list:
        ms = b.get('timestamp_realtime', 0)
        # Convert Epoch Milliseconds to Malaysia Local Standard Time
        t_time = datetime.fromtimestamp(ms / 1000.0).strftime('%d/%m/%Y %I:%M:%S %p') if ms else "N/A"
        
        table_data.append({
            "Parent Node": b.get('node_name'),
            "Block Index": b.get('index'),
            "Timestamp (MY)": t_time,
            "Transaction Type": b.get('tx_type'),
            "Data Payload": b.get('data'),
            "Current Hash": b.get('current_hash')[:20] + "...",
            "Previous Hash": b.get('previous_hash')[:20] + "..."
        })
        
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True)

else:
    st.info("Awaiting entry logs... Check your hardware connection or ESP32 Wi-Fi configuration status.")

# 4. SMART BACKGROUND DATA POLLING TIMING CONTROL
time.sleep(2)
st.rerun()
