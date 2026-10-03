import streamlit as st
from . import controller2 as ct
import pandas as pd
import io
from datetime import datetime
import os
import math
import joblib

# Load model dari file .joblib
try:
    model_fe = joblib.load('featureenvy_rf_clpso_ga_nb_cfs.joblib')
except FileNotFoundError:
    st.error("File model 'featureenvy_rf_clpso_ga_nb_cfs.joblib' tidak ditemukan. Pastikan file ada di folder utama.")
    model_fe = None

# 12 Kolom Fitur CFS untuk Feature Envy
FE_FEATURES = [
    'CYCLO_method', 'NOLV_method', 'CLNAMM_method', 'CINT_method', 'CDISP_method', 
    'LAA_method', 'NOAV_method', 'ATFD_method', 'FANOUT_method', 'ATLD_method', 
    'FDP_method', 'CBO_type'
]

def main():
    st.title("Kotlin Function Extractor - AST FE")

    # Inisialisasi state
    if "uploaded" not in st.session_state:
        st.session_state.uploaded = False
        st.session_state.df = None
        st.session_state.project_name = ""
    if "page" not in st.session_state:
        st.session_state.page = 0

    # Upload file
    if not st.session_state.uploaded:
        file = st.file_uploader("Upload a RAR or ZIP file containing Kotlin files", type=["rar", "zip"])
        if file is not None:
            with st.spinner("Processing file... Please wait."):
                df = ct.extract_and_parse(file)
                st.session_state.file = file
            if isinstance(df, str):
                st.error(f"Error extracting archive: {df}")
            else:
                st.session_state.df = df
                st.session_state.uploaded = True
                st.session_state.uploaded_file_name = os.path.splitext(file.name)[0]
                st.success("File uploaded and processed successfully!")
                st.rerun()

    # Tampilkan dataframe dan input project name jika sudah upload
    else:
        df = st.session_state.df.copy() 
        
        # --- PREDIKSI MACHINE LEARNING ---
        if model_fe is not None:
            try:
                available_cols = [col for col in FE_FEATURES if col in df.columns]
                
                if len(available_cols) == 12:
                    X_predict = df[FE_FEATURES].values
                    predictions = model_fe.predict(X_predict)
                    df['is_feature_envy'] = predictions.astype(bool)
                else:
                    num_df = df.select_dtypes(include=['number'])
                    if 'Unnamed: 0' in num_df.columns:
                        num_df = num_df.drop(columns=['Unnamed: 0'])
                    X_predict = num_df.iloc[:, :12].values
                    predictions = model_fe.predict(X_predict)
                    df['is_feature_envy'] = predictions.astype(bool)

            except Exception as e:
                st.error(f"Gagal memprediksi: {e}")
        # ----------------------------------

        # Input untuk project name
        extractor_name = st.text_input("Enter extractor name to enable download (extractor-name_project-name_extract-date.csv)", value=st.session_state.project_name)

        # Validasi input
        if extractor_name.strip() == "":
            st.warning("Please enter a extractor name to proceed with download.")
        else:
            st.session_state.project_name = extractor_name

            # Tambahkan kolom tanggal dan nama proyek
            df_modified = df.copy()
            extraction_date = datetime.now().strftime("%Y-%m-%d")
            df_modified.insert(0, "Extraction Date", extraction_date)
            df_modified.insert(1, "Project", st.session_state.project_name)

            # Convert ke CSV
            csv_buffer = io.StringIO()
            df_modified.to_csv(csv_buffer, index=False)

            # Tombol download
            st.download_button(
                label="Download CSV",
                data=csv_buffer.getvalue(),
                file_name=f"{extractor_name}_{st.session_state.uploaded_file_name}_{extraction_date}.csv",
                mime="text/csv"
            )

        # Tombol reset
        if st.button("Upload File Baru"):
            st.session_state.uploaded = False
            st.session_state.df = None
            st.session_state.project_name = ""
            st.session_state.page = 0
            st.rerun()
            
        # Paging (100 rows per page)
        rows_per_page = 100
        total_rows = len(df)
        total_pages = math.ceil(total_rows / rows_per_page)

        start_idx = st.session_state.page * rows_per_page
        end_idx = start_idx + rows_per_page

        tab1, tab2, tab3 = st.tabs(["Home", "Detailed Report", "Complexity Report"])

        with tab1:
            tab1.dataframe(df.iloc[start_idx:end_idx])

            # --- STATISTIK LAPORAN ---
            if 'is_feature_envy' in df.columns:
                st.markdown("### Laporan Statistik Prediksi Feature Envy")
                st.markdown("---")
                total_true = df['is_feature_envy'].sum()
                total_false = len(df) - total_true
                
                col1, col2 = st.columns(2)
                col1.metric("Total 'True' (Terindikasi Feature Envy)", int(total_true))
                col2.metric("Total 'False' (Normal)", int(total_false))
                st.markdown("---")
            # -------------------------

            # Layout bawah tabel
            st.markdown("<br>", unsafe_allow_html=True)

            col_left, col_center, col_right = st.columns([1, 2, 1])
            
            with col_left:
                prev_clicked = st.button("⬅ Prev", key="prev_btn", use_container_width=True)
                
            with col_center:
                st.markdown(
                    f"<div style='text-align:center; font-size: 18px;'>Page {st.session_state.page + 1} of {total_pages}</div>",
                    unsafe_allow_html=True,
                )

            with col_right:
                next_clicked = st.button("Next ➡", key="next_btn", use_container_width=True)

            if prev_clicked and st.session_state.page > 0:
                st.session_state.page -= 1
                st.rerun()
            if next_clicked and st.session_state.page < total_pages - 1:
                st.session_state.page += 1
                st.rerun()

        with tab2:
            show_detailed_report_page()

        with tab3:
            show_complexity_report_page()

def show_detailed_report_page():
    if "df" not in st.session_state or st.session_state.df is None:
        st.warning("Tidak ada data untuk ditampilkan. Silakan upload file terlebih dahulu di halaman utama.")
        return

    df = st.session_state.file
    results = ct.detail_report_parse(df)

    if "error" in results:
        st.error(results["error"])
        return

    st.subheader("Detailed Report - Grouped by Package")
    for idx, (package, details) in enumerate(results["Packages"].items(), start=1):
        st.write(f"**Package {idx}:** {package}")
        st.write(f"**File ({len(details['File'])}):** {details['File']}")
        st.write(f"**Classes ({len(details['Class'])}):** {details['Class']}")
        st.write(f"**Functions ({len(details['Method'])}):** {details['Method']}")
        st.write(f"**Properties ({len(details['Property'])}):** {details['Property']}")
        st.write("---")

def show_complexity_report_page():
    if "df" not in st.session_state or st.session_state.df is None:
        st.warning("Tidak ada data untuk ditampilkan. Silakan upload file terlebih dahulu di halaman utama.")
        return

    df = st.session_state.file
    results = ct.complexity_report_parse(df)

    if "error" in results:
        st.error(results["error"])
        return
    
    st.subheader("Complexity Report")
    st.write("Total Lines of Code (LOC):", results["LOC"]) 
    st.write("Source Lines of Code (SLOC):", results["SLOC"]) 
    st.write("Logical Lines of Code (LLOC):", results["LLOC"]) 
    st.write("Comment Lines of Code (CLOC):", results["CLOC"]) 
    st.write("Cognitive Complexity:", results["Cognitive_Complexity"]) 
    st.write("Number of Total Code Smells:", results["Code_Smells"]) 
    st.write("Comment Source Ratio (%):", results["Comment_Ratio"]) 
    st.write("MCC per 1,000 LLOC:", results["MCC_per_1000_lloc"]) 
    st.write("Code Smells per 1,000 LLOC:", results["Code_smells_per_1000_lloc"]) 
    st.write("---")

if __name__ == "__main__":
    main()