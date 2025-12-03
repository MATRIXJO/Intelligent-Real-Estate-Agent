import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import chromadb
import cohere
from sentence_transformers import SentenceTransformer

# ---------------------------
# Local modules
# ---------------------------
try:
    from config import CHROMA_DIR, COHERE_API_KEY, EMBEDDING_MODEL
except ImportError:
    CHROMA_DIR = "../data/chroma_db"
    EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
    COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")

from filters_extractor import extract_filters_llm
from ranking import compute_final_score
from locality_map import infer_zone_from_locality
from rerank import rerank
from personal import load_profile, save_feedback, init_db

# NEW modules
from locality_coords import get_coords_for_locality
from distance_utils import is_within_radius


# ---------------------------
# FastAPI Setup
# ---------------------------
app = FastAPI(title="GenAI Real Estate RAG")
init_db()

print(f"Connecting to ChromaDB at {CHROMA_DIR}...")
chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
collection = chroma_client.get_collection(name="listings")

print(f"Loading embedding model: {EMBEDDING_MODEL}...")
embed_model = SentenceTransformer(EMBEDDING_MODEL, device='cpu')

co = cohere.Client(COHERE_API_KEY)


# ---------------------------
# Request Models
# ---------------------------
class QueryRequest(BaseModel):
    user_id: Optional[str] = "anon"
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
# Helper: Chroma Filter Builder
# ---------------------------
def build_chroma_filters(query_text, budget_max=None, zone=None):
    conditions = []

    # ------- Budget Filter -------
    if budget_max:
        conditions.append({"exact_price": {"$lte": budget_max}})
        conditions.append({"exact_price": {"$gt": 100}})

    # ------- Zone Filter -------
    if zone:
        conditions.append({"zone": {"$eq": str(zone)}})

    # ------- Cheap/Budget Keyword Filter -------
    cheap_words = ["cheap", "budget", "affordable", "low cost", "low budget"]
    if any(w in query_text.lower() for w in cheap_words):
        conditions.append({"price_per_sqft": {"$lt": 9000}})

    if len(conditions) > 1:
        return {"$and": conditions}
    elif len(conditions) == 1:
        return conditions[0]
    return None


# ---------------------------
# Helper: Parse BHK from metadata
# ---------------------------
def parse_bhk_from_metadata(bhk_val):
    if not bhk_val:
        return []
    if isinstance(bhk_val, list):
        return [int(x) for x in bhk_val if str(x).isdigit()]
    try:
        clean = str(bhk_val).replace("[", "").replace("]", "")
        return [int(float(x)) for x in clean.split(",") if x.strip()]
    except:
        return []


# ======================================================================
#                           SEARCH ENDPOINT
# ======================================================================
@app.post("/query")
async def search_properties(req: QueryRequest):

    # 1. Hybrid LLM + Rule-based extraction
    extracted = extract_filters_llm(co, req.query)

    final_bhk = req.bhk or extracted.get("bhk")
    final_budget = req.budget_max or extracted.get("budget_max")
    final_zone = req.zone or extracted.get("zone")

    if not final_zone and extracted.get("locality"):
        final_zone = infer_zone_from_locality(extracted["locality"])

    print(f"\n🔍 Query: {req.query}")
    print(f"   → Filters: BHK={final_bhk}, Budget={final_budget}, Zone={final_zone}")

    # 2. Embedding
    query_text = f"Represent this sentence for searching relevant properties: {req.query}"
    query_emb = embed_model.encode(query_text, normalize_embeddings=True).tolist()

    # 3. DB filters
    where_clause = build_chroma_filters(req.query, final_budget, final_zone)

    # 4. Chroma retrieval
    try:
        results = collection.query(
            query_embeddings=[query_emb],
            n_results=50,
            where=where_clause
        )
    except Exception as e:
        print("❌ Chroma Error:", e)
        return {"answer": "Database error", "retrieved": []}

    # 5. Build documents list
    raw_docs = []
    ids = results.get("ids", [[]])[0]

    if ids:
        for i in range(len(ids)):
            meta = results["metadatas"][0][i]
            text = results["documents"][0][i]
            doc_id = results["ids"][0][i]

            # BHK filter
            if final_bhk:
                prop_bhks = parse_bhk_from_metadata(meta.get("bhk_list"))
                if not set(final_bhk).intersection(prop_bhks):
                    continue

            raw_docs.append({"id": doc_id, "text": text, "metadata": meta})

    if not raw_docs:
        return {"answer": "No matching properties found.", "retrieved": []}

    # --------------------------------------------------------------------
    # NEW STEP: LOCALITY PROXIMITY FILTERING (6.5 km radius)
    # --------------------------------------------------------------------
    user_loc = extracted.get("locality")
    proximity_docs = []

    if user_loc:
        user_lat, user_lon, matched_name, conf = get_coords_for_locality(user_loc)
        if user_lat:
            for d in raw_docs:
                prop_loc = d["metadata"].get("locality", "").lower()
                plat, plon, _, _ = get_coords_for_locality(prop_loc)
                if not plat:
                    continue
                if is_within_radius(user_lat, user_lon, plat, plon, radius_km=6.5):
                    proximity_docs.append(d)

    # fallback
    if proximity_docs:
        raw_docs = proximity_docs

    # --------------------------------------------------------------------
    # 6. Rerank the results semantically
    # --------------------------------------------------------------------
    reranked = rerank(req.query, raw_docs, top_k=min(25, len(raw_docs)))

    final_list = []
    max_sim = max([x.get("score", 0) for x in reranked]) if reranked else 1

    # --------------------------------------------------------------------
    # 7. Final scoring for ranking
    # --------------------------------------------------------------------
    for d in reranked:
        sim_norm = d["score"] / max_sim if max_sim else 0.5

        meta = d["metadata"]
        meta_scoring = meta.copy()
        if "description" not in meta_scoring:
            meta_scoring["description"] = d["text"]

        user_context = {
            "budget_max": final_budget,
            "bhk": final_bhk,
            "zone": final_zone,
            "locality": extracted.get("locality")
        }

        d["final_score"] = compute_final_score(meta_scoring, user_context, sim_score=sim_norm)
        final_list.append(d)

    final_list.sort(key=lambda x: x["final_score"], reverse=True)
    topk = final_list[: req.top_k or 5]

    # --------------------------------------------------------------------
    # 8. LLM Summary
    # --------------------------------------------------------------------
    context_parts = []
    for d in topk:
        md = d["metadata"]
        price = md.get("exact_price", 0) or 0
        price_str = f"{price/10000000:.2f} Cr" if price >= 1e7 else f"{price/100000:.2f} L"

        context_parts.append(
            f"Property: {md.get('title')}\n"
            f"Location: {md.get('locality')} ({md.get('zone')})\n"
            f"Price: {price_str}\n"
            f"Area: {md.get('area')} sqft\n"
            f"BHK: {md.get('bhk_list')}\n"
            f"Livability: {md.get('livability_score')}/100\n"
            f"Investment: {md.get('investment_score')}/100\n"
            f"Match Score: {d['final_score']}/100\n"
            f"Details: {d['text'][:220]}..."
        )

    context = "\n\n---\n\n".join(context_parts)

    system_msg = (
        "You are an expert Bangalore Real Estate advisor. "
        "Use ONLY the given property context to answer the user."
    )

    user_msg = f"User Query: {req.query}\n\nProperties:\n{context}\n\nRecommend the best options."

    try:
        resp = co.chat(
            model="command-r-plus-08-2024",
            message=user_msg,
            preamble=system_msg,
            temperature=0.3
        )
        summary = resp.text
    except:
        summary = "Here are the best matching properties."

    return {"answer": summary, "retrieved": topk}


# ======================================================================
#                           FEEDBACK ENDPOINT
# ======================================================================
@app.post("/feedback")
async def submit_feedback(req: FeedbackRequest):
    try:
        save_feedback(req.user_id, req.doc_id, req.liked)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

