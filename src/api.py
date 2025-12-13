import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import chromadb
from collections import defaultdict, deque
from sentence_transformers import SentenceTransformer

# ---------------------------
# Local modules
# ---------------------------
from config import CHROMA_DIR, EMBEDDING_MODEL, groq_client, GROQ_MODEL
from filters_extractor import extract_filters_llm
from ranking import compute_final_score
from locality_map import infer_zone_from_locality
from rerank import rerank
from personal import save_feedback, init_db
from locality_coords import get_coords_for_locality
from distance_utils import is_within_radius

# ---------------------------
# FastAPI Setup
# ---------------------------
app = FastAPI(title="GenAI Real Estate RAG (Groq Edition)")
init_db()

print(f"Connecting to ChromaDB at {CHROMA_DIR}...")
chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
collection = chroma_client.get_collection(name="listings")

print(f"Loading embedding model: {EMBEDDING_MODEL}...")
embed_model = SentenceTransformer(EMBEDDING_MODEL, device='cpu')

# ---------------------------
# MEMORY STORE
# ---------------------------
conversation_store = defaultdict(lambda: deque(maxlen=5))

# ---------------------------
# Request Models
# ---------------------------
class QueryRequest(BaseModel):
    user_id: str
    query: str
    budget_max: Optional[float] = None
    bhk: Optional[List[int]] = None
    zone: Optional[str] = None
    top_k: Optional[int] = 5

class FeedbackRequest(BaseModel):
    user_id: str
    doc_id: str
    liked: bool

# ---------------------------
# Helper: Format History
# ---------------------------
def get_formatted_history(user_id):
    history = conversation_store[user_id]
    if not history:
        return ""
    formatted = ""
    for msg in history:
        role = "User" if msg["role"] == "user" else "Assistant"
        formatted += f"{role}: {msg['content']}\n"
    return formatted

# ---------------------------
# Helper: Chroma Filter Builder
# ---------------------------
def build_chroma_filters(query_text, budget_max=None, zone=None):
    conditions = []
    if budget_max:
        conditions.append({"exact_price": {"$lte": budget_max}})
        conditions.append({"exact_price": {"$gt": 100}})
    if zone:
        conditions.append({"zone": {"$eq": str(zone)}})
    
    cheap_words = ["cheap", "budget", "affordable", "low cost"]
    if any(w in query_text.lower() for w in cheap_words):
        conditions.append({"price_per_sqft": {"$lt": 9000}})

    if len(conditions) > 1:
        return {"$and": conditions}
    elif len(conditions) == 1:
        return conditions[0]
    return None

def parse_bhk_from_metadata(bhk_val):
    if not bhk_val: return []
    if isinstance(bhk_val, list): return [int(x) for x in bhk_val if str(x).isdigit()]
    try:
        clean = str(bhk_val).replace("[", "").replace("]", "")
        return [int(float(x)) for x in clean.split(",") if x.strip()]
    except: return []

# ======================================================================
#                           SEARCH ENDPOINT
# ======================================================================
@app.post("/query")
async def search_properties(req: QueryRequest):
    
    # 1. Retrieve History
    history_str = get_formatted_history(req.user_id)
    print(f"\n🧠 Context for {req.user_id}:\n{history_str}")

    # 2. Hybrid Extraction (Using Groq)
    extracted = extract_filters_llm(groq_client, req.query, history_str)

    final_bhk = req.bhk or extracted.get("bhk")
    final_budget = req.budget_max or extracted.get("budget_max")
    final_zone = req.zone or extracted.get("zone")

    if not final_zone and extracted.get("locality"):
        final_zone = infer_zone_from_locality(extracted["locality"])

    print(f"🔍 Merged Query Filters: BHK={final_bhk}, Budget={final_budget}, Zone={final_zone}")

    # 3. Embedding (Vector Search)
    query_text = f"Represent this sentence for searching properties: {req.query}"
    query_emb = embed_model.encode(query_text, normalize_embeddings=True).tolist()

    # 4. DB filters
    where_clause = build_chroma_filters(req.query, final_budget, final_zone)

    # 5. Chroma retrieval
    try:
        results = collection.query(
            query_embeddings=[query_emb],
            n_results = 50,
            where=where_clause
        )
    except Exception as e:
        print("❌ Chroma Error:", e)
        return {"answer": "Database error", "retrieved": []}

    # 6. Process Results
    raw_docs = []
    ids = results.get("ids", [[]])[0]
    if ids:
        for i in range(len(ids)):
            meta = results["metadatas"][0][i]
            text = results["documents"][0][i]
            doc_id = results["ids"][0][i]

            if final_bhk:
                prop_bhks = parse_bhk_from_metadata(meta.get("bhk_list"))
                if not set(final_bhk).intersection(prop_bhks):
                    continue
            raw_docs.append({"id": doc_id, "text": text, "metadata": meta})

    # Proximity Logic
    user_loc = extracted.get("locality")
    proximity_docs = []
    if user_loc:
        user_lat, user_lon, _, _ = get_coords_for_locality(user_loc)
        if user_lat:
            for d in raw_docs:
                prop_loc = d["metadata"].get("locality", "").lower()
                plat, plon, _, _ = get_coords_for_locality(prop_loc)
                if plat and is_within_radius(user_lat, user_lon, plat, plon, radius_km=6.5):
                    proximity_docs.append(d)
    if proximity_docs:
        raw_docs = proximity_docs

    if not raw_docs:
        conversation_store[req.user_id].append({"role": "user", "content": req.query})
        conversation_store[req.user_id].append({"role": "assistant", "content": "I couldn't find any properties matching those exact criteria."})
        return {"answer": "I couldn't find any properties matching those specific criteria.", "retrieved": []}

    # 7. Rerank (Using Groq)
    reranked = rerank(groq_client, req.query, raw_docs, top_k=min(20, len(raw_docs)))
    
    # 8. Scoring
    final_list = []
    max_sim = max([x.get("score", 0) for x in reranked]) if reranked else 1

    for d in reranked:
        sim_norm = d["score"] / max_sim if max_sim > 0 else 0.5
        meta = d["metadata"]
        user_context = {
            "budget_max": final_budget,
            "bhk": final_bhk,
            "zone": final_zone,
            "locality": extracted.get("locality")
        }
        d["final_score"] = compute_final_score(meta, user_context, sim_score=sim_norm)
        final_list.append(d)

    final_list.sort(key=lambda x: x["final_score"], reverse=True)
    topk = final_list[: req.top_k or 5]

    # 9. LLM Summary (Using Groq)
    context_parts = []
    for d in topk:
        md = d["metadata"]
        price = md.get("exact_price", 0) or 0
        price_str = f"{price/10000000:.2f} Cr" if price >= 1e7 else f"{price/100000:.2f} L"
        context_parts.append(
            f"Property: {md.get('title')}\n"
            f"Location: {md.get('locality')} ({md.get('zone')})\n"
            f"Price: {price_str}\n"
            f"Livability: {md.get('livability_score')}\n"
        )
    context_text = "\n---\n".join(context_parts)

    system_msg = "You are an expert Real Estate advisor."
    user_msg = (
        f"Conversation History:\n{history_str}\n\n"
        f"User's Latest Query: {req.query}\n\n"
        f"Properties Found:\n{context_text}\n\n"
        f"Provide a helpful recommendation or answer based on these properties."
    )
  

    try:
        resp = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.7
        )
        summary = resp.choices[0].message.content
    except Exception as e:
        print(f"❌ Groq Summary Error: {e}")
        summary = "Here are the best matching properties."
    
    # 10. Update History
    conversation_store[req.user_id].append({"role": "user", "content": req.query})
    conversation_store[req.user_id].append({"role": "assistant", "content": summary})

    return {"answer": summary, "retrieved": topk}

@app.post("/feedback")
async def submit_feedback(req: FeedbackRequest):
    save_feedback(req.user_id, req.doc_id, req.liked)
    return {"status": "success"}
