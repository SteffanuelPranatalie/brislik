import streamlit as st
import pandas as pd
import json
import io
from datetime import datetime

# Import library pendukung
try:
    from docx import Document
    from docx.enum.section import WD_ORIENTATION
    from docx.shared import Inches, Pt
    from fpdf import FPDF
except ImportError:
    st.error("Pustaka pendukung Word/PDF belum terinstal. Jalankan: python -m pip install python-docx fpdf2 openpyxl")

# 1. Konfigurasi Halaman
st.set_page_config(
    page_title="BRISLIK",
    page_icon="https://upload.wikimedia.org/wikipedia/commons/6/6d/BRI_2025.png?20251217000202",
    layout="wide"
)

# 2. Desain Dashboard
st.markdown("""
    <style>
    .stApp { background-color: var(--background-color); }
    .main-title { color: #003366 !important; font-size: 30px; font-weight: 800; border-bottom: 4px solid #3399FF; padding-bottom: 10px; margin-bottom: 25px; }
    .box-container { padding: 20px; border-radius: 12px; margin-bottom: 20px; height: 380px !important; overflow-y: auto; }
    .identitas-bg { background-color: #F8F9FA !important; border: 2px solid #D1D5DB !important; }
    .audit-bg { background-color: #FFF9C4 !important; border: 2px solid #FBC02D !important; }
    .inner-header { color: #003366 !important; font-size: 18px; font-weight: 800; margin-bottom: 15px; border-bottom: 1px solid rgba(0,0,0,0.1); text-transform: uppercase; }
    .lbl { color: #6B7280 !important; font-size: 11px; font-weight: 800; text-transform: uppercase; margin-bottom: 1px; }
    .val { color: #111827 !important; font-size: 14px; font-weight: 700; margin-bottom: 8px; line-height: 1.3; }
    .table-header { color: #003366 !important; font-size: 20px; font-weight: 700; margin-top: 20px; margin-bottom: 15px; border-left: 6px solid #3399FF; padding-left: 15px; }
    .blue-header thead tr th { background-color: #0000FF !important; color: white !important; }
    @media (prefers-color-scheme: dark) {
        .main-title, .table-header { color: #99CCFF !important; }
        .inner-header { color: #003366 !important; }
        .val { color: #111827 !important; }
        .lbl { color: #4B5563 !important; }
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-title">📊 BRISLIK Rekapitulasi & Audit</div>', unsafe_allow_html=True)

# --- FUNGSI HELPER ---
def format_rupiah(val):
    try: return "Rp " + f"{int(float(val)):,}".replace(",", ".")
    except: return "Rp 0"

def format_date(date_str):
    if not date_str or date_str in ["-", "null", ""]: return "-"
    try:
        dt = datetime.strptime(str(date_str)[:8], '%Y%m%d')
        return dt.strftime('%d-%m-%Y')
    except: return date_str

def safe_text(text):
    if not text: return "-"
    return str(text).replace("✔", "V").encode('ascii', 'ignore').decode('ascii')

# --- FUNGSI EKSPOR LENGKAP ---
def export_excel(id_info, aud_info, df):
    output = io.BytesIO()
    summary_data = [
        ["IDENTITAS DEBITUR", ""],
        ["Nama Lengkap", id_info['nama']], ["NIK", id_info['nik']],
        ["Tempat/Tgl Lahir", f"{id_info['tmpt_lahir']}, {id_info['tgl_lahir']}"],
        ["Jenis Kelamin", id_info['jk']], ["NPWP", id_info['npwp']],
        ["Pekerjaan", id_info['pekerjaan']], ["Alamat", id_info['alamat']],
        ["", ""],
        ["SUMMARY AUDIT", ""],
        ["Skor Terburuk", f"Kolektabilitas {aud_info['skor']}"],
        ["Total Plafon", aud_info['plafon']], ["Total Kewajiban", aud_info['baki']],
        ["Utilisasi", aud_info['util']], ["Kreditur", f"{aud_info['total_kred']} Lembaga"],
        ["Posisi Data", aud_info['posisi']], ["Tanggal Laporan", id_info['tgl']],
        ["", ""]
    ]
    df_sum = pd.DataFrame(summary_data)
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_sum.to_excel(writer, index=False, header=False, sheet_name='Audit')
        df.to_excel(writer, index=False, startrow=len(summary_data), sheet_name='Audit')
    return output.getvalue()

def export_word(id_info, aud_info, df):
    doc = Document()
    section = doc.sections[-1]
    section.orientation = WD_ORIENTATION.LANDSCAPE
    section.page_width, section.page_height = section.page_height, section.page_width
    doc.add_heading('LAPORAN REKAPITULASI & AUDIT BRISLIK', 0)
    doc.add_heading('IDENTITAS DEBITUR', level=1)
    doc.add_paragraph(f"Nama: {id_info['nama']}\nNIK: {id_info['nik']}\nTTL: {id_info['tmpt_lahir']}, {id_info['tgl_lahir']}\nJK: {id_info['jk']} | NPWP: {id_info['npwp']}\nPekerjaan: {id_info['pekerjaan']}\nAlamat: {id_info['alamat']}")
    doc.add_heading('SUMMARY AUDIT', level=1)
    doc.add_paragraph(f"Skor: Kolektabilitas {aud_info['skor']}\nTotal Plafon: {aud_info['plafon']}\nTotal Kewajiban: {aud_info['baki']}\nUtilisasi: {aud_info['util']} | Kreditur: {aud_info['total_kred']} Lembaga\nPosisi Data: {aud_info['posisi']}")
    table = doc.add_table(rows=1, cols=len(df.columns)); table.style = 'Table Grid'
    for i, col in enumerate(df.columns): table.cell(0, i).text = col
    for _, row in df.iterrows():
        row_cells = table.add_row().cells
        for i, val in enumerate(row): row_cells[i].text = safe_text(val)[:35]
    out = io.BytesIO(); doc.save(out); return out.getvalue()

def export_pdf(id_info, aud_info, df):
    pdf = FPDF('L', 'mm', 'A4'); pdf.add_page(); pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, f"LAPORAN AUDIT: {id_info['nama']}", ln=True, align='C'); pdf.ln(4)
    pdf.set_font("Helvetica", 'B', 9); pdf.cell(0, 6, "IDENTITAS DEBITUR", ln=True)
    pdf.set_font("Helvetica", size=8)
    pdf.cell(0, 5, safe_text(f"Nama: {id_info['nama']} | NIK: {id_info['nik']} | TTL: {id_info['tmpt_lahir']}, {id_info['tgl_lahir']}"), ln=True)
    pdf.cell(0, 5, safe_text(f"Pekerjaan: {id_info['pekerjaan']} | NPWP: {id_info['npwp']} | JK: {id_info['jk']}"), ln=True)
    pdf.ln(3); pdf.set_font("Helvetica", 'B', 9); pdf.cell(0, 6, "SUMMARY AUDIT", ln=True)
    pdf.set_font("Helvetica", size=8)
    pdf.cell(0, 5, safe_text(f"Skor: Kol {aud_info['skor']} | Plafon: {aud_info['plafon']} | Kewajiban: {aud_info['baki']}"), ln=True)
    pdf.cell(0, 5, safe_text(f"Utilisasi: {aud_info['util']} | Kreditur: {aud_info['total_kred']} Lembaga | Posisi: {aud_info['posisi']}"), ln=True)
    pdf.ln(5); pdf.set_font("Helvetica", 'B', 7)
    w = [8, 30, 55, 35, 15, 15, 25, 15, 30, 30]
    for i, c in enumerate(df.columns): pdf.cell(w[i], 8, safe_text(c), 1, 0, 'C')
    pdf.ln(); pdf.set_font("Helvetica", size=6)
    for _, r in df.iterrows():
        for i, col in enumerate(df.columns): pdf.cell(w[i], 7, safe_text(r[col])[:35], 1, 0, 'L' if i in [1,2] else 'C')
        pdf.ln()
    return bytes(pdf.output())

# 3. Sidebar & Logika Utama
with st.sidebar:
    st.header("⚙️ Menu Utama")
    uploaded_file = st.file_uploader("Unggah File .txt iDEB", type=["txt"])
    st.divider(); st.caption("Developed by Steffanuel Pranatalie (23081010059)")

if uploaded_file is not None:
    try:
        raw_content = uploaded_file.read().decode("utf-8-sig", errors="ignore")
        data = json.loads(raw_content.strip())
        ind = data.get('individual', {}); data_pokok = ind.get('dataPokokDebitur', [{}])[0]
        ringkasan = ind.get('ringkasanFasilitas', {}); header_info = data.get('header', {})

        nama_v = str(data_pokok.get('namaDebitur') or "-").upper()
        nik_v = str(data_pokok.get('noIdentitas', '-'))
        alamat_v = str(data_pokok.get('alamat', '-'))
        tgl_lahir_v = format_date(data_pokok.get('tanggalLahir', '-'))
        tmpt_lahir_v = str(data_pokok.get('tempatLahir', '-')).upper()
        jk_v = str(data_pokok.get('jenisKelaminKet', '-')).upper()
        npwp_v = str(data_pokok.get('npwp', '-'))
        pekerjaan_v = str(data_pokok.get('pekerjaanKet', '-'))
        tgl_laporan_v = format_date(header_info.get('tanggalHasil'))
        
        skor_v = ringkasan.get('kualitasTerburuk', '-')
        plafon_v = float(ringkasan.get('plafonEfektifTotal', 0))
        baki_v = float(ringkasan.get('bakiDebetTotal', 0))
        util_v = (baki_v / plafon_v * 100) if plafon_v > 0 else 0
        total_kred = sum([int(ringkasan.get(k, 0) or 0) for k in ['krediturBankUmum', 'krediturBPR/S', 'krediturLp', 'krediturLainnya']])
        posisi_data_v = str(ind.get('posisiDataTerakhir', '-'))

        col_id, col_aud = st.columns(2)
        with col_id:
            st.markdown(f"""<div class="box-container identitas-bg"><div class="inner-header">👤 Identitas Debitur</div>
                <p class="lbl">Nama Lengkap</p><p class="val">{nama_v}</p>
                <p class="lbl">NIK / NPWP</p><p class="val">{nik_v} / {npwp_v}</p>
                <p class="lbl">TTL / Jenis Kelamin</p><p class="val">{tmpt_lahir_v}, {tgl_lahir_v} | {jk_v}</p>
                <p class="lbl">Pekerjaan</p><p class="val">{pekerjaan_v}</p>
                <p class="lbl">Alamat Lengkap</p><p class="val">{alamat_v}</p></div>""", unsafe_allow_html=True)
        with col_aud:
            st.markdown(f"""<div class="box-container audit-bg"><div class="inner-header">🔍 Summary Audit</div>
                <p class="lbl">Skor Terburuk</p><p class="val" style="color:red !important;">Kolektabilitas {skor_v}</p>
                <p class="lbl">Total Plafon</p><p class="val">{format_rupiah(plafon_v)}</p>
                <p class="lbl">Total Kewajiban</p><p class="val">{format_rupiah(baki_v)}</p>
                <p class="lbl">Utilisasi & Kreditur</p><p class="val">{util_v:.2f}% | {total_kred} Lembaga</p>
                <p class="lbl">Posisi Data Terakhir</p><p class="val">{posisi_data_v}</p></div>""", unsafe_allow_html=True)

        fas_root = ind.get('fasilitas', {})
        all_fas = []
        for k in fas_root:
            if isinstance(fas_root[k], list): all_fas.extend(fas_root[k])

        rows = []
        for i, f in enumerate(all_fas, 1):
            raw_p = str(f.get('jenisPenggunaanKet', '')).lower()
            mapped_p = "KMK" if "modal kerja" in raw_p else ("Investasi" if "investasi" in raw_p else "Konsumsi")
            original_p = f.get('jenisKreditPembiayaanKet') or f.get('jenisKreditKet', '-')

            rows.append({
                "NO": i, "NAMA JASA KEUANGAN": (f.get('ljkKet') or '-').upper(), 
                "JENIS_ORIGINAL": original_p, "JENIS_MAPPED": mapped_p,
                "PLAFON": format_rupiah(f.get('plafon', 0)), "BAKI DEBET": format_rupiah(f.get('bakiDebet', 0)),
                "RAW_BAKI": float(f.get('bakiDebet', 0)), "KOL": str(f.get('kualitas') or '-'),
                "BUNGA": f"{f.get('sukuBungaImbalan', '-')} %", "KONDISI": f.get('kondisiKet', '-'),
                "RESTRUK": "✔" if f.get('tanggalRestrukturisasiAkhir') else "-"
            })
        
        if rows:
            df_full = pd.DataFrame(rows)
            st.markdown('<div class="table-header">PENGATURAN OUTPUT TABEL</div>', unsafe_allow_html=True)
            # PERUBAHAN NAMA FORMAT DISINI
            sel_format = st.radio("Pilih Tampilan:", options=["slik 1 (Default)", "slik 2"], horizontal=True)
            
            c_f1, c_f2, c_f3, c_f4 = st.columns(4)
            with c_f1: sel_bank = st.multiselect("Filter Bank", options=sorted(df_full['NAMA JASA KEUANGAN'].unique()))
            with c_f2: sel_jenis = st.multiselect("Filter Jenis", options=sorted(df_full['JENIS_MAPPED'].unique()))
            with c_f3: sel_kol = st.multiselect("Filter KOL", options=sorted(df_full['KOL'].unique()))
            with c_f4: sel_kondisi = st.multiselect("Filter Kondisi", options=sorted(df_full['KONDISI'].unique()))

            df_f = df_full.copy()
            if sel_bank: df_f = df_f[df_f['NAMA JASA KEUANGAN'].isin(sel_bank)]
            if sel_jenis: df_f = df_f[df_f['JENIS_MAPPED'].isin(sel_jenis)]
            if sel_kol: df_f = df_f[df_f['KOL'].isin(sel_kol)]
            if sel_kondisi: df_f = df_f[df_f['KONDISI'].isin(sel_kondisi)]
            df_f['NO'] = range(1, len(df_f) + 1)

            st.markdown('<div class="table-header">RINCIAN FASILITAS DEBITUR</div>', unsafe_allow_html=True)
            
            if sel_format == "slik 2":
                df_b = df_f.rename(columns={"JENIS_MAPPED": "Jenis Penggunaan", "NAMA JASA KEUANGAN": "Bank/Lembaga pembiayaan", "BAKI DEBET": "OS (Rp)", "KOL": "Kol Terakhir", "BUNGA": "Rate (%)"})
                df_b["Kol terburuk"] = df_b["Kol Terakhir"]; df_b["Jumlah Hari Kol"] = "-"; df_b["Restrukturisasi Ya"] = df_b["RESTRUK"].apply(lambda x: "✔" if x=="✔" else ""); df_b["Restrukturisasi Tidak"] = df_b["RESTRUK"].apply(lambda x: "" if x=="✔" else "✔")
                cols = ["NO", "Jenis Penggunaan", "Bank/Lembaga pembiayaan", "OS (Rp)", "Kol Terakhir", "Kol terburuk", "Jumlah Hari Kol", "Rate (%)", "Restrukturisasi Ya", "Restrukturisasi Tidak"]
                st.markdown('<div class="blue-header">', unsafe_allow_html=True); st.dataframe(df_b[cols], use_container_width=True, hide_index=True); st.markdown('</div>', unsafe_allow_html=True)
                st.markdown(f"""<div style="background-color:#0000FF; color:white; padding:10px; font-weight:bold; text-align:center;">Total Outstanding: {format_rupiah(df_f['RAW_BAKI'].sum())}</div>""", unsafe_allow_html=True)
                df_final = df_b[cols]
            else:
                df_d = df_f.rename(columns={"JENIS_ORIGINAL": "JENIS"})
                df_final = df_d.drop(columns=['RAW_BAKI', 'RESTRUK', 'JENIS_MAPPED']); st.dataframe(df_final, use_container_width=True, hide_index=True)

            st.divider(); st.subheader("📥 Unduh Laporan")
            b1, b2, b3 = st.columns(3)
            id_i = {"nama": nama_v, "nik": nik_v, "alamat": alamat_v, "tgl": tgl_laporan_v, "tmpt_lahir": tmpt_lahir_v, "tgl_lahir": tgl_lahir_v, "jk": jk_v, "npwp": npwp_v, "pekerjaan": pekerjaan_v}
            aud_i = {"skor": skor_v, "plafon": format_rupiah(plafon_v), "baki": format_rupiah(baki_v), "util": f"{util_v:.2f}%", "total_kred": total_kred, "posisi": posisi_data_v}
            with b1: st.download_button("Excel (.xlsx)", icon="📊", data=export_excel(id_i, aud_i, df_final), file_name=f"Audit_{nama_v}.xlsx")
            with b2: st.download_button("Word (.docx)", icon="📝", data=export_word(id_i, aud_i, df_final), file_name=f"Audit_{nama_v}.docx")
            with b3:
                if st.button("Generate PDF", icon="⚙️"):
                    pdf_b = export_pdf(id_i, aud_i, df_final)
                    st.download_button("Klik Simpan PDF", icon="📕", data=pdf_b, file_name=f"Audit_{nama_v}.pdf")
    except Exception as e: st.error(f"❌ Kesalahan: {e}")
else: st.info("Unggah file .txt iDEB untuk memproses.")
