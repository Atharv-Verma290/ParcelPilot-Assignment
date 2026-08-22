import chromadb 
from chromadb.utils import embedding_functions 
from dotenv import load_dotenv
load_dotenv()

client = chromadb.PersistentClient(path="./data/chroma")

# embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
#     model_name="all-MiniLM-L6-v2" 
# )

# embedding_function = embedding_functions.GoogleGeminiEmbeddingFunction(
#     api_key_env_var="GOOGLE_API_KEY",
#     model_name="gemini-embedding-001",
#     task_type="RETRIEVAL_DOCUMENT",
#     dimension=768
# )

embedding_function = embedding_functions.OpenAIEmbeddingFunction(
    api_key_env_var="OPENAI_API_KEY",
    model_name="text-embedding-3-small",
    dimensions=768
)

collection = client.get_or_create_collection(
    name="parcel_pilot_docs",
    embedding_function=embedding_function
)

def add_chunks(chunks):
    documents = []
    metadatas = []
    ids = []

    for i, chunk in enumerate(chunks):
        documents.append(chunk["text"])
        metadatas.append(chunk["metadata"])
        ids.append(f"{chunk['metadata']['source']}_{i}")

    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )