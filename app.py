import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Set konfigurasi halaman dashboard
st.set_page_config(page_title="Nexus Shield Dashboard", page_icon="🚗", layout="wide")

st.title("🛡️ Nexus Shield - Smart Parking Blockchain Dashboard")
st.subheader("Pemantauan Rantaian Blok & Status Parkir Masa Sebenar")

# Konfigurasi Pautan Firebase Lutfi
FIREBASE_URL = "https://smart-parking-blockchain-default-rtdb.asia-southeast1.firebasedatabase.app/BlockchainLedger.json"
FIREBASE_AUTH = "KtYk6rkMY0IHHO6711hEZfqYZTLuFPHepzBopnIB"

# Fungsi untuk mengambil data terkini (Ambil 5 blok terakhir untuk paparan jadual)
def fetch_latest_data():
    params = {
        "orderBy": '"index"',
        "limitToLast": 5,
        "auth": FIREBASE_AUTH
    }
    try:
        response = requests.get(FIREBASE_URL, params=params)
        if response.status_code == 200 and response.json():
            return response.json()
        return None
    except Exception as e:
        st.error(f"Ralat Sambungan Firebase: {e}")
        return None

# Ambil data dari Firebase
data_json = fetch_latest_data()

if data_json:
    # Susun data JSON daripada format Firebase ke dalam bentuk Senarai Python (List)
    blocks_list = []
    for block_id, block_content in data_json.items():
        blocks_list.append(block_content)
    
    # Susun semula supaya indeks paling tinggi (terkini) berada di atas sekali
    blocks_list = sorted(blocks_list, key=lambda x: x['index'], reverse=True)
    
    # 1. PAPARAN LIVE STATUS (BLOK TERKINI)
    latest_block = blocks_list[0]
    
    # Proses ekstrak pecahan data payload (CardUID, Slot, PIR)
    payload_str = latest_block.get('data', '')
    slot_status = "UNKNOWN"
    card_uid = "NONE"
    
    if "Slot:" in payload_str:
        # Contoh ekstrak: CardUID:a3b2c1|Slot:AVAIL|PIR:0
        parts = payload_str.split('|')
        for part in parts:
            if "Slot:" in part:
                slot_status = part.split(':')[1]
            if "CardUID:" in part:
                card_uid = part.split(':')[1]

    # Cipta 3 Kotak Ringkasan Utama (Metrics)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Nombor Blok Terkini (#)", value=latest_block.get('index'))
        
    with col2:
        if slot_status == "AVAIL":
            st.success("🟢 SLOT P1: AVAILABLE")
        elif slot_status == "OCCU":
            st.error("🔴 SLOT P1: OCCUPIED")
        else:
            st.warning(f"🟡 STATUS: {slot_status}")
            
    with col3:
        # Tukar Epoch Milisaat Firebase kepada Waktu Tempatan Malaysia (Waktu Laptop)
        epoch_ms = latest_block.get('timestamp_realtime', 0)
        if epoch_ms:
            real_time = datetime.fromtimestamp(epoch_ms / 1000.0).strftime('%d/%m/%Y %I:%M:%S %p')
        else:
            real_time = "Tiada Data"
        st.metric(label="Masa Kemaskini Sebenar", value=real_time)

    st.markdown("---")
    
    # 2. PAPARAN JADUAL LEDGER BLOCKCHAIN (5 TRANSAKSI TERAKHIR)
    st.subheader("📜 Rantaian Blok Ledger (Audit Trail)")
    
    # Bina DataFrame untuk jadual yang kemas
    table_data = []
    for b in blocks_list:
        ms = b.get('timestamp_realtime', 0)
        t_time = datetime.fromtimestamp(ms / 1000.0).strftime('%d/%m/%Y %I:%M:%S %p') if ms else "N/A"
        
        table_data.append({
            "Block Index": b.get('index'),
            "Masa Sebenar (MY)": t_time,
            "Jenis Transaksi": b.get('tx_type'),
            "Data Payload": b.get('data'),
            "Current Hash": b.get('current_hash')[:20] + "...",  # Potong sikit bagi muat skrin
            "Previous Hash": b.get('previous_hash')[:20] + "..."
        })
        
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True)

else:
    st.info("Menunggu data masuk atau Wi-Fi ESP32 belum disambungkan...")

# 3. AUTO REFRESH DASHBOARD SETIAP 2 SAAT
st.write("⏱️ *Dashboard ini dikemas kini secara automatik setiap 2 saat.*")
st.rerun() if hasattr(st, "rerun") else st.experimental_rerun()