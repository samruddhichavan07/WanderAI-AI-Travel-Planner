import pandas as pd
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
# Load merged dataset
df = pd.read_csv("data/merged_places.csv")

# Convert each row into a LangChain Document
documents = []
for _, row in df.iterrows():
    content = (
        f"Place: {row['place_name']}. "
        f"City: {row['city']}. Country: {row['country']}. "
        f"Category: {row['category']}. Rating: {row['rating']}. "
        f"Cost: {row['cost']}. "
        f"Description: {row['description']}"
    )
    documents.append(Document(
        page_content=content,
        metadata={"place_name": str(row['place_name']), "country": str(row['country'])}
    ))

print(f"Prepared {len(documents)} documents for embedding")

# Create embeddings using Ollama
embeddings = OllamaEmbeddings(model="nomic-embed-text")

# Build and persist the vector store
vectorstore = Chroma.from_documents(
    documents=documents,
    embedding=embeddings,
    persist_directory="chroma_db"
)

print("Vector store built and saved to 'chroma_db' folder")