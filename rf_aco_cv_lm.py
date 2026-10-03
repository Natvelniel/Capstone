import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.metrics import accuracy_score
import random
import time
import joblib

# ==========================================
# 1. KONFIGURASI PARAMETER & PENCARIAN (ACO)
# ==========================================
# Ini adalah "peta" rute yang akan dilewati oleh semut
SEARCH_SPACE = {
    'n_estimators': [50, 100, 150],       # Jumlah pohon di hutan
    'max_depth': [None, 10, 20, 30],      # Kedalaman maksimal pohon
    'min_samples_split': [2, 5, 10]       # Minimal sampel untuk memecah cabang
}

# Pengaturan Algoritma Semut
N_ANTS = 5          # Jumlah semut setiap putaran
N_ITERATIONS = 3    # Jumlah putaran pencarian
EVAPORATION = 0.5   # Kecepatan feromon menguap (agar semut tidak terjebak di 1 rute)

def initialize_pheromones(search_space):
    """Memberikan nilai feromon awal (bau) yang sama rata untuk setiap pilihan"""
    pheromones = {}
    for key, values in search_space.items():
        pheromones[key] = {val: 1.0 for val in values}
    return pheromones

def select_parameter(pheromones_for_param):
    """Semut memilih jalan berdasarkan jejak feromon yang paling kuat"""
    options = list(pheromones_for_param.keys())
    # Probabilitas memilih berdasarkan jumlah feromon
    total_pheromone = sum(pheromones_for_param.values())
    probabilities = [pheromones_for_param[opt] / total_pheromone for opt in options]
    
    # Pilih secara acak tapi condong ke feromon yang besar (Roulette Wheel Selection)
    chosen_val = np.random.choice(options, p=probabilities)
    # Handle None type since np.random.choice converts None to 'None' string
    if str(chosen_val) == 'None': return None
    # Convert string numbers back to int if needed
    try: return int(chosen_val) 
    except: return chosen_val

# ==========================================
# 2. FUNGSI UTAMA PELATIHAN & EVALUASI
# ==========================================
def main():
    print("Membaca Dataset Balanced (Bisa memakan waktu beberapa detik)...\n")
    # Ganti dengan 'dataset_fe_balanced.csv' jika ingin menguji Feature Envy
    df = pd.read_csv('dataset_lm_balanced.csv') 
    
    # Memisahkan Fitur (X) dan Label (y)
    target = 'is_long_method'
    X = df.drop(columns=[target])
    y = df[target]

    # Karena datanya banuak, ACO akan sangat lama jika pakai semua data.
    # Kita ambil sampel 10.000 baris acak HANYA untuk tahap pencarian Semut (ACO)
    print("Mengambil 10.000 sampel acak untuk mempercepat proses pencarian ACO...")
    df_sample = df.sample(n=10000, random_state=42)
    X_aco = df_sample.drop(columns=[target])
    y_aco = df_sample[target]

    print("\n--- MEMULAI ANT COLONY OPTIMIZATION (ACO) ---")
    pheromones = initialize_pheromones(SEARCH_SPACE)
    best_params_overall = None
    best_score_overall = 0.0

    start_time = time.time()
    
    for iteration in range(N_ITERATIONS):
        print(f"\n[Iterasi ACO {iteration + 1}/{N_ITERATIONS}] Semut sedang berjalan mencari kombinasi parameter...")
        
        ant_results = []
        for ant in range(N_ANTS):
            # 1. Semut memilih kombinasi parameter
            params = {
                'n_estimators': select_parameter(pheromones['n_estimators']),
                'max_depth': select_parameter(pheromones['max_depth']),
                'min_samples_split': select_parameter(pheromones['min_samples_split'])
            }
            
            # 2. Coba parameter tersebut ke Random Forest
            model = RandomForestClassifier(random_state=42, n_jobs=-1, **params)
            
            # Kita uji cepat (cukup 3-fold) untuk melihat apakah parameter ini bagus
            cv_quick = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
            # Karena ini ujicoba semut, kita pakai X_aco (sampel kecil) agar cepat
            quick_scores = cross_validate(model, X_aco, y_aco, cv=cv_quick, scoring='accuracy')
            score = quick_scores['test_score'].mean()
            
            ant_results.append({'params': params, 'score': score})
            print(f"  Semut {ant+1}: {params} --> Akurasi Cepat: {score:.4f}")
            
            # Update the global best finding
            if score > best_score_overall:
                best_score_overall = score
                best_params_overall = params
        
        # 3. Update Pheromones (Feromon menguap + Semut terbaik menambah feromon)
        # Penguapan (semua bau berkurang)
        for key in pheromones:
            for val in pheromones[key]:
                pheromones[key][val] *= (1 - EVAPORATION)
                
        # Tambah feromon untuk rute-rute yang diambil oleh semut di iterasi ini
        # Semakin tinggi akurasinya, semakin banyak feromon yang ditinggalkan
        for result in ant_results:
            p = result['params']
            s = result['score']
            pheromones['n_estimators'][p['n_estimators']] += s
            pheromones['max_depth'][p['max_depth']] += s
            pheromones['min_samples_split'][p['min_samples_split']] += s

    print(f"\n[ACO SELESAI] Kombinasi TERBAIK ditemukan: {best_params_overall} (Akurasi Uji: {best_score_overall:.4f})")
    
    # ==========================================
    # 3. PENGUJIAN 10-FOLD CV PADA DATA PENUH
    # ==========================================
    print("\n--- MEMULAI 10-FOLD CROSS VALIDATION PADA SELURUH DATA ---")
    print("Ini adalah ujian sesungguhnya. Mohon tunggu, proses ini bisa memakan waktu beberapa menit...\n")
    
    final_model = RandomForestClassifier(random_state=42, n_jobs=-1, **best_params_overall)
    cv_10 = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
    
    # Menentukan metrik evaluasi yang diminta dosen
    scoring_metrics = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']
    
    # Melakukan 10-Fold CV menggunakan keseluruhan dataset
    cv_results = cross_validate(final_model, X, y, cv=cv_10, scoring=scoring_metrics)
    
    # Mengambil rata-rata dari 10 putaran ujian
    print("=====================================================")
    print("HASIL AKHIR EVALUASI MODEL (RANDOM FOREST + ACO)")
    print("=====================================================")
    print(f"Accuracy  : {cv_results['test_accuracy'].mean() * 100:.2f}%")
    print(f"Precision : {cv_results['test_precision'].mean() * 100:.2f}%")
    print(f"Recall    : {cv_results['test_recall'].mean() * 100:.2f}%")
    print(f"F1-Score  : {cv_results['test_f1'].mean() * 100:.2f}%")
    print(f"AUC       : {cv_results['test_roc_auc'].mean() * 100:.2f}%")
    print("=====================================================")
    
    # === TAMBAHAN BARU: SIMPAN MODEL ===
    print("\n[Menyimpan Model] Melatih model final dengan seluruh data...")
    final_model.fit(X, y)
    joblib.dump(final_model, 'aco_model_lm.joblib')
    print("✅ Model ACO berhasil disimpan sebagai 'aco_model_lm.joblib'")
    # ===================================
    
    end_time = time.time()
    print(f"Total waktu eksekusi: {(end_time - start_time) / 60:.2f} menit")

if __name__ == "__main__":
    main()
    
   