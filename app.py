
import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Rekap Bukti Potong DJP", layout="wide")

def extract_data(text):
    def get(pattern, default=""):
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else default

    nomor_bp = get(r"H\.1\s+NOMOR\s+:\s*([0-9]+)")
    pembetulan = get(r"H\.2\s+PEMBETULAN\s+KE\s+:\s*([0-9]+)", "0")
    jenis_pph = get(r"H\.4\s+JENIS\s+PPh.*?:\s*(.*?)\n")

    npwp_dipotong = get(r"A\.1\s+NPWP\s+:\s*([0-9\.\-]+)")
    nik_dipotong = get(r"A\.2\s+NIK\s+:\s*([0-9\.\-]+)")
    nama_dipotong = get(r"A\.3\s+Nama\s+:\s*([A-Z0-9 .,\-']+)")
    masa_pajak = get(r"Masa\s+Pajak.*?(\d{2})\s+(\d{2})\s+(\d{4})")
    masa_final = ""
    if masa_pajak:
        parts = re.findall(r"\d{2,4}", masa_pajak)
        if len(parts) == 3:
            masa_final = f"{parts[1]}-{parts[2]}"

    kode_objek = get(r"B\.1\s+Kode\s+Objek\s+Pajak\s+:\s*([0-9\-]+)")
    dpp = get(r"B\.3\s+Dasar\s+Pengenaan\s+Pajak\s+:\s*Rp\s*([0-9\.]+)").replace(".", ",")
    pph_dipotong = get(r"B\.5\s+PPh\s+Dipungut\s+:\s*Rp\s*([0-9\.]+)").replace(".", ",")
    tarif = get(r"B\.4\s+Tarif\s+:\s*([0-9\.,]+)%").replace(".", ",")

    dikenakan_tarif_lbih_tinggi = get(r"TIDAK MEMILIKI NPWP\s+\((.*?)\)", "")
    keterangan_kode_objek = get(r"B\.2\s+Keterangan\s+:\s*(.*)\n", "")
    nomor_dokumen = get(r"B\.7\s+Nomor\s+Dokumen\s+Referensi\s+:\s*([\w\-/]*)")
    nama_dokumen = get(r"B\.8\s+Nama\s+Dokumen\s+:\s*([\w\-/ ]*)")
    tanggal_dokumen = get(r"B\.8.*?Tanggal\s+Dokumen\s+:\s*(\d{2}\s+\d{2}\s+\d{4})")
    tanggal_dokumen_fmt = ""
    if tanggal_dokumen:
        tgl_parts = tanggal_dokumen.split()
        if len(tgl_parts) == 3:
            tanggal_dokumen_fmt = f"{tgl_parts[0]}/{tgl_parts[1]}/{tgl_parts[2]}"

    nomor_faktur = get(r"B\.9\s+Nomor\s+Faktur\s+Pajak\s+:\s*([\w\-\.]+)")
    tanggal_faktur = get(r"B\.9.*?Tanggal\s+Faktur\s+Pajak\s+:\s*(\d{2}\s+\d{2}\s+\d{4})")
    tanggal_faktur_fmt = ""
    if tanggal_faktur:
        tf = tanggal_faktur.split()
        if len(tf) == 3:
            tanggal_faktur_fmt = f"{tf[0]}/{tf[1]}/{tf[2]}"

    sk_pp23 = get(r"PP\s+Nomor\s+23.*?Nomor\s+:\s*([\w\-\.]*)")

    npwp_pemotong = get(r"C\.1\s+NPWP\s+:\s*([\d\.\-]+)")
    nama_wp_pemotong = get(r"C\.2\s+Nama\s+Wajib\s+Pajak\s+:\s*(.+)")
    tanggal_potong = get(r"C\.3\s+Tanggal\s+:\s*(\d{2})\s+(\d{2})\s+(\d{4})")
    tanggal_potong_fmt = ""
    if tanggal_potong:
        tpot = re.findall(r"\d{2,4}", tanggal_potong)
        if len(tpot) == 3:
            tanggal_potong_fmt = f"{tpot[0]}/{tpot[1]}/{tpot[2]}"
    nama_penandatangan = get(r"C\.4\s+Nama\s+Penandatangan\s+:\s*(.+?)(?:\n|$)")

    return {
        "Nomor Bukti Potong": nomor_bp,
        "Pembetulan ke-": pembetulan,
        "Jenis PPh": jenis_pph,
        "NPWP DIPOTONG/DIPUNGUT": npwp_dipotong,
        "NIK DIPOTONG/DIPUNGUT": nik_dipotong,
        "Nama DIPOTONG/DIPUNGUT": nama_dipotong,
        "Masa Pajak": masa_final,
        "Kode objek Pajak": kode_objek,
        "Dasar Pengenaan Pajak": dpp,
        "dikenakan tarif lebih tinggi tidak memiliki NPWP": dikenakan_tarif_lbih_tinggi,
        "tarif (%)": tarif,
        "PPh dipotong": pph_dipotong,
        "Keterangan Kode Objek Pajak": keterangan_kode_objek,
        "Nomor Dokumen Referensi": nomor_dokumen,
        "Nama Dokumen": nama_dokumen,
        "Tanggal Dokumen": tanggal_dokumen_fmt,
        "Nomor Faktur Pajak": nomor_faktur,
        "Tanggal Faktur Pajak": tanggal_faktur_fmt,
        "SK PP23": sk_pp23,
        "Nama PEMOTONG": nama_penandatangan,
        "Nama WP PEMOTONG": nama_wp_pemotong,
        "Tanggal Potong": tanggal_potong_fmt,
        "Nama Penandatangan": nama_penandatangan
    }

st.title("Rekap Data Bukti Potong DJP")

uploaded_files = st.file_uploader("Upload file PDF", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    rows = []
    for file in uploaded_files:
        import pdfplumber
        with pdfplumber.open(file) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        data = extract_data(text)
        rows.append(data)

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)

    # Export to Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Rekap")
    st.download_button("Download Excel", output.getvalue(), "Rekap_BP_Unifikasi.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
