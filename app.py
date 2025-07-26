
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
        if t:
            m = re.search(r"(\d{2})[\-/ ](\d{2})[\-/ ](\d{4})", t)
            return f"{m.group(1)}/{m.group(2)}/{m.group(3)}" if m else t
        return ""

    npwp_dipotong = find(r"A\.1\s+NPWP\s+:\s+([\d ]+)")
    nik_dipotong = find(r"A\.2\s+NIK\s*:?[ \n]+((?:\d\s*){10,})", 1).replace(" ", "")
    nama_dipotong = find(r"A\.3\s+Nama\s+:\s*(.+?)\n")

    if nik_dipotong == "A.3":
        nik_dipotong = ""

    masa_pajak = find(r"(\d{1,2}-\d{4})\s+\d{2}-\d{3}-\d{2}")
    kode_objek = find(r"(\d{2}-\d{3}-\d{2})")
    dpp = find(kode_objek + r"\s+([\d.,]+)", 1)
    tarif = find(r"{}\s+[\d.,]+\s+([\d.]+)".format(kode_objek))
    pph = find(r"{}\s+[\d.,]+\s+[\d.]+\s+([\d.,]+)".format(kode_objek))
    kena_tarif_lebih_tinggi = "Ya" if "memiliki NPWP" in text and "Tidak" in text else "Tidak"

    ket_objek = find(r"Keterangan Kode Objek Pajak\s+:\s+(.+)")
    nomor_dok = find(r"Nomor Dokumen\s*:?[ \n]*([^\n]+)", 1)
    nama_dok = find(r"Nama Dokumen\s+:\s*(.+?)\s+Tanggal")
    tanggal_dok = extract_date(find(r"Nama Dokumen[^\d]*(\d{2}[ /-]\d{2}[ /-]\d{4})"))

    if nomor_dok.lower().startswith("nama"):
        nomor_dok = ""
    if nama_dok.lower().startswith("tanggal"):
        nama_dok = ""

    nomor_faktur = find(r"Nomor Faktur Pajak\s*:\s*(\d{3}\.\d{3}-\d{2}\.\d{8})")
    tanggal_faktur = extract_date(find(r"Faktur Pajak[^\d]*(\d{2})[^\d]?(\d{2})[^\d]?(\d{4})"))

    pp23 = find(r"PP Nomor 23 Tahun 2018.*?Nomor\s*:\s*(\S+)")

    npwp_pemotong = find(r"C\.1\s+NPWP\s+:\s+([\d ]+)")
    nama_wp_pemotong = find(r"C\.2\s+Nama Wajib Pajak\s+:\s+(.+)")
    tanggal_potong = find(r"C\.3\s+Tanggal\s+:\s+(\d{2})\s*(\d{2})\s*(\d{4})")
    if tanggal_potong:
        tanggal_potong = f"{tanggal_potong[0:2]}/{tanggal_potong[2:4]}/{tanggal_potong[4:]}"
    penandatangan = find(r"C\.4\s+Nama Penandatangan\s+:\s+(.+?)\n")

    return {
        "Nomor Bukti Potong": find(r"NOMOR\s*:?\s*((?:\d\s*){10})", 1).replace(" ", ""),
        "Pembetulan ke-": find(r"Pembetulan Ke-\s*([0-9]+)"),
        "Jenis PPh": "Final" if "PPh Final" in text else "Tidak Final",
        "NPWP DIPOTONG/DIPUNGUT": npwp_dipotong.replace(" ", ""),
        "NIK DIPOTONG/DIPUNGUT": nik_dipotong,
        "Nama DIPOTONG/DIPUNGUT": nama_dipotong.replace(":", "").strip(),
        "Masa Pajak": masa_pajak,
        "Kode objek Pajak": kode_objek,
        "Dasar Pengenaan Pajak": dpp.replace(".", "").replace(",", "."),
        "dikenakan tarif lebih tinggi": kena_tarif_lebih_tinggi,
        "tarif (%)": tarif,
        "Pph dipotong": pph.replace(".", "").replace(",", "."),
        "Keterangan Kode Objek Pajak": ket_objek,
        "Nomor Dokumen Referensi": nomor_dok,
        "Nama Dokumen": nama_dok,
        "Tanggal Dokumen": tanggal_dok,
        "Nomor Faktur Pajak": nomor_faktur,
        "Tanggal Faktur Pajak": tanggal_faktur,
        "SK PP23": pp23,
        "Nama PEMOTONG/PEMUNGUT": penandatangan,
        "Nama wajib pajak PEMOTONG/PEMUNGUT": nama_wp_pemotong,
        "Tanggal Potong": tanggal_potong,
        "Nama penandatangan": penandatangan
    }

if uploaded_files:
    rows = []
    for file in uploaded_files:
        with pdfplumber.open(file) as pdf:
            full_text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            rows.append(extract_bp_data(full_text))

    df = pd.DataFrame(rows)
    st.markdown("### Berikut data yang berhasil diekstrak:")
    st.dataframe(df)

    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    st.download_button("📥 Download Excel", data=buffer.getvalue(), file_name="rekap_bp_djp.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
