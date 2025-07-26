import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Rekap Bukti Potong DJP", layout="centered")

st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: white; }
    h1, h2, h3, h4, h5, h6, p, label, .markdown-text-container, .stText, .stMarkdown {
        color: white !important;
    }
    .stButton>button, .stDownloadButton>button {
        background-color: #0070C0;
        color: white !important;
        border-radius: 8px;
        padding: 0.5em 1em;
    }
</style>
""", unsafe_allow_html=True)

st.title("📄 Rekap Bukti Potong DJP ke Excel")

uploaded_files = st.file_uploader("Upload PDF Bukti Potong", type="pdf", accept_multiple_files=True)

def extract_bp_data(text):
    def find(pattern, group=1, default=""):
        m = re.search(pattern, text, re.DOTALL)
        return m.group(group).strip() if m else default

    def extract_date(t):
        m = re.search(r"(\d{2})[\-/ ](\d{2})[\-/ ](\d{4})", t)
        return f"{m.group(1)}/{m.group(2)}/{m.group(3)}" if m else ""

    npwp_dipotong = find(r"A\.1\s+NPWP\s+:\s+([\d ]+)")
    nik_dipotong = find(r"A\.2\s+NIK\s*:?.*?(\d[\d ]{9,})", 1).replace(" ", "")
    nama_dipotong = find(r"A\.3\s+Nama\s+:\s*(.+?)\n")

    if nik_dipotong == "A.3":
        nik_dipotong = ""

    masa_pajak = find(r"(\d{1,2}-\d{4})\s+\d{2}-\d{3}-\d{2}")
    kode_objek = find(r"(\d{2}-\d{3}-\d{2})")
    dpp = find(kode_objek + r"\s+([\d.,]+)", 1)
    tarif = find(rf"{kode_objek}\s+[\d.,]+\s+([\d.,]+)")
    pph = find(rf"{kode_objek}\s+[\d.,]+\s+[\d.,]+\s+([\d.,]+)")
    kena_tarif_lebih_tinggi = "Ya" if "tidak memiliki NPWP" in text.lower() else "Tidak"

    ket_objek = find(r"Keterangan Kode Objek Pajak\s+:\s+(.+)")
    nomor_dok = find(r"Nomor Dokumen\s*:?.*?(\S+)", 1)
    nama_dok = find(r"Nama Dokumen\s+:\s*(.+?)\s+Tanggal")
    tanggal_dok = extract_date(find(r"Nama Dokumen[^\d]*(\d{2}[ /-]\d{2}[ /-]\d{4})"))

    if nomor_dok.lower().startswith("nama"):
        nomor_dok = ""
    if nama_dok.lower().startswith("tanggal"):
        nama_dok = ""

    nomor_faktur = find(r"Nomor Faktur Pajak\s*:\s*(\d{3}\.\d{3}-\d{2}\.\d{8})")
    tanggal_faktur = extract_date(find(r"Faktur Pajak[^\d]*(\d{2}[ /-]\d{2}[ /-]\d{4})"))

    pp23 = find(r"PP Nomor 23 Tahun 2018.*?Nomor\s*:\s*(\S+)")

    npwp_pemotong = find(r"C\.1[^\d]*(\d[\d ]+)")
    nama_wp_pemotong = find(r"C\.2\s+Nama Wajib Pajak\s+:\s*(.+?)\n")
    nama_pemotong = find(r"C\.4\s+Nama Penandatangan\s+:\s*(.+?)\n")
    tanggal_potong = extract_date(find(r"C\.3\s+Tanggal[^\d]*(\d{2}[ /-]\d{2}[ /-]\d{4})"))

    return {
        "Nomor Bukti Potong": find(r"NOMOR\s*:?.*?(\d[\d ]{9,})", 1).replace(" ", ""),
        "Pembetulan ke-": find(r"Pembetulan Ke-\s*(\d+)"),
        "Jenis PPh": "Final" if "PPh Final" in text else "Tidak Final",
        "NPWP DIPOTONG/DIPUNGUT": npwp_dipotong.replace(" ", ""),
        "NIK DIPOTONG/DIPUNGUT": nik_dipotong,
        "Nama DIPOTONG/DIPUNGUT": nama_dipotong.replace(":", "").strip(),
        "Masa Pajak": masa_pajak,
        "Kode objek Pajak": kode_objek,
        "Dasar Pengenaan Pajak": dpp.replace(".", "").replace(",", "."),
        "dikenakan tarif lebih tinggi": kena_tarif_lebih_tinggi,
        "tarif (%)": tarif,
        "PPh dipotong": pph.replace(".", "").replace(",", "."),
        "Keterangan Kode Objek Pajak": ket_objek,
        "Nomor Dokumen Referensi": nomor_dok,
        "Nama Dokumen": nama_dok,
        "Tanggal Dokumen": tanggal_dok,
        "Nomor Faktur Pajak": nomor_faktur,
        "Tanggal Faktur Pajak": tanggal_faktur,
        "SK PP23": pp23,
        "Nama PEMOTONG/PEMUNGUT": nama_pemotong,
        "Nama wajib pajak PEMOTONG/PEMUNGUT": nama_wp_pemotong,
        "Tanggal Potong": tanggal_potong,
        "Nama penandatangan": nama_pemotong
    }

if uploaded_files:
    rows = []
    for file in uploaded_files:
        with pdfplumber.open(file) as pdf:
            full_text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            rows.append(extract_bp_data(full_text))

    df = pd.DataFrame(rows)
    st.markdown("### Data yang berhasil diekstrak:")
    st.dataframe(df)

    buffer = BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
    st.download_button("📥 Download Excel", data=buffer.getvalue(), file_name="rekap_bp_djp.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
