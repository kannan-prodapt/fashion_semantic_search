import pandas as pd
import re, json

def process_excel(filename):
    pass

def preview_csv_head(file_path: str, n: int = 5):
    """
    Load only the first n rows of the CSV and print them as a DataFrame
    so you can inspect schema and data.
    """
    print(f"\n=== Previewing first {n} rows of {file_path} ===\n")
    df = pd.read_csv(file_path, nrows=n)
    print(df.iloc[0].to_dict())        # prints in DataFrame format


if __name__ == "__main__":
    filename = "final_processed_data.csv"
    preview_csv_head(filename)
