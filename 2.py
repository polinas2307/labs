import os
import time
import pandas as pd
import numpy as np

CSV_SOURCE = "shopping_trends.csv"
BENCHMARK_CSV = "benchmark_data.csv"
PARQUET_SNAPPY = "data_snappy.parquet"
PARQUET_GZIP = "data_gzip.parquet"
PARQUET_NONE = "data_none.parquet"


def prepare_benchmark_dataset():
    """Завантажує файл або створює масив на ~500k рядків для виразного бенчмарку."""
    if os.path.exists(CSV_SOURCE):
        print(f"-> Завантаження базового файлу: {CSV_SOURCE}")
        base_df = pd.read_csv(CSV_SOURCE)
        # Розмножуємо вихідний датасет, щоб імітувати великий аналітичний масив
        multiplier = max(1, 500_000 // len(base_df))
        df = pd.concat([base_df] * multiplier, ignore_index=True)
    else:
        print("-> Базовий файл не знайдено, генеруємо тестовий масив (500 000 рядків)...")
        n = 500_000
        df = pd.DataFrame({
            "Customer ID": range(1, n + 1),
            "Age": np.random.randint(18, 70, size=n),
            "Gender": np.random.choice(["Male", "Female"], size=n),
            "Category": np.random.choice(["Clothing", "Footwear", "Outerwear", "Accessories"], size=n),
            "Purchase Amount (USD)": np.random.uniform(10.0, 500.0, size=n).round(2),
            "Payment Method": np.random.choice(["Credit Card", "PayPal", "Cash", "Debit Card"], size=n),
            "Review Rating": np.random.uniform(1.0, 5.0, size=n).round(1)
        })

    df.to_csv(BENCHMARK_CSV, index=False)
    print(f"[OK] Створено вихідний CSV: {BENCHMARK_CSV} ({len(df):,} рядків)\n")
    return df


def convert_formats(df):
    """Конвертує датасет у Parquet із різними алгоритмами стиснення."""
    print("--- 1. Конвертація CSV -> Parquet ---")
    
    # 1. Parquet зі стандартним стисненням Snappy (баланс швидкість/розмір)
    df.to_parquet(PARQUET_SNAPPY, engine="pyarrow", compression="snappy")
    print(f"Збережено: {PARQUET_SNAPPY} (кодек snappy)")

    # 2. Parquet зі стисненням GZIP (максимальне стиснення)
    df.to_parquet(PARQUET_GZIP, engine="pyarrow", compression="gzip")
    print(f"Збережено: {PARQUET_GZIP} (кодек gzip)")

    # 3. Parquet без стиснення (чистий стовпчастий бінарний формат)
    df.to_parquet(PARQUET_NONE, engine="pyarrow", compression=None)
    print(f"Збережено: {PARQUET_NONE} (без стиснення)\n")


def compare_file_sizes():
    """Порівнює розмір отриманих файлів на диску."""
    print("--- 2. Порівняння розмірів файлів на диску ---")
    files = [
        ("CSV (оригінал)", BENCHMARK_CSV),
        ("Parquet (None)", PARQUET_NONE),
        ("Parquet (Snappy)", PARQUET_SNAPPY),
        ("Parquet (Gzip)", PARQUET_GZIP),
    ]

    base_size = os.path.getsize(BENCHMARK_CSV)
    results = []

    for name, path in files:
        size_bytes = os.path.getsize(path)
        size_mb = size_bytes / (1024 * 1024)
        compression_ratio = (1 - (size_bytes / base_size)) * 100
        results.append({
            "Формат": name,
            "Розмір (MB)": round(size_mb, 2),
            "Стиснення відносно CSV (%)": f"{compression_ratio:.1f}%" if compression_ratio > 0 else "0.0%"
        })

    table = pd.DataFrame(results)
    print(table.to_string(index=False))
    print()


def benchmark_queries():
    """Тестує швидкість виконання типових аналітичних операцій."""
    print("--- 3. Тестування продуктивності аналітичних запитів ---")

    # Тест 1: Зчитування тільки одного стовпця (Projection)
    col_name = "Purchase Amount (USD)"

    t0 = time.perf_counter()
    _ = pd.read_csv(BENCHMARK_CSV, usecols=[col_name])
    csv_col_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    _ = pd.read_parquet(PARQUET_SNAPPY, columns=[col_name])
    parquet_col_time = time.perf_counter() - t0

    print(f"[Запит 1: Зчитування лише одного стовпця '{col_name}']")
    print(f"  * CSV time:     {csv_col_time:.4f} c")
    print(f"  * Parquet time: {parquet_col_time:.4f} c")
    print(f"  -> Прискорення Parquet: {csv_col_time / parquet_col_time:.1f}x\n")

    # Тест 2: Фільтрація рядків та обчислення середнього чека (Filter + Aggregation)
    t0 = time.perf_counter()
    df_csv = pd.read_csv(BENCHMARK_CSV)
    res_csv = df_csv[df_csv["Age"] > 30][col_name].mean()
    csv_agg_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    # Parquet дозволяє зчитати тільки потрібні для обчислення колонки
    df_parquet = pd.read_parquet(PARQUET_SNAPPY, columns=["Age", col_name])
    res_parquet = df_parquet[df_parquet["Age"] > 30][col_name].mean()
    parquet_agg_time = time.perf_counter() - t0

    print(f"[Запит 2: Фільтрація (Age > 30) та розрахунок середнього Purchase Amount]")
    print(f"  * CSV time:     {csv_agg_time:.4f} c (Результат: {res_csv:.2f})")
    print(f"  * Parquet time: {parquet_agg_time:.4f} c (Результат: {res_parquet:.2f})")
    print(f"  -> Прискорення Parquet: {csv_agg_time / parquet_agg_time:.1f}x\n")


if __name__ == "__main__":
    df = prepare_benchmark_dataset()
    convert_formats(df)
    compare_file_sizes()
    benchmark_queries()
