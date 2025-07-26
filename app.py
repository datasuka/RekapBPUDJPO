
import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Rekap Bukti Potong DJP", layout="wide")

def extract_bp_data(text):
    def extract_with_regex(pattern, default=""):
        m = re.search(pattern, text, re.DOTALL)
        return m.group(1).strip() if m else default

    npwp_dipotong = extract_with_regex(r"A\.1\s+NPWP\s+:\s+([\d\.-]+)")
    nik_dipotong = extract_with_regex(r"A\.2\s+NIK\s+:\s+([\d\.-]+)")
    nama_dipotong = extract_with_regex(r"A\.3\s+Nama\s+:\s+([A-Z0-9 ,.\-']+)")
    if nama_dipotong.startswith(":"):
        nama_dipotong = nama_dipotong[1:].strip()

    masa_pajak = extract_with_regex(r"Masa Pajak.*?([0-9]{2})\s+([0-9]{2})\s+([0-9]{4})")
    masa_pajak_final = f"{masa_pajak}" if masa_pajak else ""

    kode_objek = extract_with_regex(r"B\.1\s+Kode\s+Objek\s+Pajak\s+:\s+(\d+)")
    dasar_pengenaan = extract_with_regex(r"B\.3\s+Dasar\s+Pengenaan\s+Pajak\s+:\s+Rp([\d\.]+)")
    tarif = extract_with_regex(r"B\.4\s+Tarif\s+:\s+([\d\.,]+)%")
    pph_dipotong = extract_with_regex(r"B\.5\s+PPh\s+Dipungut\s+:\s+Rp([\d\.]+)")

    # replace . with , and remove thousand separator for decimals
    dasar_pengenaan = dasar_pengenaan.replace(".", ",") if dasar_pengenaan else ""
    tarif = tarif.replace(".", ",") if tarif else ""
    pph_dipotong = pph_dipotong.replace(".", ",") if pph_dipotong else ""

    no_dok_ref = extract_with_regex(r"B\.7\s+Nomor\s+Dokumen\s+Referensi\s+:\s+([\w\-/]+)")
    nama_dok_ref = extract_with_regex(r"B\.8\s+Nama\s+Dokumen\s+:\s+([\w\s\-/]+)")
    tgl_faktur = extract_with_regex(r"B\.9\s+Tanggal\s+Faktur\s+Pajak\s+:\s+(\d{2})\s+(\d{2})\s+(\d{4})")
    tanggal_faktur = f"{tgl_faktur}" if tgl_faktur else ""

    npwp_pemotong = extract_with_regex(r"C\.1\s+NPWP\s+:\s+([\d\.-]+)")
    nama_wp_pemotong = extract_with_regex(r"C\.2\s+Nama\s+Wajib\s+Pajak\s+:\s+([\w\s\-&]+)")
    tgl_potong = extract_with_regex(r"C\.3\s+Tanggal\s+:\s+(\d{2})\s+(\d{2})\s+(\d{4})")
    tanggal_potong = f"{tgl_potong}" if tgl_potong else ""

    penandatangan = extract_with_regex(r"C\.4\s+Nama\s+Penandatangan\s+:\s+([A-Z ]+)")
    return {
        "NPWP DIPOTONG/DIPUNGUT": npwp_dipotong,
        "NIK DIPOTONG/DIPUNGUT": nik_dipotong,
        "Nama DIPOTONG/DIPUNGUT": nama_dipotong,
        "Masa Pajak": masa_pajak_final,
        "Kode objek Pajak": kode_objek,
        "Dasar Pengenaan Pajak": dasar_pengenaan,
        "tarif (%)": tarif,
        "PPh dipotong": pph_dipotong,
        "Nomor Dokumen Referensi": no_dok_ref,
        "Nama Dokumen": nama_dok_ref,
        "Tanggal Faktur Pajak": tanggal_faktur,
        "Nama PEMOTONG/PEMUNGUT": penandatangan,
        "Nama wajib pajak PEMOTONG/PEMUNGUT": nama_wp_pemotong,
        "Tanggal Potong": tanggal_potong,
        "Nama penandatangan": penandatangan
    }

st.title("Rekap Data Bukti Potong DJP")

uploaded_files = st.file_uploader("Upload file PDF", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    rows = []
    for file in uploaded_files:
        with pdfplumber.open(file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        data = extract_bp_data(text)
        rows.append(data)

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)

    to_excel = BytesIO()
    df.to_excel(to_excel, index=False, engine='openpyxl')
    st.download_button("Download Excel", data=to_excel.getvalue(), file_name="Rekap_BP_DJP.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
