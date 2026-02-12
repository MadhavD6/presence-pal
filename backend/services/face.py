from typing import List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
from backend.core.logger import logger
from backend.tasks.face_tasks import compute_embedding
import numpy as np

from backend.core.config import get_settings

class FaceService:
    def __init__(self):
        settings = get_settings()
        # Local Thread Pool for DeepFace
        self.executor = ThreadPoolExecutor(max_workers=settings.FACE_RECOGNITION_THREADS) 
        logger.info("FaceService Initialized (Local Thread Pool)", threads=settings.FACE_RECOGNITION_THREADS)

    async def get_embedding(self, image_bytes: bytes) -> Optional[dict]:
        """
        Run DeepFace in local thread pool.
        """
        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                self.executor,
                lambda: compute_embedding(image_bytes)
            )
            return result
            
        except Exception as e:
            logger.error("Face Recognition Task Failed", error=str(e))
            return None

    async def get_averaged_embedding(self, image_bytes_list: List[bytes]) -> Optional[List[float]]:
        """
        Parallel processing via local ThreadPool
        """
        if not image_bytes_list:
            return None
            
        loop = asyncio.get_running_loop()
        
        # Define helper to run all in thread pool
        def process_all_frames():
            results = []
            # We map the compute_embedding function over the list of images
            # Note: Executor doesn't support 'map' with lambda args easily in this context without more boilerplate,
            # so we just call them sequentially or we can use map.
            # However, since we are ALREADY in a thread (via run_in_executor below), 
            # we can likely just run them. 
            # BUT, we want them parallelized. 
            # Actually, run_in_executor puts the WHOLE function in ONE thread.
            # To parallelize multiple frames, we should spawn multiple futures from the event loop.
            pass

        # Better Approach: Create a list of futures
        try:
            tasks = [
                loop.run_in_executor(self.executor, compute_embedding, img)
                for img in image_bytes_list
            ]
            results = await asyncio.gather(*tasks)
            
            # ... Same averaging logic as before ...
            vectors = [res["embedding"] for res in results if res is not None and res.get("embedding")]
            confidences = [res.get("confidence", 1.0) for res in results if res is not None]
            
            if not vectors:
                return None
            if len(vectors) == 1:
                return vectors[0]

            logger.info("Averaging Frames (Local)", count=len(vectors))
            matrix = np.array(vectors)
            weights = np.array(confidences)
            
            if np.sum(weights) > 0:
                mean_vec = np.average(matrix, axis=0, weights=weights)
            else:
                mean_vec = np.mean(matrix, axis=0)
                
            norm = np.linalg.norm(mean_vec)
            if norm == 0:
                return mean_vec.tolist()
            return (mean_vec / norm).tolist()
            
        except Exception as e:
            logger.error("Averaging Task Failed", error=str(e))
            return None

# Singleton instance
face_service = FaceService()
