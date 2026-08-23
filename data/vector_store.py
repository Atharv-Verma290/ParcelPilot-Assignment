import chromadb 
from chromadb.utils import embedding_functions 
from dotenv import load_dotenv
load_dotenv()

client = chromadb.PersistentClient(path="./data/chroma")

embedding_function = embedding_functions.OpenAIEmbeddingFunction(
    api_key_env_var="OPENAI_API_KEY",
    model_name="text-embedding-3-small",
    dimensions=768
)

collection = client.get_or_create_collection(
    name="parcel_pilot_docs",
    embedding_function=embedding_function
)


def reset_collection() -> None:
    """
    Delete and recreate the ParcelPilot Chroma collection.

    Existing embeddings are discarded. The module-level `collection`
    handle is replaced with the new empty collection.
    """
    global collection

    try:
        client.delete_collection(name="parcel_pilot_docs")
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name="parcel_pilot_docs",
        embedding_function=embedding_function,
    )

def add_chunks(chunks):
    """
    Embed and insert document chunks into the Chroma collection.

    Args:
        chunks: Sequence of dicts with `text` and `metadata` keys.
            `metadata` must include a `source` field used to build
            document IDs.
    """
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