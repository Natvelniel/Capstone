import os
import pandas as pd
import joblib
import glob

def main():
    print("=== PROGRAM PELABELAN OTOMATIS (BATCH PREDICT) ===\n")
    
    # Folder tempat Anda menaruh file CSV
    folder_input = "data_mentah"
    file_output = "dataset_42_berlabel.csv"
    
    # Buat folder jika belum ada
    if not os.path.exists(folder_input):
        os.makedirs(folder_input)
        print(f"📁 Folder '{folder_input}' berhasil dibuat.")
        print(f"⏳ SILAKAN MASUKKAN 42 FILE CSV ANDA KE DALAM FOLDER '{folder_input}' LALU JALANKAN ULANG PROGRAM INI.")
        return

    # Cari semua file CSV di dalam folder
    csv_files = glob.glob(os.path.join(folder_input, "*.csv"))
    
    if len(csv_files) == 0:
        print(f"❌ Tidak ada file CSV yang ditemukan di dalam folder '{folder_input}'.")
        return
        
    print(f"🔎 Ditemukan {len(csv_files)} file CSV. Memulai proses prediksi...\n")

    # Load Model AI milik dosen
    try:
        model_lm = joblib.load('longmethod_rf_clpso_ga_nb_cfs.joblib')
        model_fe = joblib.load('featureenvy_rf_clpso_ga_nb_cfs.joblib')
        print("✅ Model klasifikasi berhasil dimuat.")
    except FileNotFoundError as e:
        print(f"❌ Error: File model tidak ditemukan. Pastikan file .joblib ada di folder utama. Detail: {e}")
        return

    # Daftar 12 Fitur yang dibutuhkan masing-masing model
    LM_FEATURES = [
        'CYCLO_method', 'NOLV_method', 'CLNAMM_method', 'CINT_method', 'CDISP_method', 
        'NOII_type', 'NOAM_type', 'NOCS_type', 'number_constructor_NotDefaultConstructor', 
        'LOC_method', 'MAXNESTING_method', 'CC_method'
    ]
    
    FE_FEATURES = [
        'CYCLO_method', 'NOLV_method', 'CLNAMM_method', 'CINT_method', 'CDISP_method', 
        'LAA_method', 'NOAV_method', 'ATFD_method', 'FANOUT_method', 'ATLD_method', 
        'FDP_method', 'CBO_type'
    ]

    list_dataframe = []
    total_baris = 0

    # Proses setiap file CSV
    print("\nSedang memproses file:")
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            
            # --- Prediksi Long Method ---
            if all(col in df.columns for col in LM_FEATURES):
                df['is_long_method'] = model_lm.predict(df[LM_FEATURES].values).astype(bool)
            else:
                num_df = df.select_dtypes(include=['number'])
                if 'Unnamed: 0' in num_df.columns: num_df = num_df.drop(columns=['Unnamed: 0'])
                df['is_long_method'] = model_lm.predict(num_df.iloc[:, :12].values).astype(bool)

            # --- Prediksi Feature Envy ---
            if all(col in df.columns for col in FE_FEATURES):
                df['is_feature_envy'] = model_fe.predict(df[FE_FEATURES].values).astype(bool)
            else:
                num_df = df.select_dtypes(include=['number'])
                if 'Unnamed: 0' in num_df.columns: num_df = num_df.drop(columns=['Unnamed: 0'])
                df['is_feature_envy'] = model_fe.predict(num_df.iloc[:, :12].values).astype(bool)

            # Simpan dataframe yang sudah dilabeli ke dalam list
            list_dataframe.append(df)
            total_baris += len(df)  
            print(f"  [OK] {os.path.basename(file)} -> {len(df)} baris")
            
        except Exception as e:
            print(f"  [GAGAL] {os.path.basename(file)}: {e}")

    # Gabungkan semua data menjadi satu file CSV
    if list_dataframe:
        print("\n⚙️ Menggabungkan seluruh data...")
        df_gabungan = pd.concat(list_dataframe, ignore_index=True)
        df_gabungan.to_csv(file_output, index=False)
        print(f"\n✅ SUKSES! {len(csv_files)} file telah diberi label dan digabungkan.")
        print(f"📊 Total data milik Anda: {total_baris} baris.")
        print(f"💾 File hasil akhir disimpan sebagai: '{file_output}'")
        
if __name__ == "__main__":
    main()  