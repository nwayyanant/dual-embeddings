
import pandas as pd
df = pd.read_parquet("data/out/normalized.parquet")
print(df.columns)
print(df["multilingual_concat"].head())
