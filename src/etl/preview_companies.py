import pandas as pd

df = pd.read_excel("../../data/raw/companies.xlsx", header=1)

print("Shape (rows, columns):", df.shape)
print()
print("Column names:")
print(df.columns.tolist())
print()
print("First 5 rows:")
print(df.head())
