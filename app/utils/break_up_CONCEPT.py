import pandas as pd
import os

# Function to split a TSV file into chunks of a given size
def split_tsv_into_fixed_chunks(file_path, output_directory, chunk_size=10000):
    # Read the TSV file into a Pandas DataFrame
    df = pd.read_csv(file_path, sep='\t', low_memory=False)

    # Initialize an empty list to hold output file paths
    output_files = []
    
    # Calculate the number of chunks needed
    num_chunks = (len(df) // chunk_size) + (1 if len(df) % chunk_size else 0)
    
    # Create the output directory if it doesn't exist
    os.makedirs(output_directory, exist_ok=True)
    
    # Split the DataFrame into chunks and save each one as a new TSV file
    for i in range(num_chunks):
        start_idx = i * chunk_size
        end_idx = (i + 1) * chunk_size if i != num_chunks - 1 else len(df)
        
        chunk = df.iloc[start_idx:end_idx]
        output_file_path = os.path.join(output_directory, f'chunk_{i+1}.tsv')
        chunk.to_csv(output_file_path, sep='\t', index=False)
        
        output_files.append(output_file_path)
        
    return output_files

# List of files to process
files = ["CONCEPT_ANCESTOR.csv", "CONCEPT.csv", "CONCEPT_RELATIONSHIP.csv", "CONCEPT_SYNONYM.csv"]

data_directory = "./app/data"

for file in files:
    # Get the base name of the file
    base_name = os.path.basename(file)
    
    # Remove the file extension (assuming it's always ".tsv")
    base_name = os.path.splitext(base_name)[0]
    output_directory = os.path.join(data_directory, base_name)
    print(output_directory)
    # Call the function to split the TSV file into chunks
    output_files = split_tsv_into_fixed_chunks(file, output_directory, chunk_size=10000)
    
    # Print the list of output file paths
    print(f"Split '{file}' into {len(output_files)} chunks:")