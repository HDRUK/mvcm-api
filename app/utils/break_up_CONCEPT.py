import pandas as pd
import os

# Function to split a TSV file into chunks of a given size
def split_tsv_into_fixed_chunks(file_path, chunk_size=10000):
    # Read the TSV file into a Pandas DataFrame
    df = pd.read_csv(file_path, sep='\t')
    
    # Initialize an empty list to hold output file paths
    output_files = []
    
    # Calculate the number of chunks needed
    num_chunks = (len(df) // chunk_size) + (1 if len(df) % chunk_size else 0)
    
    # Split the DataFrame into chunks and save each one as a new TSV file
    for i in range(num_chunks):
        start_idx = i * chunk_size
        end_idx = (i + 1) * chunk_size if i != num_chunks - 1 else len(df)
        
        chunk = df.iloc[start_idx:end_idx]

        output_file_path = f'chunk_{i+1}.tsv'
        chunk.to_csv(output_file_path, sep='\t', index=False)
        
        output_files.append(output_file_path)
        
    return output_files

# Create a sample TSV file for demonstration purposes
# For this example, the file will have only 15 rows, but the function can handle larger files as well
sample_tsv_path = 'CONCEPT_RELATIONSHIP.tsv'


# Split the sample TSV file into chunks of 5 lines each (for demonstration)
# In your case, the chunk_size would be 10000 as you specified
output_files = split_tsv_into_fixed_chunks(sample_tsv_path, chunk_size=10000)
