import pandas as pd
import glob
import os

def main():
    print("=== PROGRAM PENGGABUNG DATA TIM (MERGE CSV) ===\n")
    
    # Folder tempat mengumpulkan 5 file hasil kerja tim
    folder_input = "data_tim"
    file_output = "dataset_210_gabungan.csv"
    
    # Buat folder jika belum ada
    if not os.path.exists(folder_input):
        os.makedirs(folder_input)
        print(f"📁 Folder '{folder_input}' telah dibuat.")
        print(f"⏳ SILAKAN MASUKKAN 5 FILE CSV HASIL KERJA TIM KE DALAM FOLDER INI, LALU JALANKAN ULANG.")
        return

    # Cari semua file CSV
    csv_files = glob.glob(os.path.join(folder_input, "*.csv"))
    
    if len(csv_files) == 0:
        print(f"❌ Tidak ada file CSV di dalam folder '{folder_input}'.")
        return
        
    print(f"🔎 Ditemukan {len(csv_files)} file. Memulai penggabungan...\n")
    
    list_df = []
    total_baris = 0
    
    for file in csv_files:
        try:
            df = pd.read_csv(file)
            list_df.append(df)
            total_baris += len(df)
            print(f"  [OK] {os.path.basename(file)} -> {len(df)} baris")
        except Exception as e:
            print(f"  [GAGAL] {os.path.basename(file)}: {e}")
            
    # Gabungkan semua data
    if list_df:
        df_gabungan = pd.concat(list_df, ignore_index=True)
        # Menghapus baris kosong (jika ada) saat penggabungan
        df_gabungan = df_gabungan.dropna(subset=['is_long_method', 'is_feature_envy'], how='all')
        df_gabungan.to_csv(file_output, index=False)
        
        print(f"\n✅ SUKSES! {len(csv_files)} file berhasil digabungkan.")
        print(f"📊 Total keseluruhan data Capstone: {len(df_gabungan)} baris.")
        print(f"💾 File akhir disimpan sebagai: '{file_output}'")

if __name__ == "__main__":
    main()