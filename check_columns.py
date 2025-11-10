import pandas as pd

file_path = "Indian_Food_Nutrition_Processed 2.csv"

try:
    df = pd.read_csv(file_path)
    print("\n✅ Dataset loaded successfully!")
    print("📊 Columns found in the dataset:\n")
    print(df.columns)
    print("\n🔹 First 5 rows:\n")
    print(df.head())
except FileNotFoundError:
    print(f"⚠️ File not found! Make sure '{file_path}' is in this folder.")
except Exception as e:
    print(f"❌ Error: {e}")
    