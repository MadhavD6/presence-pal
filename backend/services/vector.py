import json
import numpy as np
from typing import List, Tuple, Optional, Protocol
from sqlmodel import Session, select
from backend.models.gallery import FaceGallery
from backend.services.gallery import gallery_service
import faiss
from backend.core.database import engine
from backend.core.logger import logger
import pickle
import threading
import time
import os
from backend.core.config import get_settings
from backend.core.performance import log_execution_time

settings = get_settings()

# File-based signal for cross-worker FAISS index synchronization.
# When a new vector is added, this file is updated.
# Workers check this file before searches and reload if it's newer than their last load.
VECTOR_SIGNAL_FILE = "/tmp/prodify_vector_version"

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

# --- Concrete Strategy: FAISS Search ---
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
            except Exception as e:
                logger.error("Error loading vector", user_id=user_id, error=str(e))
            
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
        self.threshold = 0.65  # Increased for higher precision (was 0.60)
        self.rescue_delta = 0.05  # Tightened rescue logic (was 0.10)
        self.engine: Optional[SearchEngine] = None
        self.engine_name: str = "none"  # Track which engine is active
        self.is_loaded = False
        self._last_load_time: float = 0.0  # Track when we last loaded the index
        self._reload_lock = threading.Lock()  # Prevent concurrent reloads
        
        # Scaling Thresholds
        self.SMALL_TENANT_LIMIT = 1000 
        # > 1000 uses FAISS
        # > 50000 would use FAISS IVF (Not implemented in code yet, purely config based)

    def _signal_version_change(self):
        """Write a signal file to notify other workers that the index has changed."""
        try:
            with open(VECTOR_SIGNAL_FILE, "w") as f:
                f.write(str(time.time()))
            logger.info("Vector version signal written", signal_file=VECTOR_SIGNAL_FILE)
        except Exception as e:
            logger.error("Failed to write vector signal", error=str(e))

    def _check_needs_reload(self) -> bool:
        """Check if another worker has updated the index since our last load."""
        try:
            if not os.path.exists(VECTOR_SIGNAL_FILE):
                return False
            signal_mtime = os.path.getmtime(VECTOR_SIGNAL_FILE)
            return signal_mtime > self._last_load_time
        except Exception:
            return False

    @log_execution_time
    def load_index(self):
        """Load or reload the FAISS index from database. Thread-safe."""
        with self._reload_lock:
            logger.info("Initializing Vector Engine")
            
            with Session(engine) as session:
                # Load ALL vectors from FaceGallery (Anchor + Dynamic)
                all_vectors = gallery_service.get_all_vectors(session)
                count = len(all_vectors)
                logger.info("Vectors found in gallery", count=count)
                
                # Retry Logic for FAISS
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        logger.info(f"Attempting to initialize FaissEngine (Attempt {attempt + 1}/{max_retries})")
                        self.engine = FaissEngine(self.dims)
                        self.engine.load(all_vectors)
                        self.engine_name = "FAISS"
                        logger.info("FaissEngine initialized", vectors=self.engine.count(), type="IndexFlatIP")
                        self.is_loaded = True
                        self._last_load_time = time.time()
                        logger.info("Vector Service Ready", engine=self.engine_name, vectors=self.engine.count(), threshold=self.threshold)
                        return # Success
                        
                    except Exception as faiss_error:
                        logger.warning(f"FaissEngine failed attempt {attempt + 1}", error=str(faiss_error))
                        if attempt < max_retries - 1:
                            time.sleep(1) # Wait before retry
                        else:
                            logger.error("FaissEngine failed after all retries.")
                            self.engine_name = "FAILED"
                            raise RuntimeError(f"FAISS Engine failed to initialize after {max_retries} attempts: {str(faiss_error)}")

    def _ensure_fresh_index(self):
        """Check if the index needs a reload from another worker's enrollment. Lightweight."""
        if not self.is_loaded:
            self.load_index()
        elif self._check_needs_reload():
            logger.info("Vector index stale — reloading from database (another worker enrolled a face)")
            self.load_index()

    @log_execution_time
    def find_nearest(self, query_vector: List[float]) -> Tuple[Optional[int], float]:
        self._ensure_fresh_index()
        return self.engine.search(query_vector, self.threshold)

    @log_execution_time
    def search_all_matches(self, query_vector: List[float]) -> dict:
        """
        Returns ALL similarity scores grouped by user_id.
        Format: {user_id: [score1, score2, ...]}
        
        This enables multi-reference aggregation decision logic.
        """
        self._ensure_fresh_index()
        
        # Normalize query vector
        query = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(query)
        query = query.flatten()
        
        # Get all scores for all users
        user_scores: dict = {}
        
        if isinstance(self.engine, FaissEngine):
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
            logger.info("Strong Match Found", user=best_user, score=f"{best_score:.4f}")
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
            logger.info("Rescue Match Found", user=best_user, score=f"{best_score:.4f}")
            return best_user, best_score, best_reason
        
        # No match found
        logger.info("No Match Found", best_scores=user_scores)
        return None, best_score, "rejected"

    def add_embedding(self, user_id: int, vector: List[float], session: Session, is_anchor: bool = False):
        # 1. Persist to Gallery via Service
        gallery_service.add_to_gallery(session, user_id, vector, confidence=1.0, is_anchor=is_anchor)
        
        # 2. Update In-Memory Engine (for THIS worker)
        if not self.is_loaded:
            self.load_index()
        else:
            self.engine.add(user_id, vector)
            
        # 3. Signal OTHER workers to reload their index
        self._signal_version_change()
        self._last_load_time = time.time()  # Mark this worker as fresh
        logger.info(f"Vector added and signal written (User: {user_id})")

# Singleton
vector_service = VectorService()


