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
    # 1. SUSUN DATA KEPADA LIST
    blocks_list = []
    for block_id, block_content in data_json.items():
        # Masukkan nama nod sekali (cth: Block_33) untuk rujukan
        block_content['node_name'] = block_id
        blocks_list.append(block_content)
    
    # Susun ikut indeks (terkini di atas sekali)
    blocks_list = sorted(blocks_list, key=lambda x: x['index'], reverse=True)
    
    # Ambil data blok paling terkini (Latest) dan blok sebelumnya (Sedia Ada/Current)
    latest_block = blocks_list[0]
    existing_block = blocks_list[1] if len(blocks_list) > 1 else latest_block

    # --- FUNGSI PARSING PAYLOAD BARU ---
    def parse_slot_status(payload_str):
        status = "UNKNOWN"
        if "Slot:" in payload_str:
            parts = payload_str.split('|')
            for part in parts:
                if "Slot:" in part:
                    # Memecahkan 'Slot:AVAIL' atau 'Slot:OCCU' secara tepat
                    status = part.split(':')[1].strip()
        return status

    # Dapatkan status untuk kedua-dua keadaan
    latest_status = parse_slot_status(latest_block.get('data', ''))
    existing_status = parse_slot_status(existing_block.get('data', ''))

    # --- 2. PAPARAN METRICS SIDE-BY-SIDE ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"🔄 Status Sedia Ada ({existing_block.get('node_name')})")
        if existing_status == "AVAIL":
            st.success("🟢 SLOT P1: AVAILABLE")
        elif existing_status == "OCCU":
            st.error("🔴 SLOT P1: OCCUPIED")
        else:
            st.warning(f"🟡 STATUS: {existing_status}")
            
    with col2:
        st.subheader(f"⚡ Status Paling Terkini ({latest_block.get('node_name')})")
        if latest_status == "AVAIL":
            st.success("🟢 SLOT P1: AVAILABLE")
        elif latest_status == "OCCU":
            st.error("🔴 SLOT P1: OCCUPIED")
        else:
            st.warning(f"🟡 STATUS: {latest_status}")

    st.markdown("---")
    
    # --- 3. JADUAL LOG AUDIT TRAIL ---
    st.subheader("📜 Rantaian Blok Ledger (Audit Trail)")
    table_data = []
    for b in blocks_list:
        ms = b.get('timestamp_realtime', 0)
        t_time = datetime.fromtimestamp(ms / 1000.0).strftime('%d/%m/%Y %I:%M:%S %p') if ms else "N/A"
        
        table_data.append({
            "Nod Induk": b.get('node_name'),
            "Block Index": b.get('index'),
            "Masa Sebenar (MY)": t_time,
            "Jenis Transaksi": b.get('tx_type'),
            "Data Payload": b.get('data'),
            "Current Hash": b.get('current_hash')[:20] + "...",
            "Previous Hash": b.get('previous_hash')[:20] + "..."
        })
        
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True)

else:
    st.info("Menunggu data masuk atau Wi-Fi ESP32 belum disambungkan...")

# 4. AUTO REFRESH DASHBOARD SETIAP 2 SAAT
st.write("⏱️ *Dashboard ini dikemas kini secara automatik setiap 2 saat.*")
st.rerun() if hasattr(st, "rerun") else st.experimental_rerun()
