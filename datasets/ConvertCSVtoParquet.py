# Converts CSV to parquet for more efficient loading to memory


import pandas as pd

# List of CSV files to convert
csv_files = ['acceptable_prompts.csv', 'bad_prompts.csv']

# Convert each CSV file to a Parquet file
for csv_file in csv_files:
    # Load the CSV data into a pandas DataFrame
    df = pd.read_csv(csv_file)

    # Create a Parquet file name based on the CSV file name
    parquet_file = csv_file.replace('.csv', '.parquet')

    # Write the DataFrame to a Parquet file
    df.to_parquet(parquet_file, engine='pyarrow')
