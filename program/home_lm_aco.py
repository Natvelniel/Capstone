import streamlit as st
from . import controller2 as ct
import pandas as pd
import io
from datetime import datetime
import os
import math
import joblib

# LOAD MODEL BARU (HASIL TRAINING ACO TIM ANDA)
try:
    model_lm = joblib.load('aco_model_lm.joblib')
except FileNotFoundError:
    st.error("File model 'aco_model_lm.joblib' belum dibuat. Jalankan rf_aco_cv_lm.py terlebih dahulu.")
    model_lm = None

def main():
    # JUDUL HALAMAN DIUBAH
    st.title("Kotlin Function Extractor - AST LM (ACO)")

    if "uploaded" not in st.session_state:
        st.session_state.uploaded = False
        st.session_state.df = None
        st.session_state.project_name = ""
    if "page" not in st.session_state:
        st.session_state.page = 0

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
    else:
        df = st.session_state.df.copy() 
        
        # --- PREDIKSI MACHINE LEARNING (DISESUAIKAN DENGAN MODEL ACO) ---
        if model_lm is not None:
            try:
                num_df = df.select_dtypes(include=['number'])
                if 'Unnamed: 0' in num_df.columns:
                    num_df = num_df.drop(columns=['Unnamed: 0'])
                
                expected_features = model_lm.n_features_in_
                
                if num_df.shape[1] >= expected_features:
                    X_predict = num_df.iloc[:, :expected_features].values
                    predictions = model_lm.predict(X_predict)
                    df['is_long_method'] = predictions.astype(bool)
                else:
                    st.error(f"Gagal memprediksi: Ekstraksi hanya mendapat {num_df.shape[1]} fitur, model butuh {expected_features} fitur.")
            except Exception as e:
                st.error(f"Gagal memprediksi: {e}")
        # -------------------------------------------------------------

        extractor_name = st.text_input("Enter extractor name to enable download", value=st.session_state.project_name)

        if extractor_name.strip() == "":
            st.warning("Please enter a extractor name to proceed with download.")
        else:
            st.session_state.project_name = extractor_name
            df_modified = df.copy()
            extraction_date = datetime.now().strftime("%Y-%m-%d")
            df_modified.insert(0, "Extraction Date", extraction_date)
            df_modified.insert(1, "Project", st.session_state.project_name)

            csv_buffer = io.StringIO()
            df_modified.to_csv(csv_buffer, index=False)

            st.download_button(
                label="Download CSV",
                data=csv_buffer.getvalue(),
                file_name=f"{extractor_name}_{st.session_state.uploaded_file_name}_{extraction_date}.csv",
                mime="text/csv"
            )

        if st.button("Upload File Baru"):
            st.session_state.uploaded = False
            st.session_state.df = None
            st.session_state.project_name = ""
            st.session_state.page = 0
            st.rerun()
            
        rows_per_page = 100
        total_rows = len(df)
        total_pages = math.ceil(total_rows / rows_per_page)

        start_idx = st.session_state.page * rows_per_page
        end_idx = start_idx + rows_per_page

        tab1, tab2, tab3 = st.tabs(["Home", "Detailed Report", "Complexity Report"])

        with tab1:
            tab1.dataframe(df.iloc[start_idx:end_idx])

            if 'is_long_method' in df.columns:
                st.markdown("### Laporan Statistik Prediksi Long Method (ACO Model)")
                st.markdown("---")
                total_true = df['is_long_method'].sum()
                total_false = len(df) - total_true
                
                col1, col2 = st.columns(2)
                col1.metric("Total 'True' (Terindikasi Long Method)", int(total_true))
                col2.metric("Total 'False' (Normal)", int(total_false))
                st.markdown("---")

            st.markdown("<br>", unsafe_allow_html=True)
            col_left, col_center, col_right = st.columns([1, 2, 1])
            with col_left:
                prev_clicked = st.button("⬅ Prev", key="prev_btn", use_container_width=True)
            with col_center:
                st.markdown(f"<div style='text-align:center; font-size: 18px;'>Page {st.session_state.page + 1} of {total_pages}</div>", unsafe_allow_html=True)
            with col_right:
                next_clicked = st.button("Next ➡", key="next_btn", use_container_width=True)

            if prev_clicked and st.session_state.page > 0:
                st.session_state.page -= 1
                st.rerun()
            if next_clicked and st.session_state.page < total_pages - 1:
                st.session_state.page += 1
                st.rerun()

        # --- BAGIAN YANG SEBELUMNYA HILANG ---
        with tab2:
            show_detailed_report_page()

        with tab3:
            show_complexity_report_page()

# --- FUNGSI HELPER YANG SEBELUMNYA HILANG ---
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