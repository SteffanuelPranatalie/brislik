import streamlit as st
import pandas as pd
import json
from datetime import datetime

# 1. Konfigurasi Halaman & CSS Custom
st.set_page_config(
    page_title="BRISLIK",
    page_icon="https://upload.wikimedia.org/wikipedia/commons/6/6d/BRI_2025.png?20251217000202",
    layout="wide"
)

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    .main-title { color: #0A3D1C; font-size: 30px; font-weight: 800; border-bottom: 4px solid #4CAF50; padding-bottom: 10px; margin-bottom: 25px; }
    
    /* Styling Kotak Kontainer */
    .box-container {
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        min-height: 260px;
    }
    .identitas-bg { background-color: #F8F9FA; border: 2px solid #D1D5DB; }
    .audit-bg { background-color: #FFF9C4; border: 2px solid #FBC02D; }
    
    /* Judul di DALAM Kotak */
    .inner-header {
        color: #0A3D1C;
        font-size: 18px;
        font-weight: 800;
        margin-bottom: 15px;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(0,0,0,0.1);
        text-transform: uppercase;
    }
    
    /* Label dan Nilai */
    .lbl { color: #6B7280; font-size: 11px; font-weight: 800; text-transform: uppercase; margin-bottom: 1px; }
    .val { color: #111827; font-size: 14px; font-weight: 700; margin-bottom: 10px; line-height: 1.4; }
    
    /* Judul Tabel Luar */
    .table-header { color: #0A3D1C; font-size: 20px; font-weight: 700; margin-top: 20px; margin-bottom: 15px; border-left: 6px solid #4CAF50; padding-left: 15px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-title">📊 BRISLIK Rekapitulasi & Audit</div>', unsafe_allow_html=True)

# 2. Sidebar
with st.sidebar:
    st.header("⚙️ Menu Utama")
    uploaded_file = st.file_uploader("Unggah File .txt iDEB", type=["txt"])
    st.divider()
    st.caption("BRI SLIK Rekapitulasi by Steffanuel Pranatalie (23081010059) Mhs UPN Veteran Jawa Timur")

# Fungsi Format Rupiah (Rp 1.000.000)
def format_rupiah(val):
    try:
        return "Rp " + f"{int(float(val)):,}".replace(",", ".")
    except:
        return "Rp 0"

def format_date(date_str):
    if not date_str or date_str in ["-", "null", ""]: return "-"
    try:
        dt = datetime.strptime(str(date_str)[:8], '%Y%m%d')
        return dt.strftime('%d-%m-%Y')
    except:
        return date_str

if uploaded_file is not None:
    try:
        raw_content = uploaded_file.read().decode("utf-8-sig", errors="ignore")
        data = json.loads(raw_content.strip())
        while isinstance(data, str):
            data = json.loads(data)

        ind = data.get('individual', {})
        if isinstance(ind, list): ind = ind[0]
        
        data_pokok_list = ind.get('dataPokokDebitur', [{}])
        data_pokok = data_pokok_list[0] if data_pokok_list else {}
        ringkasan = ind.get('ringkasanFasilitas', {})
        header_info = data.get('header', {})

        # Persiapan Data Identitas
        nama = (data_pokok.get('namaDebitur') or ind.get('parameterPencarian', {}).get('namaDebitur', '-')).upper()
        nik = data_pokok.get('noIdentitas', '-')
        alamat = data_pokok.get('alamat', '-')
        tgl_lap = format_date(header_info.get('tanggalHasil') or ind.get('tanggalPermintaan'))
        
        # Persiapan Data Audit
        skor = ringkasan.get('kualitasTerburuk', '-')
        kewajiban = float(ringkasan.get('bakiDebetTotal', 0) or 0)
        total_kred = sum([int(ringkasan.get(k, 0) or 0) for k in ['krediturBankUmum', 'krediturBPR/S', 'krediturLp', 'krediturLainnya']])

        # --- TAMPILAN ATAS: 2 KOLOM KOTAK ---
        col_identitas, col_audit = st.columns(2)

        with col_identitas:
            st.markdown(f"""
                <div class="box-container identitas-bg">
                    <div class="inner-header">👤 Identitas Debitur</div>
                    <p class="lbl">Nama Lengkap</p><p class="val">{nama}</p>
                    <p class="lbl">NIK</p><p class="val">{nik}</p>
                    <p class="lbl">Alamat Lengkap</p><p class="val">{alamat}</p>
                    <p class="lbl">Tanggal Laporan</p><p class="val">{tgl_lap}</p>
                </div>
            """, unsafe_allow_html=True)

        with col_audit:
            st.markdown(f"""
                <div class="box-container audit-bg">
                    <div class="inner-header">🔍 Summary Audit</div>
                    <p class="lbl">Skor Terburuk</p><p class="val" style="color:#D32F2F;">Kolektabilitas {skor}</p>
                    <p class="lbl">Total Kewajiban</p><p class="val">{format_rupiah(kewajiban)}</p>
                    <p class="lbl">Total Kreditur</p><p class="val">{total_kred} Lembaga/Bank</p>
                    <p class="lbl">Status Audit</p><p class="val">Verified</p>
                </div>
            """, unsafe_allow_html=True)

        # --- TAMPILAN BAWAH: TABEL FASILITAS ---
        st.markdown('<div class="table-header">RINCIAN FASILITAS DEBITUR</div>', unsafe_allow_html=True)
        
        fas_root = ind.get('fasilitas', {})
        all_fas = []
        if isinstance(fas_root, dict):
            for k in fas_root:
                if isinstance(fas_root[k], list): all_fas.extend(fas_root[k])

        rows = []
        for i, f in enumerate(all_fas, 1):
            rows.append({
                "NO": i,
                "NAMA JASA KEUANGAN": (f.get('ljkKet') or f.get('namaLjk', '-')).upper(),
                "JENIS": f.get('jenisKreditPembiayaanKet') or f.get('jenisKreditKet', '-'),
                "PLAFON": format_rupiah(f.get('plafon', 0)),
                "BAKI DEBET": format_rupiah(f.get('bakiDebet', 0)),
                "DENDA": format_rupiah(f.get('denda', 0)),
                "KOL": f.get('kualitas') or f.get('kolektabilitas', '-'),
                "TGL MULAI": format_date(f.get('tanggalMulai')),
                "JATUH TEMPO": format_date(f.get('tanggalJatuhTempo')),
                "BUNGA": f"{f.get('sukuBungaImbalan') or f.get('sukuBunga', '-')} %",
                "KONDISI": f.get('kondisiKet', '-')
            })
        
        if rows:
            df = pd.DataFrame(rows)
            # Menampilkan dataframe dengan lebar penuh
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.warning("Data rincian tidak ditemukan dalam file.")

    except Exception as e:
        st.error(f"❌ Kesalahan: {e}")

else:
    st.info("Silakan unggah file .txt iDEB untuk memproses dashboard.")
