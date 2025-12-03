import cohere
from config import COHERE_API_KEY

# Initialize Client
if not COHERE_API_KEY:
    raise ValueError("COHERE_API_KEY is missing in environment variables.")

co = cohere.Client(COHERE_API_KEY)

def rerank(query, docs, top_k=5):
    """
    Reranks a list of documents using Cohere's Rerank-English-v3.0 model.
    docs: List of dicts [{"text": "...", "metadata": {...}, "id": "..."}]
    """
    if not docs:
        return []

    # Prepare just the text for reranking
    passages = [d["text"] for d in docs]

    try:
        response = co.rerank(
            query=query,
            documents=passages,
            top_n=top_k,
            model="rerank-english-v3.0"
        )
        
        ranked_docs = []
        for r in response.results:
            # Map back to original document object based on index
            original_doc = docs[r.index].copy()
            # Add the relevance score
            original_doc["score"] = float(r.relevance_score)
            ranked_docs.append(original_doc)
            
        return ranked_docs

    except Exception as e:
        print(f"⚠️ Cohere Rerank failed: {e}. Returning original top-k.")
        return docs[:top_k]
