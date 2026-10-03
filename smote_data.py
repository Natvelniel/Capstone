import pandas as pd
from imblearn.over_sampling import SMOTE
import warnings
warnings.filterwarnings('ignore') 

def balance_dataset(input_file, target_column, column_to_drop, output_file):
    print(f"\n--- Memproses {input_file} untuk target '{target_column}' ---")
    try:
        df = pd.read_csv(input_file, low_memory=False)
    except FileNotFoundError:
        print(f"Error: File '{input_file}' tidak ditemukan.")
        return

    df_numeric = df.select_dtypes(include=['number', 'bool'])
    
    # MENCEGAH KEBOCORAN DATA: Hapus kolom target label lain agar tidak dihitung sebagai fitur
    if column_to_drop in df_numeric.columns:
        df_numeric = df_numeric.drop(columns=[column_to_drop])

    if target_column not in df_numeric.columns:
        print(f"Error: Kolom '{target_column}' tidak ditemukan di dataset!")
        return

    print("Menghapus baris data yang kosong (NaN)...")
    df_numeric = df_numeric.dropna() 

    X = df_numeric.drop(columns=[target_column])
    y = df_numeric[target_column].astype(bool)
    
    print("Jumlah kelas SEBELUM SMOTE:")
    print(y.value_counts())
    
    print("Sedang melakukan over-sampling dengan SMOTE. Harap tunggu...")
    smote = SMOTE(random_state=42)
    X_resampled, y_resampled = smote.fit_resample(X, y)
    
    print("\nJumlah kelas SETELAH SMOTE:")
    print(y_resampled.value_counts())
    
    df_balanced = pd.DataFrame(X_resampled, columns=X.columns)
    df_balanced[target_column] = y_resampled
    
    df_balanced.to_csv(output_file, index=False)
    print(f"✅ Berhasil! File diseimbangkan dan disimpan sebagai: {output_file}")

if __name__ == "__main__":
    # 1. Proses SMOTE untuk Long Method (Buang kolom feature envy)
    balance_dataset(
        # input_file='dataset_210_gabungan.csv', 
        input_file='dataset_42_berlabel.csv', 
        target_column='is_long_method', 
        column_to_drop='is_feature_envy',
        output_file='dataset_lm_balanced.csv'
    )

    # 2. Proses SMOTE untuk Feature Envy (Buang kolom long method)
    balance_dataset(
        # input_file='dataset_210_gabungan.csv', 
        input_file='dataset_42_berlabel.csv', 
        target_column='is_feature_envy', 
        column_to_drop='is_long_method',
        output_file='dataset_fe_balanced.csv'
    )