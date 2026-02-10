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

# 2. Desain Dashboard (Tema Biru Tua & Biru Muda)
st.markdown("""
    <style>
    .stApp { background-color: var(--background-color); }
    
    .main-title { 
        color: #003366; 
        font-size: 30px; 
        font-weight: 800; 
        border-bottom: 4px solid #3399FF; 
        padding-bottom: 10px; 
        margin-bottom: 25px; 
    }
    
    .box-container {
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        min-height: 260px;
    }
    .identitas-bg { background-color: #F8F9FA; border: 2px solid #D1D5DB; }
    .audit-bg { background-color: #FFF9C4; border: 2px solid #FBC02D; }
    
    .inner-header {
        color: #003366;
        font-size: 18px;
        font-weight: 800;
        margin-bottom: 15px;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(0,0,0,0.1);
        text-transform: uppercase;
    }
    
    .lbl { color: var(--text-color); opacity: 0.6; font-size: 11px; font-weight: 800; text-transform: uppercase; margin-bottom: 1px; }
    .val { color: var(--text-color); font-size: 14px; font-weight: 700; margin-bottom: 10px; line-height: 1.4; }
    
    .table-header { 
        color: #003366; 
        font-size: 20px; 
        font-weight: 700; 
        margin-top: 20px; 
        margin-bottom: 15px; 
        border-left: 6px solid #3399FF; 
        padding-left: 15px; 
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-title">📊 BRISLIK Rekapitulasi & Audit</div>', unsafe_allow_html=True)

# --- FUNGSI HELPER ---

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

def safe_text(text):
    if not text: return "-"
    return str(text).encode('ascii', 'ignore').decode('ascii')

# --- FUNGSI EKSPOR ---

def export_excel(id_info, aud_info, df):
    output = io.BytesIO()
    summary_data = [
        ["IDENTITAS DEBITUR", ""],
        ["Nama Lengkap", id_info['nama']],
        ["NIK", id_info['nik']],
        ["Alamat Lengkap", id_info['alamat']],
        ["Tanggal Laporan", id_info['tgl']],
        ["", ""],
        ["SUMMARY AUDIT", ""],
        ["Skor Terburuk", f"Kolektabilitas {aud_info['skor']}"],
        ["Total Plafon", aud_info['plafon']],
        ["Total Kewajiban", aud_info['baki']],
        ["Utilisasi & Kreditur", f"{aud_info['util']} | {aud_info['total_kred']} Lembaga"],
        ["Status Audit", "Verified"],
        ["", ""]
    ]
    df_sum = pd.DataFrame(summary_data)
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_sum.to_excel(writer, index=False, header=False, sheet_name='Audit_SLIK')
        df.to_excel(writer, index=False, startrow=len(summary_data), sheet_name='Audit_SLIK')
    return output.getvalue()

def export_word(id_info, aud_info, df):
    doc = Document()
    section = doc.sections[-1]
    section.orientation = WD_ORIENTATION.LANDSCAPE
    section.page_width, section.page_height = section.page_height, section.page_width

    doc.add_heading('LAPORAN REKAPITULASI & AUDIT BRISLIK', 0)
    
    doc.add_heading('IDENTITAS DEBITUR', level=1)
    doc.add_paragraph(f"Nama Lengkap: {id_info['nama']}\nNIK: {id_info['nik']}\nAlamat Lengkap: {id_info['alamat']}\nTanggal Laporan: {id_info['tgl']}")

    doc.add_heading('SUMMARY AUDIT', level=1)
    doc.add_paragraph(f"Skor Terburuk: Kolektabilitas {aud_info['skor']}\nTotal Plafon: {aud_info['plafon']}\nTotal Kewajiban: {aud_info['baki']}\nUtilisasi: {aud_info['util']}\nTotal Kreditur: {aud_info['total_kred']} Lembaga\nStatus Audit: Verified")

    doc.add_heading('RINCIAN FASILITAS', level=1)
    table = doc.add_table(rows=1, cols=len(df.columns))
    table.style = 'Table Grid'
    for i, col in enumerate(df.columns):
        table.cell(0, i).text = col
    for _, row in df.iterrows():
        row_cells = table.add_row().cells
        for i, val in enumerate(row):
            text_val = str(val)
            if i == 1: text_val = text_val[:35]
            if i == 2: text_val = text_val[:30]
            row_cells[i].text = text_val
    
    out = io.BytesIO()
    doc.save(out)
    return out.getvalue()

def export_pdf(id_info, aud_info, df):
    pdf = FPDF('L', 'mm', 'A4')
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, "LAPORAN REKAPITULASI & AUDIT BRISLIK", ln=True, align='C')
    pdf.ln(5)

    pdf.set_font("Helvetica", 'B', 10)
    pdf.cell(0, 7, "IDENTITAS DEBITUR", ln=True)
    pdf.set_font("Helvetica", size=9)
    pdf.cell(0, 6, safe_text(f"Nama Lengkap: {id_info['nama']} | NIK: {id_info['nik']}"), ln=True)
    pdf.cell(0, 6, safe_text(f"Alamat: {id_info['alamat']}"), ln=True)
    pdf.cell(0, 6, safe_text(f"Tanggal: {id_info['tgl']}"), ln=True)
    pdf.ln(3)

    pdf.set_font("Helvetica", 'B', 10)
    pdf.cell(0, 7, "SUMMARY AUDIT", ln=True)
    pdf.set_font("Helvetica", size=9)
    # Perubahan label "Baki" menjadi "Total Kewajiban"
    pdf.cell(0, 6, safe_text(f"Skor: {aud_info['skor']} | Plafon: {aud_info['plafon']} | Total Kewajiban: {aud_info['baki']}"), ln=True)
    pdf.cell(0, 6, safe_text(f"Utilisasi: {aud_info['util']} | Kreditur: {aud_info['total_kred']} Lembaga"), ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", 'B', 7)
    w = [8, 45, 35, 28, 28, 25, 8, 22, 22, 16, 40] 
    cols = ["NO", "JASA KEUANGAN", "JENIS", "PLAFON", "BAKI DEBET", "DENDA", "KOL", "MULAI", "TEMPO", "BUNGA", "KONDISI"]
    for i, c in enumerate(cols):
        pdf.cell(w[i], 8, c, 1, 0, 'C')
    pdf.ln()
    
    pdf.set_font("Helvetica", size=6)
    for _, r in df.iterrows():
        pdf.cell(w[0], 7, safe_text(r['NO']), 1, 0, 'C')
        pdf.cell(w[1], 7, safe_text(r['NAMA JASA KEUANGAN'])[:35], 1)
        pdf.cell(w[2], 7, safe_text(r['JENIS'])[:30], 1)
        pdf.cell(w[3], 7, safe_text(r['PLAFON']), 1)
        pdf.cell(w[4], 7, safe_text(r['BAKI DEBET']), 1)
        pdf.cell(w[5], 7, safe_text(r['DENDA']), 1)
        pdf.cell(w[6], 7, safe_text(r['KOL']), 1, 0, 'C')
        pdf.cell(w[7], 7, safe_text(r['TGL MULAI']), 1)
        pdf.cell(w[8], 7, safe_text(r['JATUH TEMPO']), 1)
        pdf.cell(w[9], 7, safe_text(r['BUNGA']), 1)
        pdf.cell(w[10], 7, safe_text(r['KONDISI']), 1)
        pdf.ln()
    return bytes(pdf.output())

# 3. Sidebar & Logika Utama
with st.sidebar:
    st.header("⚙️ Menu Utama")
    uploaded_file = st.file_uploader("Unggah File .txt iDEB", type=["txt"])
    st.divider()
    st.caption("Developed by Steffanuel Pranatalie (23081010059) Mhs UPN Veteran Jatim")

if uploaded_file is not None:
    try:
        raw_content = uploaded_file.read().decode("utf-8-sig", errors="ignore")
        data = json.loads(raw_content.strip())
        while isinstance(data, str): data = json.loads(data)

        ind = data.get('individual', {})
        if isinstance(ind, list): ind = ind[0]
        
        data_pokok_list = ind.get('dataPokokDebitur', [{}])
        data_pokok = data_pokok_list[0] if data_pokok_list else {}
        ringkasan = ind.get('ringkasanFasilitas', {})
        header_info = data.get('header', {})

        nama_v = str(data_pokok.get('namaDebitur') or ind.get('parameterPencarian', {}).get('namaDebitur', '-')).upper()
        nik_v = str(data_pokok.get('noIdentitas', '-'))
        alamat_v = str(data_pokok.get('alamat', '-'))
        tgl_v = format_date(header_info.get('tanggalHasil') or ind.get('tanggalPermintaan'))
        
        skor_v = ringkasan.get('kualitasTerburuk', '-')
        plafon_v = float(ringkasan.get('plafonEfektifTotal', 0) or 0)
        baki_v = float(ringkasan.get('bakiDebetTotal', 0) or 0)
        util_v = (baki_v / plafon_v * 100) if plafon_v > 0 else 0
        total_kred = sum([int(ringkasan.get(k, 0) or 0) for k in ['krediturBankUmum', 'krediturBPR/S', 'krediturLp', 'krediturLainnya']])

        col_id, col_aud = st.columns(2)
        with col_id:
            st.markdown(f"""<div class="box-container identitas-bg"><div class="inner-header">👤 Identitas Debitur</div>
                <p class="lbl">Nama Lengkap</p><p class="val">{nama_v}</p>
                <p class="lbl">NIK</p><p class="val">{nik_v}</p>
                <p class="lbl">Alamat Lengkap</p><p class="val">{alamat_v}</p>
                <p class="lbl">Tanggal Laporan</p><p class="val">{tgl_v}</p></div>""", unsafe_allow_html=True)
        with col_aud:
            st.markdown(f"""<div class="box-container audit-bg"><div class="inner-header">🔍 Summary Audit</div>
                <p class="lbl">Skor Terburuk</p><p class="val" style="color:red;">Kolektabilitas {skor_v}</p>
                <p class="lbl">Total Plafon</p><p class="val">{format_rupiah(plafon_v)}</p>
                <p class="lbl">Total Kewajiban</p><p class="val">{format_rupiah(baki_v)}</p>
                <p class="lbl">Utilisasi & Kreditur</p><p class="val">{util_v:.2f}% | {total_kred} Lembaga</p></div>""", unsafe_allow_html=True)

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
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.divider()
            st.subheader("📥 Unduh Laporan")
            b1, b2, b3 = st.columns(3)
            
            id_info = {"nama": nama_v, "nik": nik_v, "alamat": alamat_v, "tgl": tgl_v}
            aud_info = {"skor": skor_v, "plafon": format_rupiah(plafon_v), "baki": format_rupiah(baki_v), "util": f"{util_v:.2f}%", "total_kred": total_kred}

            with b1:
                st.download_button("Excel (.xlsx)", icon="📊", data=export_excel(id_info, aud_info, df), file_name=f"Audit_{nama_v}.xlsx")
            with b2:
                st.download_button("Word (.docx)", icon="📝", data=export_word(id_info, aud_info, df), file_name=f"Audit_{nama_v}.docx")
            with b3:
                if st.button("Generate PDF", icon="⚙️"):
                    try:
                        pdf_bytes = export_pdf(id_info, aud_info, df)
                        st.download_button("Klik Simpan PDF", icon="📕", data=pdf_bytes, file_name=f"Audit_{nama_v}.pdf")
                    except Exception as e:
                        st.error(f"Eror PDF: {e}")
        else:
            st.warning("Data rincian tidak ditemukan.")

    except Exception as e:
        st.error(f"❌ Kesalahan: {e}")
else:
    st.info("Unggah file .txt iDEB untuk memproses dashboard.")
