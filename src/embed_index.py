import os
import json
import chromadb
import chromadb.errors 
from pathlib import Path
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from config import CHROMA_DIR, EMBEDDING_MODEL, DOCS_JSONL

def embed_and_index():
    print(f"🖥️  Running on CPU. Loading model: {EMBEDDING_MODEL}...")
    # device='cpu' ensures no GPU memory allocation attempts
    model = SentenceTransformer(EMBEDDING_MODEL, device='cpu')

    print(f"📂 Initializing ChromaDB at {CHROMA_DIR}...")
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    
    # Reset Collection
    try:
        client.delete_collection("listings")
    except:
        pass

    # Create collection with Cosine Similarity
    coll = client.create_collection(name="listings", metadata={"hnsw:space": "cosine"})

    print("📖 Reading documents...")
    ids, texts, metadatas = [], [], []
    
    if not os.path.exists(DOCS_JSONL):
        print(f"❌ Error: {DOCS_JSONL} not found. Run ingest.py first.")
        return

    with open(DOCS_JSONL, "r", encoding="utf8") as f:
        for line in f:
            doc = json.loads(line)
            ids.append(str(doc["id"])) # Ensure ID is string
            texts.append(doc["text"])
            metadatas.append(doc["metadata"])

    print(f"   - Found {len(ids)} documents.")
    
    batch_size = 32 
    print("🚀 Starting embedding process...")
    
    for i in tqdm(range(0, len(ids), batch_size), desc="Processing"):
        batch_ids = ids[i : i + batch_size]
        batch_texts = texts[i : i + batch_size]
        batch_meta = metadatas[i : i + batch_size]

        # Normalize embeddings for Cosine Similarity
        embeddings = model.encode(batch_texts, normalize_embeddings=True)

        coll.add(
            ids=batch_ids,
            documents=batch_texts,
            embeddings=embeddings.tolist(),
            metadatas=batch_meta
        )

    print(f"✅ Success! Indexed {coll.count()} documents.")

if __name__ == "__main__":
    embed_and_index()
