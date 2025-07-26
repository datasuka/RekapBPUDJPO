
# app.py - Streamlit Rekap Bukti Potong DJP ke Excel (Final)
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
        match = re.search(pattern, text)
        return match.group(group).strip() if match else default

    def clean(val):
        return val.replace(".", "").replace(",", ".") if val else ""

    data = {
        "Nomor Bukti potong (h.1)": find(r'NOMOR\s+:?\s*([0-9A-Z\-]+)'),
        "Pembetulan ke- (H.2)": find(r'Pembetulan Ke-?\s*([0-9]+)'),
        "H4. Jenis Pph (Final/tidak final) (h4/h4)": "Final" if "PPh Final" in text else "Tidak Final" if "PPh Tidak Final" in text else "",
        "NPWP DIPOTONG/DIPUNGUT": find(r'A\.1\s+NPWP\s+:?\s*([\d\s]+)').replace(" ", ""),
        "BIK DIPOTONG/DIPUNGUT": find(r'A\.2\s+NIK\s*:?\s*([0-9\-]+)'),
        "Nama DIPOTONG/DIPUNGUT": find(r'A\.3\s+Nama\s+(.+)'),
        "Masa Pajak (b1)": find(r'(\d{1,2}-\d{4})\s+\d{2}-\d{3}-\d{2}'),
        "Kode objek Pajak (b.2)": find(r'(\d{2}-\d{3}-\d{2})'),
        "Dasar Pengenaan Pajak (B.3)": clean(find(r'\d{2}-\d{3}-\d{2}\s+([\d.,]+)')),
        "dikenakan tarif lebih tinggi tidak memiliki NPWP": "Ya" if "Tidak\n    memiliki NPWP" in text else "Tidak",
        "tarif(%) b.5": find(r'([\d.]+)\s+([\d.,]+)\s+V', 1),
        "Pph dipotong B.6": clean(find(r'([\d.]+)\s+([\d.,]+)\s+V', 2)),
        "Keterangan Kode Objek Pajak": find(r'Keterangan Kode Objek Pajak\s+:\s+(.+)'),
        "Nomor Dokumen referensi B.7": find(r'B\.7 Dokumen Referensi\s+:\s+Nomor Dokumen\s+(.+)'),
        "Nama Dokumen": find(r'B\.7.*?Nama Dokumen\s+(.+)', 1),
        "Tanggal Dokumen": find(r'Nama Dokumen\s+Tanggal\s+(\d{2}) (\d{2}) (\d{4})'),
        "Dokumen Referensi untuk Faktur Pajak, apabila ada B.8": find(r'Nomor Faktur Pajak\s*:\s*(\d{3}\.\d{3}-\d{2}\.\d{8})'),
        "Tanggal Faktur Pajak": find(r'(\d{2}) (\d{2}) (\d{4})'),
        "PPh berdasarkan PP Nomor 23 Tahun 2018 (B.11)": find(r'PP Nomor 23 Tahun 2018 dengan Nomor\s+:\s+(.+)'),
        "Nama PEMOTONG/PEMUNGUT": find(r'C\.2\s+:\s+([A-Z .]+)'),
        "Nama wajib pajak PEMOTONG/PEMUNGUT": find(r'C\.2\s+:\s+([A-Z .]+)'),
        "Tanggal Potong": find(r'C\.3\s+Tanggal\s+:\s+dd mm yyyy([0-9 ]{10})'),
        "Nama penandatangan": find(r'C\.4 Nama Penandatangan\s+:\s+(.+)')
    }

    dok_date = re.search(r'Nama Dokumen\s+Tanggal\s+(\d{2}) (\d{2}) (\d{4})', text)
    if dok_date:
        data["Tanggal Dokumen"] = f"{dok_date.group(1)}/{dok_date.group(2)}/{dok_date.group(3)}"

    faktur_date = re.search(r'Faktur Pajak.*?(\d{2}) (\d{2}) (\d{4})', text)
    if faktur_date:
        data["Tanggal Faktur Pajak"] = f"{faktur_date.group(1)}/{faktur_date.group(2)}/{faktur_date.group(3)}"

    potong_date = data["Tanggal Potong"]
    if potong_date and len(potong_date.strip().split()) == 3:
        d, m, y = potong_date.strip().split()
        data["Tanggal Potong"] = f"{d}/{m}/{y}"

    return data

if uploaded_files:
    rows = []
    for file in uploaded_files:
        with pdfplumber.open(file) as pdf:
            full_text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            extracted = extract_bp_data(full_text)
            rows.append(extracted)

    df = pd.DataFrame(rows)
    st.markdown("### Data yang berhasil diekstrak:")
    st.dataframe(df.head(10))

    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    st.download_button("📥 Download Excel", data=buffer.getvalue(), file_name="rekap_bp_djp.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
