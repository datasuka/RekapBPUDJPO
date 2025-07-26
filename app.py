# Revisi penuh pada app.py untuk perbaikan parsing data PEMOTONG/PEMUNGUT (C.1 - C.4) dan format angka
revised_code = """
import streamlit as st
import pdfplumber
import pandas as pd
import re
import base64
from io import BytesIO

def extract_bp_data(text):
    rows = []
    blocks = re.split(r'(?:A\.1|A\. IDENTITAS|Nomor :|Nomor:)', text)
    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Nomor Bukti Potong
        nomor_bp_match = re.search(r'H\.1\s+NOMOR\s+:\s*([0-9]+)', block)
        nomor_bp = nomor_bp_match.group(1).strip() if nomor_bp_match else ""

        # Nama DIPOTONG/DIPUNGUT
        nama_dipotong_match = re.search(r'A\.3\s+Nama\s+:\s*([A-Z0-9 .,\\'’()-]+)', block)
        nama_dipotong = nama_dipotong_match.group(1).strip() if nama_dipotong_match else ""

        # NIK/NPWP DIPOTONG
        nik_dipotong_match = re.search(r'A\.2\s+(?:NPWP|NIK)\s*:\s*([0-9.\s]+)', block)
        nik_dipotong = nik_dipotong_match.group(1).replace(" ", "").replace(".", "") if nik_dipotong_match else ""

        # Masa Pajak (bulan/tahun)
        masa_match = re.search(r'Tanggal\s*([0-9]{2})\s*([0-9]{2})\s*([0-9]{4})', block)
        tgl_faktur = f"{masa_match.group(1)}/{masa_match.group(2)}/{masa_match.group(3)}" if masa_match else ""

        # Kode Objek Pajak
        kode_objek_match = re.search(r'B\.1\s+Kode\s+Objek\s+Pajak\s+:\s*([0-9.]+)', block)
        kode_objek = kode_objek_match.group(1).strip() if kode_objek_match else ""

        # DPP, Tarif, PPh dipotong, dan format angka
        dpp_match = re.search(r'B\.3\s+Dasar Pengenaan Pajak\s+:\s*Rp?\s*([\d,.]+)', block)
        tarif_match = re.search(r'B\.4\s+Tarif\s*\(%\)\s*:\s*([\d,.]+)', block)
        pph_match = re.search(r'B\.5\s+PPh\s+Dipungut/Dipotong\s+:\s*Rp?\s*([\d,.]+)', block)

        dpp = dpp_match.group(1).replace(".", "").replace(",", ".") if dpp_match else ""
        tarif = tarif_match.group(1).replace(",", ".") if tarif_match else ""
        pph = pph_match.group(1).replace(".", "").replace(",", ".") if pph_match else ""

        # Dokumen referensi
        no_dok = re.search(r'B\.7\s+Nomor Dokumen Referensi\s+:\s*([A-Z0-9./-]+)', block)
        nama_dok = re.search(r'B\.8\s+Nama Dokumen\s+:\s*([A-Z0-9 .,\\'’()-]+)', block)

        nomor_dokumen = no_dok.group(1).strip() if no_dok else ""
        nama_dokumen = nama_dok.group(1).strip() if nama_dok else ""

        # PEMOTONG - bagian C.1 s.d C.4
        npwp_pemotong = ""
        nama_wp_pemotong = ""
        tanggal_potong = ""
        nama_penandatangan = ""

        c1 = re.search(r'C\.1\s+NPWP\s*:\s*([0-9 ]+)', block)
        if c1:
            npwp_pemotong = c1.group(1).replace(" ", "").replace(".", "")

        c2 = re.search(r'C\.2\s+Nama Wajib Pajak\s*:\s*(.*)', block)
        if c2:
            nama_wp_pemotong = c2.group(1).strip()

        c3 = re.search(r'C\.3\s+Tanggal\s*:\s*([0-9]{2})\s*([0-9]{2})\s*([0-9]{4})', block)
        if c3:
            tanggal_potong = f"{c3.group(1)}/{c3.group(2)}/{c3.group(3)}"

        c4 = re.search(r'C\.4\s+Nama Penandatangan\s*:\s*(.*?)\s*(?:C\.5|$)', block, re.DOTALL)
        if c4:
            nama_penandatangan = c4.group(1).strip()

        rows.append({
            "Nomor Bukti Potong": nomor_bp,
            "NPWP DIPOTONG/DIPUNGUT": nik_dipotong,
            "Nama DIPOTONG/DIPUNGUT": nama_dipotong,
            "Masa Pajak": tgl_faktur,
            "Kode Objek Pajak": kode_objek,
            "Dasar Pengenaan Pajak": dpp.replace(".", ","),
            "Tarif (%)": tarif.replace(".", ","),
            "PPh dipotong": pph.replace(".", ","),
            "Nomor Dokumen Referensi": nomor_dokumen,
            "Nama Dokumen": nama_dokumen,
            "Nama PEMOTONG/PEMUNGUT": nama_penandatangan,
            "Nama wajib pajak PEMOTONG/PEMUNGUT": nama_wp_pemotong,
            "Tanggal Potong": tanggal_potong,
        })
    return rows

st.set_page_config(page_title="Rekap Bukti Potong DJP", layout="wide")
st.title("Rekap Data Bukti Potong DJP (PDF)")
uploaded_files = st.file_uploader("Upload file PDF", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    all_rows = []
    for uploaded_file in uploaded_files:
        with pdfplumber.open(uploaded_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text(x_tolerance=1) + "\\n"
            data_rows = extract_bp_data(text)
            all_rows.extend(data_rows)

    if all_rows:
        df = pd.DataFrame(all_rows)
        st.dataframe(df, use_container_width=True)

        # Export
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Bukti Potong')
        st.download_button("Download Excel", data=output.getvalue(), file_name="rekap_bukti_potong.xlsx")
"""

with open("/mnt/data/app.py", "w", encoding="utf-8") as f:
    f.write(revised_code)

