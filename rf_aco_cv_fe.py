import joblib
import pandas as pd
import numpy as np
import time
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import warnings

warnings.filterwarnings('ignore')

# 1. BACA DATASET FEATURE ENVY
print("Membaca Dataset Balanced Feature Envy (Bisa memakan waktu beberapa detik)...\n")
try:
    df = pd.read_csv('dataset_fe_balanced.csv')
except FileNotFoundError:
    print("Error: File 'dataset_fe_balanced.csv' tidak ditemukan. Pastikan file ada di folder yang sama.")
    exit()

target_col = 'is_feature_envy'

if target_col not in df.columns:
    print(f"Error: Kolom target '{target_col}' tidak ditemukan di dataset.")
    exit()

# Pisahkan Fitur (X) dan Target (y)
X_full = df.drop(columns=[target_col]).values
y_full = df[target_col].astype(int).values

# 2. AMBIL SAMPEL UNTUK ACO (Agar pencarian parameter cepat)
print("Mengambil 10.000 sampel acak untuk mempercepat proses pencarian ACO...\n")
sample_size = min(10000, len(df))
df_sample = df.sample(n=sample_size, random_state=42)
X_sample = df_sample.drop(columns=[target_col]).values
y_sample = df_sample[target_col].astype(int).values

# ==========================================
# 3. ALGORITMA ANT COLONY OPTIMIZATION (ACO)
# ==========================================
print("--- MEMULAI ANT COLONY OPTIMIZATION (ACO) UNTUK FEATURE ENVY ---\n")

# Ruang pencarian Parameter (Tuas yang bisa diputar semut)
param_space = {
    'n_estimators': [50, 100, 150],
    'max_depth': [10, 20, 30],
    'min_samples_split': [2, 5, 10]
}

# Inisialisasi Feromon (Jejak bau semut, awalnya sama rata)
pheromones = {
    'n_estimators': {k: 1.0 for k in param_space['n_estimators']},
    'max_depth': {k: 1.0 for k in param_space['max_depth']},
    'min_samples_split': {k: 1.0 for k in param_space['min_samples_split']}
}

n_ants = 5       # Jumlah semut per putaran
n_iterations = 3 # Jumlah putaran
evaporation_rate = 0.2

best_global_acc = 0.0
best_global_params = {}

for iteration in range(n_iterations):
    print(f"[Iterasi ACO {iteration+1}/{n_iterations}] Semut sedang berjalan mencari kombinasi parameter...")
    
    ant_results = []
    
    for ant in range(n_ants):
        # Semut memilih jalan berdasarkan jejak feromon
        chosen_params = {}
        for param_name, values in param_space.items():
            phero_values = np.array([pheromones[param_name][v] for v in values])
            probabilities = phero_values / phero_values.sum()
            chosen_val = np.random.choice(values, p=probabilities)
            chosen_params[param_name] = chosen_val
            
        # Semut mencoba melatih AI dengan parameter yang ia temukan
        rf = RandomForestClassifier(
            n_estimators=chosen_params['n_estimators'],
            max_depth=chosen_params['max_depth'],
            min_samples_split=chosen_params['min_samples_split'],
            random_state=42,
            n_jobs=-1
        )
        
        # Tes cepat pada data sampel
        rf.fit(X_sample, y_sample)
        preds = rf.predict(X_sample)
        acc = accuracy_score(y_sample, preds)
        
        print(f"  Semut {ant+1}: {chosen_params} --> Akurasi Cepat: {acc:.4f}")
        
        ant_results.append((chosen_params, acc))
        
        # Ingat parameter terbaik sepanjang masa
        if acc > best_global_acc:
            best_global_acc = acc
            best_global_params = chosen_params

    # Penguapan Feromon (Jejak bau lama perlahan hilang)
    for param_name in pheromones:
        for k in pheromones[param_name]:
            pheromones[param_name][k] *= (1.0 - evaporation_rate)
            
    # Semut yang sukses meninggalkan feromon baru
    for params, acc in ant_results:
        for param_name, val in params.items():
            pheromones[param_name][val] += acc
            
    print("")

print(f"[ACO SELESAI] Kombinasi TERBAIK ditemukan: {best_global_params} (Akurasi Uji: {best_global_acc:.4f})\n")

# ==========================================
# 4. 10-FOLD CROSS VALIDATION (UJIAN ASLI)
# ==========================================
print("--- MEMULAI 10-FOLD CROSS VALIDATION PADA SELURUH DATA ---")
print("Ini adalah ujian sesungguhnya. Mohon tunggu, proses ini bisa memakan waktu beberapa menit...\n")

start_time = time.time()

skf = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)

# Siapkan model dengan parameter terbaik hasil pencarian ACO tadi
best_rf = RandomForestClassifier(
    n_estimators=best_global_params['n_estimators'],
    max_depth=best_global_params['max_depth'],
    min_samples_split=best_global_params['min_samples_split'],
    random_state=42,
    n_jobs=-1
)

# Tempat menyimpan nilai dari tiap putaran
acc_scores, prec_scores, rec_scores, f1_scores, auc_scores = [], [], [], [], []

for fold, (train_idx, test_idx) in enumerate(skf.split(X_full, y_full)):
    X_train, X_test = X_full[train_idx], X_full[test_idx]
    y_train, y_test = y_full[train_idx], y_full[test_idx]
    
    best_rf.fit(X_train, y_train)
    y_pred = best_rf.predict(X_test)
    y_prob = best_rf.predict_proba(X_test)[:, 1]
    
    acc_scores.append(accuracy_score(y_test, y_pred))
    prec_scores.append(precision_score(y_test, y_pred))
    rec_scores.append(recall_score(y_test, y_pred))
    f1_scores.append(f1_score(y_test, y_pred))
    auc_scores.append(roc_auc_score(y_test, y_prob))

# === TAMBAHAN BARU: SIMPAN MODEL ===
print("\n[Menyimpan Model] Melatih model final dengan seluruh data...")
best_rf.fit(X_full, y_full)
joblib.dump(best_rf, 'aco_model_fe.joblib')
print("✅ Model ACO berhasil disimpan sebagai 'aco_model_fe.joblib'")
# ===================================

end_time = time.time()
execution_time = (end_time - start_time) / 60

print("=====================================================")
print("HASIL AKHIR EVALUASI MODEL (FEATURE ENVY: RF + ACO)")
print("=====================================================")
print(f"Accuracy  : {np.mean(acc_scores)*100:.2f}%")
print(f"Precision : {np.mean(prec_scores)*100:.2f}%")
print(f"Recall    : {np.mean(rec_scores)*100:.2f}%")
print(f"F1-Score  : {np.mean(f1_scores)*100:.2f}%")
print(f"AUC       : {np.mean(auc_scores)*100:.2f}%")
print("=====================================================")
print(f"Total waktu eksekusi: {execution_time:.2f} menit")