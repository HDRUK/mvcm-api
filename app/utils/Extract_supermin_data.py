import pandas as pd
import os

# Read CONCEPT data and filter
CONCEPT = pd.read_csv('CONCEPT.tsv', sep='\t', low_memory=False)

# Read CONCEPT_RELATIONSHIP data
CONCEPT_RELATIONSHIP = pd.read_csv('CONCEPT_RELATIONSHIP.tsv', sep='\t', low_memory=False)

# Read CONCEPT_ANCESTOR data
CONCEPT_ANCESTOR = pd.read_csv('CONCEPT_ANCESTOR.tsv', sep='\t', low_memory=False)

# Read CONCEPT_SYNONYM data
CONCEPT_SYNONYM = pd.read_csv('CONCEPT_SYNONYM.tsv', sep='\t', low_memory=False)

CONCEPT_filtered_rows = CONCEPT[CONCEPT['concept_name'].str.contains('Asthma', case=False, na=False)]

# Filter CONCEPT_RELATIONSHIP based on CONCEPT_filtered_rows
CONCEPT_RELATIONSHIP_filtered_rows = CONCEPT_RELATIONSHIP[
    CONCEPT_RELATIONSHIP['concept_id_1'].isin(CONCEPT_filtered_rows['concept_id']) &
    CONCEPT_RELATIONSHIP['concept_id_2'].isin(CONCEPT_filtered_rows['concept_id'])
]

# Filter CONCEPT_RELATIONSHIP based on CONCEPT_filtered_rows
CONCEPT_ANCESTOR_filtered_rows = CONCEPT_ANCESTOR[
    CONCEPT_ANCESTOR['ancestor_concept_id'].isin(CONCEPT_filtered_rows['concept_id']) &
    CONCEPT_ANCESTOR['descendant_concept_id'].isin(CONCEPT_filtered_rows['concept_id'])
]

# Filter CONCEPT_SYNONYM based on CONCEPT_filtered_rows
CONCEPT_SYNONYM_filtered_rows = CONCEPT_SYNONYM[
    CONCEPT_SYNONYM['concept_id'].isin(CONCEPT_filtered_rows['concept_id'])
]

CONCEPT_extra_rows_1 = CONCEPT[
    CONCEPT['concept_id'].isin(CONCEPT_RELATIONSHIP_filtered_rows['relationship_id'])
]

CONCEPT_extra_rows_2 = CONCEPT[
    CONCEPT['concept_id'].isin(CONCEPT_SYNONYM_filtered_rows['language_concept_id'])
]

CONCEPT_filtered_rows = pd.concat([CONCEPT_filtered_rows,CONCEPT_extra_rows_1,CONCEPT_extra_rows_2],axis=0)

CONCEPT_filtered_rows.to_csv("CONCEPT_filtered_rows.tsv", sep='\t', index=False)

CONCEPT_RELATIONSHIP_filtered_rows.to_csv("CONCEPT_RELATIONSHIP_filtered_rows.tsv", sep='\t', index=False)

CONCEPT_ANCESTOR_filtered_rows.to_csv("CONCEPT_ANCESTOR_filtered_rows.tsv", sep='\t', index=False)

CONCEPT_SYNONYM_filtered_rows.to_csv("CONCEPT_SYNONYM_filtered_rows.tsv", sep='\t', index=False)



