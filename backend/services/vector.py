import json
import numpy as np
from typing import List, Tuple, Optional, Protocol
from sqlmodel import Session, select
from backend.models.gallery import FaceGallery
from backend.services.gallery import gallery_service
import faiss
from backend.core.database import engine
import pickle

# --- Strategy Interface ---
class SearchEngine(Protocol):
    def load(self, vectors: List[Tuple[int, List[float]]]) -> None:
        ...
    
    def search(self, query_vector: List[float], threshold: float) -> Tuple[Optional[int], float]:
        ...
    
    def add(self, user_id: int, vector: List[float]) -> None:
        ...
    
    def count(self) -> int:
        ...

# --- Concrete Strategy: Linear Search (Small Tenant) ---
class LinearEngine:
    def __init__(self, dims: int):
        self.dims = dims
        self.vectors = np.empty((0, dims), dtype=np.float32)
        self.user_ids = []

    def load(self, items: List[Tuple[int, List[float]]]) -> None:
        if not items:
            return
            
        vec_list = []
        id_list = []
        for user_id, vec in items:
            try:
                v = np.array(vec, dtype=np.float32)
                if len(v) != self.dims: continue
                vec_list.append(v)
                id_list.append(user_id)
            except: pass
            
        if vec_list:
            self.vectors = np.array(vec_list, dtype=np.float32)
            # Normalize for Cosine Similarity
            faiss.normalize_L2(self.vectors)
            self.user_ids = id_list

    def search(self, query_vector: List[float], threshold: float) -> Tuple[Optional[int], float]:
        if len(self.vectors) == 0:
            return None, 0.0

        query = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(query)
        
        # Linear Dot Product (Cosine Sim since normalized)
        scores = np.dot(self.vectors, query.T).flatten()
        
        if len(scores) == 0:
            return None, 0.0
            
        best_idx = np.argmax(scores)
        best_score = float(scores[best_idx])
        print(f"DEBUG: Linear Search Best Score: {best_score}")
        
        if best_score > threshold:
            return self.user_ids[best_idx], best_score
        return None, best_score

    def add(self, user_id: int, vector: List[float]) -> None:
        vec_np = np.array([vector], dtype=np.float32)
        faiss.normalize_L2(vec_np)
        self.vectors = np.vstack([self.vectors, vec_np])
        self.user_ids.append(user_id)

    def count(self) -> int:
        return len(self.user_ids)

# --- Concrete Strategy: FAISS Search (Medium/Large Tenant) ---
class FaissEngine:
    def __init__(self, dims: int):
        self.dims = dims
        self.index = faiss.IndexFlatIP(dims)
        self.user_ids = []

    def load(self, items: List[Tuple[int, List[float]]]) -> None:
        self.index.reset()
        self.user_ids = []
        
        if not items: return

        vec_list = []
        id_list = []
        for user_id, vec in items:
            try:
                v = np.array(vec, dtype=np.float32)
                if len(v) != self.dims: continue
                vec_list.append(v)
                id_list.append(user_id)
            except: pass
            
        if vec_list:
            vectors = np.array(vec_list, dtype=np.float32)
            faiss.normalize_L2(vectors)
            self.index.add(vectors)
            self.user_ids = id_list

    def search(self, query_vector: List[float], threshold: float) -> Tuple[Optional[int], float]:
        if self.index.ntotal == 0:
            return None, 0.0

        query = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(query)
        
        D, I = self.index.search(query, 1)
        idx = I[0][0]
        score = float(D[0][0])
        print(f"DEBUG: FAISS Search Best Score: {score}")
        
        if idx != -1 and score > threshold:
            return self.user_ids[idx], score
        return None, score

    def add(self, user_id: int, vector: List[float]) -> None:
        vec_np = np.array([vector], dtype=np.float32)
        faiss.normalize_L2(vec_np)
        self.index.add(vec_np)
        self.user_ids.append(user_id)

    def count(self) -> int:
        return self.index.ntotal

# --- Context: Vector Service ---
class VectorService:
    def __init__(self):
        self.dims = 512
        self.threshold = 0.5 # Updated for better security with Multi-Frame averaging
        self.rescue_delta = 0.08 # For multi-reference rescue logic
        self.engine: Optional[SearchEngine] = None
        self.engine_name: str = "none"  # Track which engine is active
        self.is_loaded = False
        
        # Scaling Thresholds
        self.SMALL_TENANT_LIMIT = 1000 
        # > 1000 uses FAISS
        # > 50000 would use FAISS IVF (Not implemented in code yet, purely config based)

    def load_index(self):
        print("=" * 60)
        print("🔧 Initializing Vector Engine...")
        print("=" * 60)
        
        with Session(engine) as session:
            # Load ALL vectors from FaceGallery (Anchor + Dynamic)
            all_vectors = gallery_service.get_all_vectors(session)
            count = len(all_vectors)
            print(f"📊 Total vectors found in gallery: {count}")
            
            # Try FAISS first, fallback to Linear
            try:
                print("🚀 Attempting to initialize FaissEngine (preferred)...")
                self.engine = FaissEngine(self.dims)
                self.engine.load(all_vectors)
                self.engine_name = "FAISS"
                print(f"✅ FaissEngine initialized successfully!")
                print(f"   └── Vectors loaded: {self.engine.count()}")
                print(f"   └── Index type: IndexFlatIP (Inner Product)")
            except Exception as faiss_error:
                print(f"⚠️  FaissEngine failed: {faiss_error}")
                print("🔄 Falling back to LinearEngine...")
                
                try:
                    self.engine = LinearEngine(self.dims)
                    self.engine.load(all_vectors)
                    self.engine_name = "Linear"
                    print(f"✅ LinearEngine initialized successfully!")
                    print(f"   └── Vectors loaded: {self.engine.count()}")
                except Exception as linear_error:
                    print(f"❌ LinearEngine also failed: {linear_error}")
                    self.engine_name = "FAILED"
                    raise RuntimeError("Both FAISS and Linear engines failed to initialize")
            
            self.is_loaded = True
            print("-" * 60)
            print(f"🎯 Active Engine: {self.engine_name}")
            print(f"🎯 Vectors Ready: {self.engine.count()}")
            print(f"🎯 Threshold: {self.threshold} | Rescue Delta: {self.rescue_delta}")
            print("=" * 60)

    def find_nearest(self, query_vector: List[float]) -> Tuple[Optional[int], float]:
        if not self.is_loaded:
            self.load_index()
            
        return self.engine.search(query_vector, self.threshold)

    def search_all_matches(self, query_vector: List[float]) -> dict:
        """
        Returns ALL similarity scores grouped by user_id.
        Format: {user_id: [score1, score2, ...]}
        
        This enables multi-reference aggregation decision logic.
        """
        if not self.is_loaded:
            self.load_index()
        
        # Normalize query vector
        query = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(query)
        query = query.flatten()
        
        # Get all scores for all users
        user_scores: dict = {}
        
        if isinstance(self.engine, LinearEngine):
            # Linear engine - compute all dot products
            if len(self.engine.vectors) == 0:
                return {}
            scores = np.dot(self.engine.vectors, query).flatten()
            for idx, score in enumerate(scores):
                uid = self.engine.user_ids[idx]
                if uid not in user_scores:
                    user_scores[uid] = []
                user_scores[uid].append(float(score))
        
        elif isinstance(self.engine, FaissEngine):
            # FAISS - search for all vectors (k = total)
            if self.engine.index.ntotal == 0:
                return {}
            k = min(self.engine.index.ntotal, 100)  # Limit to top 100
            D, I = self.engine.index.search(query.reshape(1, -1), k)
            for i in range(k):
                idx = I[0][i]
                score = float(D[0][i])
                if idx != -1:
                    uid = self.engine.user_ids[idx]
                    if uid not in user_scores:
                        user_scores[uid] = []
                    user_scores[uid].append(score)
        
        return user_scores

    def decide_match(self, user_scores: dict) -> Tuple[Optional[int], float, str]:
        """
        Multi-Reference Aggregation Decision Logic.
        
        Rules:
        1. Strong Match: If ANY score >= threshold → ACCEPT
        2. Rescue: If avg(top_3_scores) >= (threshold - delta) → ACCEPT
        3. Otherwise → REJECT
        
        Returns: (user_id, confidence, decision_reason)
        """
        if not user_scores:
            return None, 0.0, "no_matches"
        
        best_user = None
        best_score = 0.0
        best_reason = "rejected"
        
        rescue_threshold = self.threshold - self.rescue_delta  # 0.5 - 0.08 = 0.42
        
        for user_id, scores in user_scores.items():
            max_score = max(scores)
            
            # Rule 1: Strong single match
            if max_score >= self.threshold:
                if max_score > best_score:
                    best_user = user_id
                    best_score = max_score
                    best_reason = "strong_match"
        
        # If we found a strong match, return it
        if best_user and best_reason == "strong_match":
            print(f"🎯 Strong Match: User {best_user} with {best_score:.4f}")
            return best_user, best_score, best_reason
        
        # Rule 2: Try rescue logic
        for user_id, scores in user_scores.items():
            # Get top 3 scores for this user
            sorted_scores = sorted(scores, reverse=True)[:3]
            avg_top3 = sum(sorted_scores) / len(sorted_scores)
            
            if avg_top3 >= rescue_threshold:
                if avg_top3 > best_score:
                    best_user = user_id
                    best_score = avg_top3
                    best_reason = "rescue_match"
        
        if best_user and best_reason == "rescue_match":
            print(f"🆘 Rescue Match: User {best_user} with avg top-3 = {best_score:.4f}")
            return best_user, best_score, best_reason
        
        # No match found
        print(f"❌ No Match: Best scores = {user_scores}")
        return None, best_score, "rejected"

    def add_embedding(self, user_id: int, vector: List[float], session: Session, is_anchor: bool = False):
        # 1. Persist to Gallery via Service
        gallery_service.add_to_gallery(session, user_id, vector, confidence=1.0, is_anchor=is_anchor)
        
        # 2. Update In-Memory Engine
        if not self.is_loaded:
            self.load_index()
        else:
            self.engine.add(user_id, vector)


# Singleton
vector_service = VectorService()

