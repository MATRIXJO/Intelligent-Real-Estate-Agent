import json
from config import GROQ_MODEL

def rerank(client, query, docs, top_k=5):
    """
    Reranks documents using Groq (Llama-3).
    """
    if not docs:
        return []

    # Limit to top 20
    candidate_docs = docs[:20] 
    
    docs_text = ""
    doc_map = {}
    
    for i, d in enumerate(candidate_docs):
        short_id = str(i)
        doc_map[short_id] = d
        meta = d.get("metadata", {})
        snippet = (
            f"ID: {short_id}\n"
            f"Content: {d.get('text', '')[:200]}\n"
            f"Price: {meta.get('exact_price', 'N/A')}\n"
            f"Locality: {meta.get('locality', 'N/A')}\n"
            f"---\n"
        )
        docs_text += snippet

    system_msg = "You are a ranking assistant. You must output JSON only."
    
    user_msg = f"""
    Query: "{query}"
    
    Rank the Top {top_k} listings based on relevance.
    Return a JSON object with a "ranking" list containing "id" and "relevance_score" (0.0 to 1.0).
    Example: {{ "ranking": [ {{ "id": "2", "relevance_score": 0.95 }} ] }}
    
    Listings:
    {docs_text}
    """

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        
        result = json.loads(response.choices[0].message.content)
        rankings = result.get("ranking", [])
        
        reranked_docs = []
        for r in rankings:
            d_id = str(r.get("id"))
            if d_id in doc_map:
                original_doc = doc_map[d_id].copy()
                original_doc["score"] = float(r.get("relevance_score", 0))
                reranked_docs.append(original_doc)
        
        # Fill rest
        returned_ids = set(str(r.get("id")) for r in rankings)
        for i, d in enumerate(candidate_docs):
            if str(i) not in returned_ids:
                d_copy = d.copy()
                d_copy["score"] = 0.1 
                reranked_docs.append(d_copy)

        reranked_docs.sort(key=lambda x: x["score"], reverse=True)
        return reranked_docs

    except Exception as e:
        print(f"⚠️ Groq Rerank failed: {e}. Returning original order.")
        for d in docs:
            d["score"] = 0.5
        return docs[:top_k]
