from transformers import AutoTokenizer, AutoModel, pipeline
import torch

# Initialize BERT model and tokenizer
tokenizer = AutoTokenizer.from_pretrained("dmis-lab/biobert-base-cased-v1.1")
model = AutoModel.from_pretrained("dmis-lab/biobert-base-cased-v1.1")
nlp = pipeline("feature-extraction", model=model, tokenizer=tokenizer)

# Function to calculate semantic similarity using BERT
def bert_similarity(text1, text2):
    with torch.no_grad():
        features1 = nlp(text1)
        features2 = nlp(text2)
        emb1 = torch.tensor(features1[0]).mean(dim=0)
        emb2 = torch.tensor(features2[0]).mean(dim=0)
        similarity = torch.cosine_similarity(emb1, emb2, dim=0)  * 100
    return similarity.item()
